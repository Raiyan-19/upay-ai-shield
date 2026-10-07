from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from backend.models.base import Base


class UserRole:
    ADMIN = "ADMIN"
    SENIOR_OFFICER = "SENIOR_OFFICER"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"
    CUSTOMER = "CUSTOMER"

    ALL = [ADMIN, SENIOR_OFFICER, ANALYST, VIEWER, CUSTOMER]


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(String(32), default=UserRole.ANALYST, index=True)
    department = Column(String(128), default="Fraud Investigation Unit")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)
