from fastapi import APIRouter, HTTPException
import os
from backend.services.data_loader import load_all
from backend.services.similarity import similarity_engine
from backend.services.router import route_ticket
from backend.services.guardrails import apply_guardrails
from backend.services.explanation import generate_explanation
from backend.services.llm_reply import generate_reply
from backend.services.decision_log import log_decision
from backend.services.actions import simulate_action
from backend.models.schemas import TicketDecision, BoardSummary, TicketDetailResponse, OrderContext, Precedent, ReviewSubmit
from backend.config import SIMILARITY_THRESHOLD, TOP_K
from datetime import datetime

router = APIRouter()

resolved_df, new_with_orders_df, orders_df = load_all()
similarity_engine.fit(resolved_df)

_processed = {}
_stream_order = list(new_with_orders_df['ticket_id'])
_stream_idx = 0
_review_queue = {}


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
            r["reason"] = f"guardrail_applied|{action}->{final_action}|{';'.join(flags)}"
        action = final_action
    else:
        action = None
        flags = []

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
    if lane == "human":
        decision.review_status = "needs_review"
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
            "guardrail_flags": d.guardrail_flags,
            "review_status": d.review_status,
            "review_note": d.review_note,
            "reply": d.reply,
            "tags": _ticket_tags(d),
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


@router.post("/reset")
def reset_queue():
    """Reinitiate the queue from the start: clear processed decisions, reset
    the stream index to 0 and wipe the decision log so the demo replays
    from the first ticket.
    """
    global _stream_idx, _processed, _review_queue
    _processed = {}
    _stream_idx = 0
    _review_queue = {}
    from backend.services.decision_log import LOG_FILE
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    return {"reset": True, "total": len(_stream_order), "remaining": len(_stream_order)}


@router.get("/review/queue")
def review_queue():
    """All tickets with review status + tags. Supports filtering by tag, lane,
    confidence range and free-text search (for the human review console).
    """
    out = []
    for tid in _stream_order:
        d = _processed.get(tid)
        if d:
            out.append(_ticket_summary(d))
    return out


@router.get("/review/tags")
def review_tags():
    """All distinct tags across tickets, so the human can build filter chips."""
    tags = set()
    for tid in _stream_order:
        d = _processed.get(tid)
        if d:
            tags.update(_ticket_tags(d))
    return {"tags": sorted(tags)}


@router.post("/review/{ticket_id}")
def submit_review(ticket_id: str, body: ReviewSubmit):
    """Human writes (or overrides) a solution for ANY ticket. Stored as
    submitted, awaiting approval — it only 'passes' after /approve.
    Overriding an auto-resolved ticket is allowed: it goes back to review
    and its new solution supersedes the AI's suggestion.
    """
    if ticket_id not in _stream_order:
        raise HTTPException(status_code=404, detail="Ticket not found")
    d = _processed.get(ticket_id)
    if not d:
        raise HTTPException(status_code=404, detail="Ticket not processed yet")
    if d.review_status == "submitted":
        raise HTTPException(status_code=400, detail="Solution already submitted, awaiting review")
    if d.review_status == "approved":
        raise HTTPException(status_code=400, detail="Ticket already approved")

    order = _order_from_row(_row_for(ticket_id))
    final_action, flags = apply_guardrails(body.action, order, d.precedents)
    d.action = final_action
    d.review_note = body.note
    d.guardrail_flags = flags
    d.review_status = "submitted"
    d.status = "review-submitted"
    d.lane = "review" if d.lane == "auto" else d.lane
    if final_action != body.action:
        d.pipeline["reason"] = f"guardrail_applied|{body.action}->{final_action}|{';'.join(flags)}"
    log_decision(d)
    return _ticket_summary(d)


@router.post("/review/{ticket_id}/approve")
def approve_review(ticket_id: str):
    """Human reviews the submitted solution. On approval the action is applied
    and the ticket passes — marked resolved, removed from review queue.
    Handles both human-lane tickets and overridden auto/`review`-lane tickets.
    """
    if ticket_id not in _stream_order:
        raise HTTPException(status_code=404, detail="Ticket not found")
    d = _processed.get(ticket_id)
    if not d:
        raise HTTPException(status_code=404, detail="Ticket not processed yet")
    if d.review_status != "submitted":
        raise HTTPException(status_code=400, detail="No submitted solution to approve")

    order = _order_from_row(_row_for(ticket_id))
    simulate_action(d.action, ticket_id, order, d.precedents)
    if not d.reply:
        d.reply = generate_reply(ticket_id, d.description, d.action, order, d.precedents)
    d.review_status = "approved"
    d.status = "resolved"
    d.lane = "auto"  # passed review -> leaves human queue, joins resolved board
    log_decision(d)
    return _ticket_summary(d)


def _ticket_tags(d) -> list:
    """Human-searchable tags derived from the ticket's routing + guardrails."""
    tags = [d.lane, "confidence_" + str(round(d.confidence * 100))]
    if d.action:
        tags.append(d.action)
    if d.review_status:
        tags.append(d.review_status)
    for flag in d.guardrail_flags:
        tags.append(flag.replace("_", " "))
    return tags


def _ticket_summary(d):
    return {
        "ticket_id": d.ticket_id,
        "order_id": d.order_id,
        "description": d.description,
        "lane": d.lane,
        "status": d.status,
        "action": d.action,
        "confidence": d.confidence,
        "pipeline": d.pipeline,
        "explanation": d.explanation,
        "guardrail_flags": d.guardrail_flags,
        "review_status": d.review_status,
        "review_note": d.review_note,
        "reply": d.reply,
        "tags": _ticket_tags(d),
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
    review_needs = sum(1 for d in decisions if d.review_status == "needs_review")
    submitted = sum(1 for d in decisions if d.review_status == "submitted")
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
            "review_needs": review_needs,
            "review_submitted": submitted,
        },
    )