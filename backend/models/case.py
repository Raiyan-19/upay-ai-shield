from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base import Base


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String(32), primary_key=True, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), index=True)
    customer_id = Column(String(64), index=True)
    status = Column(String(32), default="OPEN", index=True)  # OPEN, UNDER_REVIEW, NEEDS_MORE_INFORMATION, RESOLVED
    priority = Column(String(32), default="MEDIUM", index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    assigned_analyst = Column(String(64), default="Tariq Hassan")
    analyst_notes = Column(Text, default="")
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(32), default="LOW")
    decision = Column(String(32), nullable=True)  # CONFIRM_SUSPICIOUS, MARK_LEGITIMATE, NEEDS_MORE_INVESTIGATION
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    transaction = relationship("Transaction", back_populates="cases")
    events = relationship("CaseEvent", back_populates="case", cascade="all, delete-orphan")


class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(32), ForeignKey("cases.case_id"), index=True)
    event_type = Column(String(64))  # CREATED, STATUS_CHANGE, NOTE_ADDED, DECISION_RECORDED, ESCALATION
    analyst_id = Column(String(64), default="Tariq Hassan")
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("Case", back_populates="events")
