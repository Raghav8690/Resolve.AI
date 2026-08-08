from fastapi import APIRouter, HTTPException
from backend.services.data_loader import load_all
from backend.services.similarity import similarity_engine
from backend.services.router import route_ticket, compute_confidence
from backend.services.guardrails import apply_guardrails
from backend.services.explanation import generate_explanation
from backend.services.llm_reply import generate_reply
from backend.services.decision_log import log_decision
from backend.services.actions import simulate_action
from backend.models.schemas import TicketDecision, BoardSummary, TicketDetailResponse, OrderContext, Precedent
from backend.config import SIMILARITY_THRESHOLD, TOP_K
from datetime import datetime

router = APIRouter()

resolved_df, new_with_orders_df, orders_df = load_all()
similarity_engine.fit(resolved_df)

_processed = {}
_stream_order = list(new_with_orders_df['ticket_id'])
_stream_idx = 0


def _order_from_row(row) -> OrderContext:
    return OrderContext(
        order_id=row['order_id'],
        items=int(row['items']),
        value_inr=int(row['value_inr']),
        delivery_time_min=int(row['delivery_time_min']),
        delivery_status=row['delivery_status']
    )


def _row_for(ticket_id: str):
    match = new_with_orders_df[new_with_orders_df['ticket_id'] == ticket_id]
    return match.iloc[0]


def process_ticket(ticket_id: str) -> dict:
    """Run the full pipeline for one ticket. Returns {decision, trace}."""
    if ticket_id in _processed:
        d = _processed[ticket_id]
        return {"decision": d, "trace": d.pipeline["trace"]}

    row = _row_for(ticket_id)
    order = _order_from_row(row)

    details = similarity_engine.get_match_details(row['description'], k=TOP_K)

    r = route_ticket(row['description'])
    lane = r["lane"]
    suggested = r["suggested_action"]

    guardrails = {"checked": False, "flags": []}
    if r["auto"]:
        action = suggested
        final_action, flags = apply_guardrails(action, order, r["precedents"])
        guardrails = {"checked": True, "flags": flags}
        if final_action != action:
            lane = "human"
            r["reason"] = f"guardrail_block|{action}|{';'.join(flags)}"
        action = final_action
    else:
        action = None
        flags = []

    distinct = details["top_k"]
    if distinct:
        distinct_prec = [Precedent(**p) for p in distinct]
        distinct_confidence = compute_confidence(distinct_prec, r["agreement"])
    else:
        distinct_confidence = 0.0
    r["confidence"] = distinct_confidence

    explanation = generate_explanation(lane, action or "none", r["precedents"], r["reason"])
    reply = None
    if action:
        reply = generate_reply(row['ticket_id'], row['description'], action, order, r["precedents"])
        simulate_action(action, row['ticket_id'], order, r["precedents"])

    decision = TicketDecision(
        ticket_id=row['ticket_id'],
        order_id=row['order_id'],
        description=row['description'],
        lane=lane,
        action=action,
        confidence=r["confidence"],
        precedents=r["precedents"],
        explanation=explanation,
        reply=reply,
        guardrail_flags=flags,
        timestamp=datetime.now()
    )
    decision.pipeline = {
        "top_similarity": r["top_similarity"],
        "avg_distinct_similarity": details["avg_distinct_similarity"],
        "agreement": r["agreement"],
        "threshold": SIMILARITY_THRESHOLD,
        "matched": len(r["precedents"]),
        "reason": r["reason"],
        "suggested_action": suggested,
        "trace": _build_trace(row, details, r, lane, action, guardrails),
    }
    decision.status = "auto-resolved" if lane == "auto" else "human-review"
    log_decision(decision)
    _processed[row['ticket_id']] = decision
    return {"decision": decision, "trace": decision.pipeline["trace"]}


def _build_trace(row, details, r, lane, action, guardrails) -> dict:
    top3_actions = [p["resolution_action"] for p in details["top_k"]]
    return {
        "step1_vectorize": {
            "query_text": row['description'],
            "tokens": details["tokens"],
            "num_tokens": details["num_tokens"],
            "vector_dim": details["vector_dim"],
            "message": f"TF-IDF vectorized '{row['description']}' → {details['num_tokens']} tokens in {details['vector_dim']}-dim space",
        },
        "step2_cosine": {
            "pool_size": details["pool_size"],
            "all_scores": details["all_scores"],
            "top_k": details["top_k"],
            "top_similarity": details["avg_distinct_similarity"],
            "closest_similarity": r["top_similarity"],
            "message": f"Cosine-scored against all {details['pool_size']} resolved tickets",
        },
        "step3_top3": {
            "precedents": details["top_k"],
            "actions": top3_actions,
            "agree_count": r["agreement"],
            "message": f"Top-3 retrieved; {r['agreement']}/3 agree on '{r['agreed_action'] or '—'}'",
        },
        "step4_confidence": {
            "confidence": r["confidence"],
            "avg_similarity": details["avg_distinct_similarity"],
            "agreement": r["agreement"],
            "formula": "0.5·avg_sim + 0.35·agreement + 0.15·csat",
            "message": f"Confidence {r['confidence']*100:.0f}% = similarity + agreement + CSAT",
        },
        "step5_guardrail": {
            "checked": guardrails["checked"],
            "flags": guardrails["flags"],
            "order_status": row['delivery_status'],
            "order_value": int(row['value_inr']),
            "message": f"Guardrails {'PASS' if not guardrails['flags'] else 'BLOCKED: ' + ';'.join(guardrails['flags'])}",
        },
        "step6_route": {
            "lane": lane,
            "action": action,
            "reason": r["reason"],
            "message": f"Routed to {'AUTO-RESOLVE' if lane == 'auto' else 'HUMAN REVIEW'}",
        },
    }


@router.get("/tickets")
def list_tickets():
    decisions = [_processed[t] for t in _stream_order if t in _processed]
    return [
        {
            "ticket_id": d.ticket_id,
            "order_id": d.order_id,
            "created_at": _row_for(d.ticket_id)['created_at'],
            "description": d.description,
            "lane": d.lane,
            "status": d.status,
            "action": d.action,
            "confidence": d.confidence,
            "pipeline": d.pipeline,
            "explanation": d.explanation,
        }
        for d in decisions
    ]


@router.get("/stream/next")
def stream_next():
    """Process the next pending ticket. Returns the animated trace + decision."""
    global _stream_idx
    if _stream_idx >= len(_stream_order):
        return {"done": True, "processed": len(_processed), "remaining": 0, "total": len(_stream_order)}
    ticket_id = _stream_order[_stream_idx]
    _stream_idx += 1
    result = process_ticket(ticket_id)
    decision = result["decision"]
    return {
        "done": False,
        "ticket_id": decision.ticket_id,
        "lane": decision.lane,
        "action": decision.action,
        "confidence": decision.confidence,
        "pipeline": decision.pipeline,
        "trace": result["trace"],
        "order_context": _order_from_row(_row_for(ticket_id)).model_dump(),
        "remaining": len(_stream_order) - _stream_idx,
        "processed": _stream_idx,
        "total": len(_stream_order),
    }


@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket_detail(ticket_id: str):
    if ticket_id not in _stream_order:
        raise HTTPException(status_code=404, detail="Ticket not found")
    result = process_ticket(ticket_id)
    row = _row_for(ticket_id)
    return TicketDetailResponse(ticket=result["decision"], order_context=_order_from_row(row))


@router.get("/board", response_model=BoardSummary)
def board_summary():
    decisions = [_processed[t] for t in _stream_order if t in _processed]
    auto = sum(1 for d in decisions if d.lane == "auto")
    human = sum(1 for d in decisions if d.lane == "human")
    return BoardSummary(
        auto_resolved=auto,
        human_review=human,
        total=len(decisions),
        threshold=SIMILARITY_THRESHOLD,
        min_agreement=TOP_K // 2 + 1,
        pipeline_steps={
            "incoming": len(_stream_order),
            "pending": len(_stream_order) - len(decisions),
            "matched": len(decisions),
            "guardrail_checked": auto,
            "llm_reply": len(decisions),
        },
    )