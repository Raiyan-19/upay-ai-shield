from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from backend.models.base import Base


class AnalystFeedback(Base):
    __tablename__ = "analyst_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), index=True)
    decision = Column(String(32), index=True)  # SUSPICIOUS, LEGITIMATE, NEEDS_REVIEW
    comment = Column(Text, default="")
    analyst_id = Column(String(64), default="analyst_lead_01", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), index=True, nullable=True)
    username = Column(String(64), index=True, default="system")
    role = Column(String(32), default="ANALYST")
    action = Column(String(64), index=True)  # LOGIN, LOGOUT, CASE_UPDATE, TRANSACTION_FLAG, POLICY_CHANGE, SIMULATION
    resource_type = Column(String(64), index=True)  # case, transaction, user, system
    resource_id = Column(String(64), nullable=True)
    details = Column(Text, default="")
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(256), nullable=True)
    prev_hash = Column(String(64), nullable=True, default="GENESIS")
    curr_hash = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

