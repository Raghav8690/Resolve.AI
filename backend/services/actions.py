from backend.models.schemas import OrderContext
from datetime import datetime

def simulate_action(action: str, ticket_id: str, order: OrderContext, precedents: list) -> dict:
    result = {
        "action": action,
        "ticket_id": ticket_id,
        "order_id": order.order_id,
        "timestamp": datetime.now().isoformat()
    }
    
    if action == "full_refund":
        result["amount"] = order.value_inr
        result["detail"] = f"Full refund of ₹{order.value_inr} processed"
    elif action == "partial_refund":
        amount = order.value_inr // 2
        result["amount"] = amount
        result["detail"] = f"Partial refund of ₹{amount} processed"
    elif action == "redelivery":
        result["detail"] = f"Redelivery scheduled for order {order.order_id}"
    elif action == "coupon":
        result["detail"] = "₹50 coupon issued"
    elif action == "refund_reissue":
        result["amount"] = order.value_inr
        result["detail"] = f"Refund re-triggered for ₹{order.value_inr}"
    elif action == "escalation":
        result["detail"] = "Escalated to payments team"
    elif action == "apology_no_action":
        result["detail"] = "Apology issued, no action needed (SLA breach < threshold)"
    else:
        result["detail"] = f"Action {action} logged"
    
    return result