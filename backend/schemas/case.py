from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CaseEventResponse(BaseModel):
    id: int
    case_id: str
    event_type: str
    analyst_id: str
    description: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CaseResponse(BaseModel):
    case_id: str
    transaction_id: str
    customer_id: str
    status: str
    priority: str
    assigned_analyst: str
    analyst_notes: str
    risk_score: float
    risk_level: str
    decision: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    events: Optional[List[CaseEventResponse]] = []

    class Config:
        from_attributes = True


class CaseUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_analyst: Optional[str] = None
    analyst_notes: Optional[str] = None


class CaseDecision(BaseModel):
    decision: str = Field(..., description="CONFIRM_SUSPICIOUS, MARK_LEGITIMATE, or NEEDS_MORE_INVESTIGATION")
    notes: Optional[str] = ""
