from backend.services.similarity import similarity_engine
from backend.models.schemas import Precedent
from backend.config import SIMILARITY_THRESHOLD, MIN_AGREEMENT, TOP_K, AUTO_CONFIDENCE_THRESHOLD


def check_agreement(precedents: list[Precedent]) -> tuple[bool, str]:
    if len(precedents) < 2:
        return False, ""
    top_actions = [p.resolution_action for p in precedents[:TOP_K]]
    action_counts = {}
    for action in top_actions:
        action_counts[action] = action_counts.get(action, 0) + 1
    max_count = max(action_counts.values())
    agreed_action = max(action_counts, key=action_counts.get)
    return max_count >= MIN_AGREEMENT, agreed_action


def compute_confidence(precedents: list[Precedent], agreement_count: int) -> float:
    """Blend avg top-k similarity, top-3 agreement and averaged CSAT so the
    score never trivially saturates at 100% even for exact text duplicates.
    """
    if not precedents:
        return 0.0
    avg_sim = sum(p.similarity for p in precedents) / len(precedents)
    agree_ratio = agreement_count / len(precedents)
    csat_ratio = (sum(p.csat for p in precedents) / len(precedents)) / 5.0
    score = 0.50 * avg_sim + 0.35 * agree_ratio + 0.15 * csat_ratio
    return round(min(score, 0.995), 3)


def route_ticket(description: str) -> dict:
    """Route on the raw top-k precedents. A ticket may only be AUTO-RESOLVED
    when confidence >= AUTO_CONFIDENCE_THRESHOLD (0.8) AND the closest match
    clears the similarity bar AND the top-3 agree on an action. Anything
    below the confidence bar is routed to human review.
    """
    precedents = similarity_engine.get_top_k(description)
    top_similarity = precedents[0].similarity if precedents else 0.0

    if not precedents:
        return {
            "lane": "human", "auto": False, "precedents": [], "reason": "no_precedents_found",
            "top_similarity": 0.0, "agreement": 0, "agreed_action": None,
            "confidence": 0.0, "suggested_action": None,
        }

    agrees, agreed_action = check_agreement(precedents)
    agreement_count = sum(1 for p in precedents[:TOP_K] if p.resolution_action == agreed_action)
    confidence = compute_confidence(precedents, agreement_count)

    if confidence >= AUTO_CONFIDENCE_THRESHOLD and agrees and top_similarity >= SIMILARITY_THRESHOLD:
        lane, reason, auto = "auto", f"conf {confidence:.2f} >= {AUTO_CONFIDENCE_THRESHOLD}, {agreement_count}/{TOP_K} agree", True
        suggested = agreed_action
    else:
        lane, auto = "human", False
        reasons = []
        if confidence < AUTO_CONFIDENCE_THRESHOLD:
            reasons.append(f"low_confidence({confidence:.2f}<{AUTO_CONFIDENCE_THRESHOLD})")
        if top_similarity < SIMILARITY_THRESHOLD:
            reasons.append(f"low_similarity({top_similarity:.2f}<{SIMILARITY_THRESHOLD})")
        if not agrees:
            reasons.append("precedent_disagreement")
        reason = ";".join(reasons) if reasons else "no_precedents_found"
        suggested = agreed_action if agrees else None

    return {
        "lane": lane, "confidence": confidence, "precedents": precedents, "reason": reason,
        "auto": auto, "top_similarity": top_similarity, "agreement": agreement_count,
        "agreed_action": agreed_action, "suggested_action": suggested,
    }
