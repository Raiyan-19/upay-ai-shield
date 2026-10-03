import os
import json
from datetime import datetime, timezone, timedelta
from backend.models import Base, engine, SessionLocal, User, Customer, Transaction, Case, CaseEvent, AnalystFeedback, AuditLog
from backend.services.auth_service import AuthService


def initialize_database():
    """Creates all database tables and seeds demo accounts and records if empty."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed users
        AuthService.seed_initial_users(db)

        # Seed audit log for system start
        sys_audit = db.query(AuditLog).filter(AuditLog.action == "SYSTEM_BOOTSTRAP").first()
        if not sys_audit:
            db.add(AuditLog(
                username="system",
                role="ADMIN",
                action="SYSTEM_BOOTSTRAP",
                resource_type="system",
                resource_id="kernel",
                details="upay AI Shield full-stack database schema verified and initialized."
            ))
            db.commit()

        print("[upay-ai-shield] Database initialized and verified successfully.")
    except Exception as e:
        db.rollback()
        print(f"[upay-ai-shield] Error during DB initialization: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()
