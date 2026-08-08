from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ResolvedTicket(BaseModel):
    ticket_id: str
    category: str
    description: str
    resolution_action: str
    resolution_note: str
    time_to_resolve_min: int
    csat: int

class NewTicket(BaseModel):
    ticket_id: str
    created_at: str
    order_id: str
    description: str

class OrderContext(BaseModel):
    order_id: str
    items: int
    value_inr: int
    delivery_time_min: int
    delivery_status: str

class Precedent(BaseModel):
    ticket_id: str
    description: str
    resolution_action: str
    similarity: float
    csat: int

class TicketDecision(BaseModel):
    ticket_id: str
    order_id: str
    description: str
    lane: str
    action: Optional[str] = None
    confidence: float
    precedents: List[Precedent]
    explanation: str
    reply: Optional[str] = None
    guardrail_flags: List[str] = []
    timestamp: datetime

class BoardSummary(BaseModel):
    auto_resolved: int
    human_review: int
    total: int

class TicketDetailResponse(BaseModel):
    ticket: TicketDecision
    order_context: OrderContext
