import json
from datetime import datetime
from backend.models.schemas import TicketDecision, Precedent

LOG_FILE = "data/decision_log.jsonl"

def log_decision(decision: TicketDecision):
    entry = {
        "ticket_id": decision.ticket_id,
        "order_id": decision.order_id,
        "description": decision.description,
        "lane": decision.lane,
        "action": decision.action,
        "confidence": decision.confidence,
        "precedents": [
            {"ticket_id": p.ticket_id, "action": p.resolution_action, "similarity": p.similarity, "csat": p.csat}
            for p in decision.precedents
        ],
        "explanation": decision.explanation,
        "reply": decision.reply,
        "guardrail_flags": decision.guardrail_flags,
        "timestamp": decision.timestamp.isoformat()
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def get_all_decisions() -> list[dict]:
    decisions = []
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                decisions.append(json.loads(line.strip()))
    except FileNotFoundError:
        pass
    return decisions

def get_board_summary() -> dict:
    decisions = get_all_decisions()
    auto = sum(1 for d in decisions if d["lane"] == "auto")
    human = sum(1 for d in decisions if d["lane"] == "human")
    return {"auto_resolved": auto, "human_review": human, "total": len(decisions)}
