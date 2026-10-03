from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.base import get_db
from backend.models.transaction import Transaction
from backend.models.case import Case
from backend.schemas.common import ApiResponse

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=ApiResponse[dict])
def get_dashboard_metrics(db: Session = Depends(get_db)):
    total_tx = db.query(Transaction).count()
    flagged_tx = db.query(Transaction).filter(Transaction.decision_action.in_(["REVIEW", "BLOCK"])).count()
    blocked_tx = db.query(Transaction).filter(Transaction.decision_action == "BLOCK").count()
    total_vol = db.query(func.sum(Transaction.amount)).scalar() or 0.0

    open_cases = db.query(Case).filter(Case.status == "OPEN").count()
    under_review = db.query(Case).filter(Case.status == "UNDER_REVIEW").count()
    resolved_cases = db.query(Case).filter(Case.status == "RESOLVED").count()

    # Risk breakdown count
    high_count = db.query(Transaction).filter(Transaction.risk_level.in_(["HIGH", "CRITICAL"])).count()
    med_count = db.query(Transaction).filter(Transaction.risk_level == "MEDIUM").count()
    low_count = db.query(Transaction).filter(Transaction.risk_level == "LOW").count()

    fraud_rate = round((flagged_tx / total_tx * 100) if total_tx > 0 else 0.0, 2)

    return ApiResponse(
        success=True,
        message="Dashboard metrics calculated",
        data={
            "total_transactions": total_tx,
            "flagged_transactions": flagged_tx,
            "blocked_transactions": blocked_tx,
            "total_volume_bdt": float(total_vol),
            "fraud_rate_pct": fraud_rate,
            "cases": {
                "open": open_cases,
                "under_review": under_review,
                "resolved": resolved_cases,
                "total": open_cases + under_review + resolved_cases
            },
            "risk_distribution": {
                "critical_and_high": high_count,
                "medium": med_count,
                "low": low_count
            },
            "engine_status": {
                "model_version": "v1.2.4-xgboost-prod",
                "rules_active": 9,
                "latency_p95_ms": 32.4,
                "uptime_pct": 99.98
            }
        }
    )


@router.get("/recent-activity", response_model=ApiResponse[list])
def get_recent_activity(db: Session = Depends(get_db)):
    txs = db.query(Transaction).order_by(Transaction.created_at.desc()).limit(15).all()
    results = [
        {
            "transaction_id": t.transaction_id,
            "customer_id": t.customer_id,
            "amount": t.amount,
            "transaction_type": t.transaction_type,
            "channel": t.channel,
            "risk_score": t.risk_score,
            "decision_action": t.decision_action,
            "risk_level": t.risk_level,
            "location": t.location,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in txs
    ]
    return ApiResponse(
        success=True,
        message="Recent activity fetched",
        data=results
    )
