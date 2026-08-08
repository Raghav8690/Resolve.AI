from backend.models.schemas import OrderContext

def apply_guardrails(action: str, order: OrderContext, precedents: list) -> tuple[str, list[str]]:
    flags = []
    final_action = action
    
    if action in ["redelivery", "partial_refund", "full_refund"]:
        if order.delivery_status == "cancelled":
            flags.append("cancelled_order_blocks_redelivery_refund")
            final_action = "escalation"
    
    if action in ["full_refund", "partial_refund", "refund_reissue"]:
        refund_amount = estimate_refund_amount(action, order, precedents)
        if refund_amount > order.value_inr:
            flags.append(f"refund_cap_exceeded({refund_amount}>{order.value_inr})")
            final_action = "escalation"
    
    if action == "redelivery" and order.delivery_status == "delivered":
        if any("missing" in p.description.lower() or "got " in p.description.lower() for p in precedents):
            pass
        else:
            flags.append("redelivery_on_delivered_order_flagged")
    
    return final_action, flags

def estimate_refund_amount(action: str, order: OrderContext, precedents: list) -> int:
    if action == "full_refund":
        return order.value_inr
    elif action == "partial_refund":
        return order.value_inr // 2
    elif action == "refund_reissue":
        return order.value_inr
    return 0
