from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    title: str
    message: str
    category: Optional[str] = None


class TicketOut(BaseModel):
    id: int
    title: str
    sentiment: str
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


# --- QueueStorm /sort-ticket schemas ---------------------------------------

# Permitted values come straight from the task spec (§4).
ChannelType = Literal["app", "sms", "call_center", "merchant_portal"]
LocaleType = Literal["bn", "en", "mixed"]
CaseType = Literal[
    "wrong_transfer",
    "payment_failed",
    "refund_request",
    "phishing_or_social_engineering",
    "other",
]
Severity = Literal["low", "medium", "high", "critical"]
Department = Literal[
    "customer_support",
    "dispute_resolution",
    "payments_ops",
    "fraud_risk",
]


class SortTicketRequest(BaseModel):
    ticket_id: str = Field(..., min_length=1)
    channel: Optional[ChannelType] = None
    locale: Optional[LocaleType] = None
    message: str = Field(..., min_length=1)


class SortTicketResponse(BaseModel):
    ticket_id: str
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    human_review_required: bool
    confidence: float = Field(..., ge=0.0, le=1.0)