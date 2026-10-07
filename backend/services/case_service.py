import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc
from backend.models.case import Case, CaseEvent
from backend.models.transaction import Transaction, Customer
from backend.models.audit import AuditLog


class CaseService:
    @staticmethod
    def list_cases(
        db: Session,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_analyst: Optional[str] = None,
        search: Optional[str] = None,
        date_preset: Optional[str] = None,
        specific_date: Optional[str] = None,
        sort_by: Optional[str] = "created_at",
        sort_dir: Optional[str] = "desc"
    ) -> Tuple[List[Case], int]:
        query = db.query(Case).options(joinedload(Case.transaction))

        if status and status.upper() != "ALL":
            query = query.filter(Case.status == status.upper())

        if priority and priority.upper() != "ALL":
            query = query.filter(Case.priority == priority.upper())

        if assigned_analyst and assigned_analyst.lower() != "all":
            query = query.filter(Case.assigned_analyst.ilike(f"%{assigned_analyst}%"))

        if specific_date:
            try:
                dt = datetime.strptime(specific_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                query = query.filter(Case.created_at >= dt, Case.created_at < dt + timedelta(days=1))
            except Exception:
                pass
        elif date_preset and date_preset.upper() != "ALL":
            dp = date_preset.upper()
            now = datetime.now(timezone.utc)
            if dp == "TODAY":
                start_today = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
                query = query.filter(Case.created_at >= start_today)
            elif dp == "YESTERDAY":
                yesterday = now - timedelta(days=1)
                start_yesterday = datetime(yesterday.year, yesterday.month, yesterday.day, tzinfo=timezone.utc)
                end_yesterday = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
                query = query.filter(Case.created_at >= start_yesterday, Case.created_at < end_yesterday)
            elif dp == "THIS_WEEK":
                start_week = now - timedelta(days=7)
                query = query.filter(Case.created_at >= start_week)
            elif dp == "THIS_MONTH":
                start_month = now - timedelta(days=30)
                query = query.filter(Case.created_at >= start_month)
            else:
                try:
                    dt = datetime.strptime(date_preset, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    query = query.filter(Case.created_at >= dt, Case.created_at < dt + timedelta(days=1))
                except Exception:
                    pass

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Case.case_id.ilike(search_pattern)) |
                (Case.transaction_id.ilike(search_pattern)) |
                (Case.customer_id.ilike(search_pattern)) |
                (Case.assigned_analyst.ilike(search_pattern)) |
                (Case.analyst_notes.ilike(search_pattern))
            )

        total = query.count()

        sort_column = getattr(Case, sort_by, Case.created_at)
        if sort_dir.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        offset = (page - 1) * limit
        items = query.offset(offset).limit(limit).all()
        return items, total

    @staticmethod
    def get_case_by_id(db: Session, case_id: str) -> Optional[Dict[str, Any]]:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            return None

        # Fetch events ordered by created_at
        events = db.query(CaseEvent).filter(CaseEvent.case_id == case_id).order_by(asc(CaseEvent.created_at)).all()
        events_data = [
            {
                "id": ev.id,
                "case_id": ev.case_id,
                "event_type": ev.event_type,
                "analyst_id": ev.analyst_id,
                "description": ev.description,
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            }
            for ev in events
        ]

        # Fetch transaction details
        tx = db.query(Transaction).filter(Transaction.transaction_id == case.transaction_id).first()
        tx_data = None
        if tx:
            tx_data = {
                "transaction_id": tx.transaction_id,
                "customer_id": tx.customer_id,
                "amount": tx.amount,
                "transaction_type": tx.transaction_type,
                "channel": tx.channel,
                "device_id": tx.device_id,
                "ip_address": tx.ip_address,
                "location": tx.location,
                "recipient_account": tx.recipient_account,
                "is_new_recipient": tx.is_new_recipient,
                "is_night_transaction": tx.is_night_transaction,
                "failed_pin_attempts_last_hour": tx.failed_pin_attempts_last_hour,
                "device_changed_recently": tx.device_changed_recently,
                "sim_changed_recently": tx.sim_changed_recently,
                "velocity_1h_count": tx.velocity_1h_count,
                "velocity_24h_count": tx.velocity_24h_count,
                "amount_deviation_score": tx.amount_deviation_score,
                "risk_score": tx.risk_score,
                "decision_action": tx.decision_action,
                "risk_level": tx.risk_level,
                "created_at": tx.created_at.isoformat() if tx.created_at else None
            }

        # Fetch customer baseline
        cust = db.query(Customer).filter(Customer.customer_id == case.customer_id).first()
        cust_data = None
        if cust:
            cust_data = {
                "customer_id": cust.customer_id,
                "account_age_days": cust.account_age_days,
                "normal_avg_amount": cust.normal_avg_amount,
                "normal_transaction_count": cust.normal_transaction_count,
                "primary_location": cust.primary_location,
                "registered_device_count": cust.registered_device_count,
                "account_created_date": cust.account_created_date
            }

        return {
            "case": {
                "case_id": case.case_id,
                "transaction_id": case.transaction_id,
                "customer_id": case.customer_id,
                "status": case.status,
                "priority": case.priority,
                "assigned_analyst": case.assigned_analyst,
                "analyst_notes": case.analyst_notes,
                "risk_score": case.risk_score,
                "risk_level": case.risk_level,
                "decision": case.decision,
                "created_at": case.created_at.isoformat() if case.created_at else None,
                "updated_at": case.updated_at.isoformat() if case.updated_at else None
            },
            "events": events_data,
            "transaction": tx_data,
            "customer": cust_data
        }

    @staticmethod
    def update_case(
        db: Session,
        case_id: str,
        analyst_user: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_analyst: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[Case]:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            return None

        now = datetime.now(timezone.utc)
        case.updated_at = now

        if status and status != case.status:
            old_status = case.status
            case.status = status
            event = CaseEvent(
                case_id=case_id,
                event_type="STATUS_CHANGE",
                analyst_id=analyst_user,
                description=f"Status transitioned from {old_status} to {status}",
                created_at=now
            )
            db.add(event)

        if priority and priority != case.priority:
            old_priority = case.priority
            case.priority = priority
            event = CaseEvent(
                case_id=case_id,
                event_type="PRIORITY_CHANGE",
                analyst_id=analyst_user,
                description=f"Priority updated from {old_priority} to {priority}",
                created_at=now
            )
            db.add(event)

        if assigned_analyst and assigned_analyst != case.assigned_analyst:
            old_assigned = case.assigned_analyst
            case.assigned_analyst = assigned_analyst
            event = CaseEvent(
                case_id=case_id,
                event_type="ASSIGNMENT_CHANGE",
                analyst_id=analyst_user,
                description=f"Case reassigned from {old_assigned} to {assigned_analyst}",
                created_at=now
            )
            db.add(event)

        if notes:
            case.analyst_notes = (case.analyst_notes + "\n" + notes).strip() if case.analyst_notes else notes
            event = CaseEvent(
                case_id=case_id,
                event_type="NOTE_ADDED",
                analyst_id=analyst_user,
                description=f"Note: {notes}",
                created_at=now
            )
            db.add(event)

        db.commit()
        db.refresh(case)
        return case

    @staticmethod
    def record_decision(
        db: Session,
        case_id: str,
        decision: str,
        notes: str,
        analyst_user: str
    ) -> Optional[Case]:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            return None

        now = datetime.now(timezone.utc)
        case.decision = decision
        case.status = "RESOLVED"
        case.updated_at = now
        if notes:
            case.analyst_notes = (case.analyst_notes + f"\n[{decision}] {notes}").strip()

        event = CaseEvent(
            case_id=case_id,
            event_type="DECISION_RECORDED",
            analyst_id=analyst_user,
            description=f"Final decision: {decision}. Notes: {notes}",
            created_at=now
        )
        db.add(event)

        audit = AuditLog(
            username=analyst_user,
            action="CASE_DECISION",
            resource_type="case",
            resource_id=case_id,
            details=f"Case resolved with decision {decision}"
        )
        db.add(audit)
        db.commit()
        db.refresh(case)
        return case
