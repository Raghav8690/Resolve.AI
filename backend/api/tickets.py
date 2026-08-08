from fastapi import APIRouter, HTTPException
from backend.services.data_loader import load_all
from backend.services.similarity import similarity_engine
from backend.services.router import route_ticket
from backend.services.guardrails import apply_guardrails
from backend.services.explanation import generate_explanation
from backend.services.llm_reply import generate_reply
from backend.services.decision_log import log_decision, get_board_summary, get_all_decisions
from backend.services.actions import simulate_action
from backend.models.schemas import TicketDecision, BoardSummary, TicketDetailResponse, OrderContext
from backend.config import SIMILARITY_THRESHOLD, TOP_K
from datetime import datetime

router = APIRouter()

resolved_df, new_with_orders_df, orders_df = load_all()
similarity_engine.fit(resolved_df)

_processed = {}


def _order_from_row(row) -> OrderContext:
    return OrderContext(
        order_id=row['order_id'],
        items=int(row['items']),
        value_inr=int(row['value_inr']),
        delivery_time_min=int(row['delivery_time_min']),
        delivery_status=row['delivery_status']
    )


def process_ticket(row):
    if row['ticket_id'] in _processed:
        return _processed[row['ticket_id']]

    r = route_ticket(row['description'])
    lane = r["lane"]
    suggested = r["suggested_action"]
    order = _order_from_row(row)

    if r["auto"]:
        action = suggested
        final_action, flags = apply_guardrails(action, order, r["precedents"])
        if final_action != action:
            lane = "human"
            r["reason"] = f"guardrail_block|{action}|{';'.join(flags)}"
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
        "agreement": r["agreement"],
        "threshold": SIMILARITY_THRESHOLD,
        "matched": len(r["precedents"]),
        "reason": r["reason"],
        "suggested_action": suggested,
    }
    decision.status = "auto-resolved" if lane == "auto" else "human-review"
    log_decision(decision)
    _processed[row['ticket_id']] = decision
    return decision


@router.get("/tickets")
def list_tickets():
    decisions = [process_ticket(row) for _, row in new_with_orders_df.iterrows()]
    return [
        {
            "ticket_id": d.ticket_id,
            "order_id": d.order_id,
            "created_at": new_with_orders_df.loc[new_with_orders_df['ticket_id'] == d.ticket_id, 'created_at'].iloc[0],
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


@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(ticket_id: str):
    row = new_with_orders_df[new_with_orders_df['ticket_id'] == ticket_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Ticket not found")
    row = row.iloc[0]
    decision = process_ticket(row)
    return TicketDetailResponse(ticket=decision, order_context=_order_from_row(row))


@router.get("/board", response_model=BoardSummary)
def get_board():
    summary = get_board_summary()
    summary = dict(summary)
    decisions = list(_processed.values())
    summary["threshold"] = SIMILARITY_THRESHOLD
    summary["min_agreement"] = TOP_K // 2 + 1
    summary["pipeline_steps"] = {
        "incoming": len(new_with_orders_df),
        "matched": sum(1 for d in decisions if d.pipeline["matched"] > 0),
        "guardrail_checked": sum(1 for d in decisions if d.lane == "auto"),
        "llm_reply": sum(1 for d in decisions if d.reply is not None),
    }
    return summary