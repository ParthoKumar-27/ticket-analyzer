from datetime import datetime
from typing import Optional
from pydantic import BaseModel


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