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
    review_status: Optional[str] = None  # needs_review | submitted | approved
    review_note: Optional[str] = None
    timestamp: datetime
    pipeline: Optional[dict] = None
    status: Optional[str] = None

class ReviewSubmit(BaseModel):
    action: str
    note: str

class BoardSummary(BaseModel):
    auto_resolved: int
    human_review: int
    total: int
    threshold: Optional[float] = None
    min_agreement: Optional[int] = None
    pipeline_steps: Optional[dict] = None

class TicketDetailResponse(BaseModel):
    ticket: TicketDecision
    order_context: OrderContext
