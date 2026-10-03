import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from backend.models.user import User, UserRole
from backend.models.transaction import Transaction
from backend.models.case import Case
from backend.models.audit import AuditLog
from backend.services.auth_service import hash_password


class AdminService:
    @staticmethod
    def get_system_metrics(db: Session) -> Dict[str, Any]:
        """Aggregate system metrics across transactions, cases, users, and audit logs."""
        total_transactions = db.query(Transaction).count()
        flagged_transactions = db.query(Transaction).filter(Transaction.risk_level.in_(["HIGH", "CRITICAL"])).count()
        blocked_transactions = db.query(Transaction).filter(Transaction.risk_level == "CRITICAL").count()
        total_volume = db.query(func.sum(Transaction.amount)).scalar() or 0.0

        total_cases = db.query(Case).count()
        open_cases = db.query(Case).filter(Case.status == "OPEN").count()
        resolved_cases = db.query(Case).filter(Case.status == "RESOLVED").count()
        under_review_cases = db.query(Case).filter(Case.status == "UNDER_REVIEW").count()

        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()

        recent_audits = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(10).all()
        audit_items = [
            {
                "id": a.id,
                "username": a.username,
                "role": a.role,
                "action": a.action,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "details": a.details,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in recent_audits
        ]

        return {
            "transactions": {
                "total": total_transactions,
                "flagged": flagged_transactions,
                "blocked": blocked_transactions,
                "total_volume_bdt": float(total_volume),
                "fraud_rate_pct": round((flagged_transactions / total_transactions * 100) if total_transactions > 0 else 0, 2)
            },
            "cases": {
                "total": total_cases,
                "open": open_cases,
                "under_review": under_review_cases,
                "resolved": resolved_cases
            },
            "users": {
                "total": total_users,
                "active": active_users
            },
            "recent_audit_logs": audit_items
        }

    @staticmethod
    def list_users(db: Session) -> List[Dict[str, Any]]:
        users = db.query(User).order_by(User.username).all()
        return [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "department": u.department,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None
            }
            for u in users
        ]

    @staticmethod
    def create_user(db: Session, user_data: Dict[str, Any], creator_username: str) -> User:
        username = (user_data.get("username") or "").strip()
        email = (user_data.get("email") or "").strip().lower()
        full_name = (user_data.get("full_name") or "").strip()
        password = user_data.get("password") or ""
        role = (user_data.get("role") or UserRole.ANALYST).strip().upper()
        department = (user_data.get("department") or "Fraud Investigation Unit").strip()

        if not username:
            raise ValueError("Username is required.")
        if not email:
            raise ValueError("Email address is required.")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")
        if not full_name:
            raise ValueError("Full name is required.")
        if role not in UserRole.ALL:
            raise ValueError(f"Invalid clearance role. Must be one of: {', '.join(UserRole.ALL)}")

        # Check duplicate username
        existing_u = db.query(User).filter(User.username == username).first()
        if existing_u:
            raise ValueError(f"Username '@{username}' is already registered.")

        # Check duplicate email
        existing_e = db.query(User).filter(User.email == email).first()
        if existing_e:
            raise ValueError(f"Email '{email}' is already in use by another officer.")

        user_id = f"USR-{int(datetime.now(timezone.utc).timestamp()*1000)}"
        user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
            department=department,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        audit = AuditLog(
            username=creator_username,
            action="CREATE_USER",
            resource_type="user",
            resource_id=user.id,
            details=f"Provisioned personnel @{user.username} ({user.full_name}) with role clearance {user.role} in department '{user.department}'"
        )
        db.add(audit)
        db.commit()
        return user

    @staticmethod
    def toggle_user_status(db: Session, user_id: str, admin_username: str) -> Optional[User]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Prevent admin from suspending their own active account
        if user.username == admin_username and user.is_active:
            raise ValueError("Cannot suspend your own active administrator account.")

        user.is_active = not user.is_active
        db.commit()
        db.refresh(user)

        status_label = "ACTIVE" if user.is_active else "SUSPENDED"
        audit = AuditLog(
            username=admin_username,
            action="TOGGLE_USER_STATUS",
            resource_type="user",
            resource_id=user.id,
            details=f"Officer @{user.username} clearance status set to {status_label}"
        )
        db.add(audit)
        db.commit()
        return user

    @staticmethod
    def list_audit_logs(db: Session, limit: int = 50, page: int = 1) -> Tuple[List[Dict[str, Any]], int]:
        total = db.query(AuditLog).count()
        offset = (page - 1) * limit
        audits = db.query(AuditLog).order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
        items = [
            {
                "id": a.id,
                "username": a.username,
                "role": a.role,
                "action": a.action,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "details": a.details,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in audits
        ]
        return items, total
