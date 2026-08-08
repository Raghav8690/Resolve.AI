from backend.models.schemas import Precedent

def generate_explanation(lane: str, action: str, precedents: list[Precedent], reason: str = "") -> str:
    if lane == "auto":
        precedent_ids = ", ".join([p.ticket_id for p in precedents[:3]])
        actions = [p.resolution_action for p in precedents[:3]]
        common_action = max(set(actions), key=actions.count)
        return (
            f"Auto-resolved via {common_action} based on 3 similar precedents: "
            f"{precedent_ids}. All three precedents agreed on {common_action}."
        )
    else:
        if "low_similarity" in reason:
            top = ", ".join([f"{p.ticket_id}({p.similarity:.2f})" for p in precedents[:3]])
            return f"Routed to human: top similarity too low to trust precedent ({reason}). Closest precedents: {top}"
        elif "precedent_disagreement" in reason:
            actions = [p.resolution_action for p in precedents[:3]]
            return f"Routed to human: precedents disagree on action ({', '.join(set(actions))}). " \
                   f"Confidence is not unanimous enough to auto-resolve."
        elif "guardrail_block" in reason:
            parts = reason.split("|")
            suggested = parts[1] if len(parts) > 1 else "unknown"
            block_flags = parts[2] if len(parts) > 2 else ""
            return f"Routed to human: blocked by order-context guardrail ({block_flags.replace(';', ', ')}). " \
                   f"Text similarity suggests '{suggested}' but the order status disallows it."
        elif "no_precedents" in reason:
            return "Routed to human: no similar precedents found"
        else:
            return f"Routed to human: {reason}"
