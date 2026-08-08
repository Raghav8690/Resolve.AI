from backend.services.similarity import similarity_engine
from backend.models.schemas import Precedent
from backend.config import SIMILARITY_THRESHOLD, MIN_AGREEMENT

def check_agreement(precedents: list[Precedent]) -> tuple[bool, str]:
    if len(precedents) < 2:
        return False, "insufficient_precedents"
    
    top_actions = [p.resolution_action for p in precedents[:3]]
    action_counts = {}
    for action in top_actions:
        action_counts[action] = action_counts.get(action, 0) + 1
    
    max_count = max(action_counts.values())
    agreed_action = max(action_counts, key=action_counts.get)
    
    return max_count >= MIN_AGREEMENT, agreed_action

def route_ticket(description: str) -> tuple[str, float, list[Precedent], str, bool]:
    precedents = similarity_engine.get_top_k(description)
    
    if not precedents:
        return "human", 0.0, [], "no_precedents_found", False
    
    top_similarity = precedents[0].similarity
    agrees, agreed_action = check_agreement(precedents)
    
    if top_similarity >= SIMILARITY_THRESHOLD and agrees:
        return "auto", top_similarity, precedents, agreed_action, True
    else:
        reason = []
        if top_similarity < SIMILARITY_THRESHOLD:
            reason.append(f"low_similarity({top_similarity:.2f}<{SIMILARITY_THRESHOLD})")
        if not agrees:
            reason.append("precedent_disagreement")
        return "human", top_similarity, precedents, ";".join(reason), False
