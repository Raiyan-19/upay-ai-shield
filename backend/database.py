import os
import json
import csv
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "upay_ai_shield.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


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


class AnalystFeedback(Base):
    __tablename__ = "analyst_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), index=True)
    decision = Column(String(32), index=True)  # SUSPICIOUS, LEGITIMATE, NEEDS_REVIEW
    comment = Column(Text, default="")
    analyst_id = Column(String(64), default="analyst_lead_01", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


def init_db():
    Base.metadata.create_all(bind=engine)
    seed_db_if_empty()


def seed_db_if_empty():
    db = SessionLocal()
    try:
        cust_count = db.query(Customer).count()
        if cust_count == 0:
            customers_json_path = os.path.join(BASE_DIR, "model and chatboat", "data", "sample_customers.json")
            if os.path.exists(customers_json_path):
                with open(customers_json_path, "r", encoding="utf-8") as f:
                    cust_data = json.load(f)
                    for item in cust_data:
                        c = Customer(
                            customer_id=item.get("customer_id"),
                            account_age_days=int(item.get("account_age_days", 730)),
                            normal_avg_amount=float(item.get("normal_avg_amount", 2500.0)),
                            normal_transaction_count=int(item.get("normal_transaction_count", 10)),
                            primary_location=item.get("primary_location", "Dhaka"),
                            registered_device_count=int(item.get("registered_device_count", 2)),
                            account_created_date=item.get("account_created_date", "2022-01-01")
                        )
                        db.merge(c)
                db.commit()

        tx_count = db.query(Transaction).count()
        if tx_count == 0:
            tx_csv_path = os.path.join(BASE_DIR, "model and chatboat", "data", "sample_transactions.csv")
            if os.path.exists(tx_csv_path):
                with open(tx_csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        cid = row.get("customer_id")
                        existing_cust = db.query(Customer).filter_by(customer_id=cid).first()
                        if not existing_cust:
                            db.add(Customer(
                                customer_id=cid,
                                account_age_days=int(float(row.get("account_age_days", 730))),
                                normal_avg_amount=float(row.get("avg_transaction_amount", 2500.0)),
                                normal_transaction_count=10,
                                primary_location=row.get("location", "Dhaka"),
                                registered_device_count=2,
                                account_created_date="2022-01-01"
                            ))
                            db.commit()

                        tx = Transaction(
                            transaction_id=row.get("transaction_id"),
                            customer_id=cid,
                            amount=float(row.get("amount", 0.0)),
                            timestamp=row.get("timestamp"),
                            hour=int(float(row.get("hour", 14))),
                            day_of_week=int(float(row.get("day_of_week", 3))),
                            transaction_type=row.get("transaction_type", "SEND_MONEY"),
                            channel=row.get("channel", "APP"),
                            receiver_id=row.get("receiver_id"),
                            is_new_receiver=int(float(row.get("is_new_receiver", 0))),
                            device_id=row.get("device_id"),
                            is_new_device=int(float(row.get("is_new_device", 0))),
                            location=row.get("location", "Dhaka"),
                            location_changed=int(float(row.get("location_changed", 0))),
                            transactions_last_1h=int(float(row.get("transactions_last_1h", 1))),
                            transactions_last_24h=int(float(row.get("transactions_last_24h", 4))),
                            failed_attempts=int(float(row.get("failed_attempts", 0))),
                            account_age_days=int(float(row.get("account_age_days", 730))),
                            receiver_transaction_count=int(float(row.get("receiver_transaction_count", 25))),
                            avg_transaction_amount=float(row.get("avg_transaction_amount", 2500.0)),
                            amount_deviation=float(row.get("amount_deviation", 1.0)),
                            is_fraud=int(float(row.get("is_fraud", 0))),
                            demo_risk_score=float(row.get("demo_risk_score", 10.0)),
                            risk_level=row.get("risk_level", "LOW")
                        )
                        db.merge(tx)
                db.commit()

        # Seed initial rich case management records if none exist
        case_count = db.query(Case).count()
        if case_count == 0:
            high_risk_txs = db.query(Transaction).filter(Transaction.risk_level.in_(["HIGH", "MEDIUM"])).limit(16).all()
            statuses = ["OPEN", "UNDER_REVIEW", "NEEDS_MORE_INFORMATION", "RESOLVED"]
            priorities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            analysts = ["Tariq Hassan", "Farhana Yasmin", "Tanvir Ahmed", "Sadia Rahman"]

            now = datetime.now(timezone.utc)
            for idx, tx in enumerate(high_risk_txs):
                status = statuses[idx % len(statuses)]
                priority = "CRITICAL" if tx.demo_risk_score > 90 else ("HIGH" if tx.demo_risk_score > 70 else "MEDIUM")
                analyst = analysts[idx % len(analysts)]
                created_delta = timedelta(days=idx * 2, hours=idx * 3)
                case_created = now - created_delta

                case_id = f"CASE-{1000 + idx}"
                c = Case(
                    case_id=case_id,
                    transaction_id=tx.transaction_id,
                    customer_id=tx.customer_id,
                    status=status,
                    priority=priority,
                    assigned_analyst=analyst,
                    analyst_notes=f"Flagged by XGBoost risk engine with score {tx.demo_risk_score:.1f}. Amount: ৳{tx.amount:,.2f} with deviation factor {tx.amount_deviation:.1f}x. Device: {tx.device_id}.",
                    risk_score=tx.demo_risk_score,
                    risk_level=tx.risk_level,
                    decision="CONFIRM_SUSPICIOUS" if status == "RESOLVED" and idx % 2 == 0 else ("MARK_LEGITIMATE" if status == "RESOLVED" else None),
                    created_at=case_created,
                    updated_at=case_created + timedelta(hours=2)
                )
                db.add(c)
                db.commit()

                # Add events
                ev1 = CaseEvent(
                    case_id=case_id,
                    event_type="CREATED",
                    analyst_id="System Engine",
                    description=f"Automated risk triage detected {tx.risk_level} risk score ({tx.demo_risk_score:.1f}/100).",
                    created_at=case_created
                )
                db.add(ev1)

                if status != "OPEN":
                    ev2 = CaseEvent(
                        case_id=case_id,
                        event_type="STATUS_CHANGE",
                        analyst_id=analyst,
                        description=f"Status transitioned to {status}. Outreach checklist initiated.",
                        created_at=case_created + timedelta(hours=1)
                    )
                    db.add(ev2)

                if status == "RESOLVED":
                    ev3 = CaseEvent(
                        case_id=case_id,
                        event_type="DECISION_RECORDED",
                        analyst_id=analyst,
                        description=f"Formal human analyst determination: {c.decision}. Audit record synchronized to feedback store.",
                        created_at=case_created + timedelta(hours=2)
                    )
                    db.add(ev3)
                    # Add to feedback
                    db.add(AnalystFeedback(
                        transaction_id=tx.transaction_id,
                        decision="SUSPICIOUS" if c.decision == "CONFIRM_SUSPICIOUS" else "LEGITIMATE",
                        comment=f"Resolved case {case_id}: {c.analyst_notes}",
                        analyst_id=analyst,
                        created_at=case_created + timedelta(hours=2)
                    ))

            db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
