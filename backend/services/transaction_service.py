import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from backend.models.transaction import Transaction, Customer
from backend.models.audit import AnalystFeedback, AuditLog
from backend.models.case import Case, CaseEvent
from backend.services.risk_service import RiskService


class TransactionService:
    @staticmethod
    def list_transactions(
        db: Session,
        page: int = 1,
        limit: int = 20,
        risk_level: Optional[str] = None,
        decision_action: Optional[str] = None,
        transaction_type: Optional[str] = None,
        channel: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "created_at",
        sort_dir: Optional[str] = "desc"
    ) -> Tuple[List[Transaction], int]:
        query = db.query(Transaction)

        if risk_level and risk_level.upper() != "ALL":
            query = query.filter(Transaction.risk_level == risk_level.upper())

        if transaction_type and transaction_type.upper() != "ALL":
            query = query.filter(Transaction.transaction_type == transaction_type)

        if channel and channel.upper() != "ALL":
            query = query.filter(Transaction.channel == channel)

        if min_amount is not None:
            query = query.filter(Transaction.amount >= min_amount)

        if max_amount is not None:
            query = query.filter(Transaction.amount <= max_amount)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Transaction.transaction_id.ilike(search_pattern)) |
                (Transaction.customer_id.ilike(search_pattern)) |
                (Transaction.receiver_id.ilike(search_pattern)) |
                (Transaction.location.ilike(search_pattern))
            )

        total = query.count()

        # Sorting
        sort_column = getattr(Transaction, sort_by, Transaction.created_at)
        if sort_dir.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        offset = (page - 1) * limit
        items = query.offset(offset).limit(limit).all()
        return items, total

    @staticmethod
    def get_transaction_by_id(db: Session, transaction_id: str) -> Optional[Dict[str, Any]]:
        tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        if not tx:
            return None

        # Customer baseline
        customer = db.query(Customer).filter(Customer.customer_id == tx.customer_id).first()
        customer_info = None
        if customer:
            customer_info = {
                "customer_id": customer.customer_id,
                "account_age_days": customer.account_age_days,
                "normal_avg_amount": customer.normal_avg_amount,
                "normal_transaction_count": customer.normal_transaction_count,
                "primary_location": customer.primary_location,
                "registered_device_count": customer.registered_device_count,
                "account_created_date": customer.account_created_date
            }

        # Analyst feedbacks
        feedbacks = db.query(AnalystFeedback).filter(AnalystFeedback.transaction_id == transaction_id).all()
        feedback_list = [
            {
                "id": f.id,
                "decision": f.decision,
                "comment": f.comment,
                "analyst_id": f.analyst_id,
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in feedbacks
        ]

        # Case association
        associated_case = db.query(Case).filter(Case.transaction_id == transaction_id).first()
        case_info = None
        if associated_case:
            case_info = {
                "case_id": associated_case.case_id,
                "status": associated_case.status,
                "priority": associated_case.priority,
                "assigned_analyst": associated_case.assigned_analyst
            }

        # Dynamic risk breakdown calculation
        tx_data = {
            "transaction_id": tx.transaction_id,
            "customer_id": tx.customer_id,
            "amount": tx.amount,
            "transaction_type": tx.transaction_type,
            "channel": tx.channel,
            "device_id": tx.device_id,
            "location": tx.location,
            "recipient_account": tx.receiver_id,
            "is_new_recipient": bool(tx.is_new_receiver),
            "is_night_transaction": bool(tx.hour < 5 if tx.hour is not None else False),
            "failed_pin_attempts_last_hour": tx.failed_attempts or 0,
            "device_changed_recently": bool(tx.is_new_device),
            "velocity_1h_count": tx.transactions_last_1h or 1,
            "velocity_24h_count": tx.transactions_last_24h or 4,
            "amount_deviation_score": tx.amount_deviation or 1.0,
            "timestamp": tx.timestamp if isinstance(tx.timestamp, str) else (tx.timestamp.isoformat() if tx.timestamp else None)
        }
        risk_result = RiskService.assess_transaction_data(db, tx_data)

        # Derived decision action based on score
        score = tx.demo_risk_score if tx.demo_risk_score is not None else 10.0
        if score >= 80:
            decision = "BLOCK" if score >= 90 else "REVIEW"
        elif score >= 50:
            decision = "REVIEW"
        else:
            decision = "APPROVE"

        return {
            "transaction": {
                "transaction_id": tx.transaction_id,
                "customer_id": tx.customer_id,
                "amount": tx.amount,
                "transaction_type": tx.transaction_type,
                "channel": tx.channel,
                "device_id": tx.device_id,
                "ip_address": "103.114.98.12",
                "location": tx.location,
                "recipient_account": tx.receiver_id,
                "is_new_recipient": bool(tx.is_new_receiver),
                "is_night_transaction": bool(tx.hour < 5 if tx.hour is not None else False),
                "failed_pin_attempts_last_hour": tx.failed_attempts or 0,
                "device_changed_recently": bool(tx.is_new_device),
                "velocity_1h_count": tx.transactions_last_1h or 1,
                "velocity_24h_count": tx.transactions_last_24h or 4,
                "amount_deviation_score": tx.amount_deviation or 1.0,
                "risk_score": score,
                "decision_action": decision,
                "risk_level": tx.risk_level or "LOW",
                "timestamp": tx.timestamp if isinstance(tx.timestamp, str) else (tx.timestamp.isoformat() if tx.timestamp else None),
                "created_at": tx.created_at.isoformat() if tx.created_at else None
            },
            "customer_baseline": customer_info,
            "risk_assessment": risk_result,
            "feedbacks": feedback_list,
            "associated_case": case_info
        }

    @staticmethod
    def record_feedback(db: Session, transaction_id: str, decision: str, comment: str, analyst_id: str) -> AnalystFeedback:
        fb = AnalystFeedback(
            transaction_id=transaction_id,
            decision=decision,
            comment=comment,
            analyst_id=analyst_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)

        audit = AuditLog(
            username=analyst_id,
            action="FEEDBACK_RECORDED",
            resource_type="transaction",
            resource_id=transaction_id,
            details=f"Analyst decided {decision}: {comment}"
        )
        db.add(audit)
        db.commit()
        return fb
