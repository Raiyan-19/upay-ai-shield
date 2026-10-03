from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(64), primary_key=True, index=True)
    account_age_days = Column(Integer, default=730)
    normal_avg_amount = Column(Float, default=2500.0)
    normal_transaction_count = Column(Integer, default=10)
    primary_location = Column(String(128), default="Dhaka")
    registered_device_count = Column(Integer, default=2)
    account_created_date = Column(String(32), default="2022-01-01")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    transactions = relationship("Transaction", back_populates="customer")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), index=True)
    amount = Column(Float, nullable=False)
    timestamp = Column(String(64), index=True)
    hour = Column(Integer, default=14)
    day_of_week = Column(Integer, default=3)
    transaction_type = Column(String(64), default="SEND_MONEY")
    channel = Column(String(64), default="APP")
    receiver_id = Column(String(64), index=True)
    is_new_receiver = Column(Integer, default=0)
    device_id = Column(String(64), index=True)
    is_new_device = Column(Integer, default=0)
    location = Column(String(128), default="Dhaka")
    location_changed = Column(Integer, default=0)
    transactions_last_1h = Column(Integer, default=1)
    transactions_last_24h = Column(Integer, default=4)
    failed_attempts = Column(Integer, default=0)
    account_age_days = Column(Integer, default=730)
    receiver_transaction_count = Column(Integer, default=25)
    avg_transaction_amount = Column(Float, default=2500.0)
    amount_deviation = Column(Float, default=1.0)
    is_fraud = Column(Integer, default=0, index=True)
    demo_risk_score = Column(Float, default=10.0)
    risk_level = Column(String(32), default="LOW", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", back_populates="transactions")
    cases = relationship("Case", back_populates="transaction")
