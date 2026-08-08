from fastapi import APIRouter, HTTPException
from backend.services.data_loader import load_all, join_new_tickets_with_orders
from backend.services.similarity import similarity_engine
from backend.services.router import route_ticket
from backend.services.guardrails import apply_guardrails
from backend.services.explanation import generate_explanation
from backend.services.llm_reply import generate_reply
from backend.services.decision_log import log_decision, get_board_summary, get_all_decisions
from backend.services.actions import simulate_action
from backend.models.schemas import TicketDecision, BoardSummary, TicketDetailResponse, OrderContext, Precedent
from datetime import datetime

router = APIRouter()

# Load data at startup
resolved_df, new_with_orders_df, orders_df = load_all()
similarity_engine.fit(resolved_df)

# Process all new tickets at startup
_processed = {}

def process_ticket(row):
    if row['ticket_id'] in _processed:
        return _processed[row['ticket_id']]
    
    lane, confidence, precedents, action_or_reason, auto = route_ticket(row['description'])
    
    order = OrderContext(
        order_id=row['order_id'],
        items=int(row['items']),
        value_inr=int(row['value_inr']),
        delivery_time_min=int(row['delivery_time_min']),
        delivery_status=row['delivery_status']
    )
    
    if auto:
        action = action_or_reason
        suggested_action = action
        final_action, flags = apply_guardrails(action, order, precedents)
        if final_action != action:
            lane = "human"
            auto = False
            action_or_reason = f"guardrail_block|{suggested_action}|{';'.join(flags)}"
        action = final_action
    else:
        action = None
        flags = []
    
    explanation = generate_explanation(lane, action or "none", precedents, action_or_reason if not auto else "")
    reply = None
    if action:
        reply = generate_reply(row['ticket_id'], row['description'], action, order, precedents)
        simulate_action(action, row['ticket_id'], order, precedents)
    
    decision = TicketDecision(
        ticket_id=row['ticket_id'],
        order_id=row['order_id'],
        description=row['description'],
        lane=lane,
        action=action,
        confidence=confidence,
        precedents=precedents,
        explanation=explanation,
        reply=reply,
        guardrail_flags=flags,
        timestamp=datetime.now()
    )
    
    log_decision(decision)
    _processed[row['ticket_id']] = decision
    return decision

@router.get("/tickets")
def list_tickets():
    decisions = [process_ticket(row) for _, row in new_with_orders_df.iterrows()]
    return [{"ticket_id": d.ticket_id, "lane": d.lane, "action": d.action, "confidence": d.confidence} for d in decisions]

@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(ticket_id: str):
    row = new_with_orders_df[new_with_orders_df['ticket_id'] == ticket_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Ticket not found")
    row = row.iloc[0]
    decision = process_ticket(row)
    order = OrderContext(
        order_id=row['order_id'],
        items=int(row['items']),
        value_inr=int(row['value_inr']),
        delivery_time_min=int(row['delivery_time_min']),
        delivery_status=row['delivery_status']
    )
    return TicketDetailResponse(ticket=decision, order_context=order)

@router.get("/board", response_model=BoardSummary)
def get_board():
    return get_board_summary()

@router.post("/process")
def process_all():
    decisions = [process_ticket(row) for _, row in new_with_orders_df.iterrows()]
    return {"processed": len(decisions), "summary": get_board_summary()}
