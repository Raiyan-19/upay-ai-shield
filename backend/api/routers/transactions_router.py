from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.models.base import get_db
from backend.models.user import User
from backend.schemas.common import ApiResponse, PaginatedData
from backend.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    AnalystFeedbackCreate,
    RiskAssessmentResult
)
from backend.services.transaction_service import TransactionService
from backend.services.risk_service import RiskService
from backend.api.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])


@router.get("")
def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    risk_level: Optional[str] = Query(None),
    decision_action: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_dir: Optional[str] = Query("desc"),
    db: Session = Depends(get_db)
):
    items, total = TransactionService.list_transactions(
        db=db,
        page=page,
        limit=limit,
        risk_level=risk_level,
        decision_action=decision_action,
        transaction_type=transaction_type,
        channel=channel,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
        sort_by=sort_by or "created_at",
        sort_dir=sort_dir or "desc"
    )

    items_data = []
    for t in items:
        score = t.demo_risk_score if t.demo_risk_score is not None else 10.0
        if score >= 80:
            act = "BLOCK" if score >= 90 else "REVIEW"
        elif score >= 50:
            act = "REVIEW"
        else:
            act = "APPROVE"

        items_data.append({
            "transaction_id": t.transaction_id,
            "customer_id": t.customer_id,
            "amount": t.amount,
            "transaction_type": t.transaction_type,
            "channel": t.channel,
            "device_id": t.device_id,
            "ip_address": "103.114.98.12",
            "location": t.location,
            "receiver_id": t.receiver_id,
            "recipient_account": t.receiver_id,
            "is_new_receiver": bool(t.is_new_receiver),
            "is_new_recipient": bool(t.is_new_receiver),
            "is_night_transaction": bool(t.hour < 5 if t.hour is not None else False),
            "failed_attempts": t.failed_attempts or 0,
            "failed_pin_attempts_last_hour": t.failed_attempts or 0,
            "device_changed_recently": bool(t.is_new_device),
            "is_new_device": bool(t.is_new_device),
            "sim_changed_recently": False,
            "velocity_1h_count": t.transactions_last_1h or 1,
            "transactions_last_1h": t.transactions_last_1h or 1,
            "velocity_24h_count": t.transactions_last_24h or 4,
            "transactions_last_24h": t.transactions_last_24h or 4,
            "amount_deviation": t.amount_deviation or 1.0,
            "amount_deviation_score": t.amount_deviation or 1.0,
            "risk_score": score,
            "decision_action": act,
            "risk_level": t.risk_level or "LOW",
            "timestamp": t.timestamp or (t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else None),
            "created_at": t.created_at.isoformat() if t.created_at else None
        })

    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return JSONResponse(
        content={
            "success": True,
            "message": f"Retrieved {len(items_data)} transactions",
            "page": page,
            "limit": limit,
            "total": total,
            "total_count": total,
            "total_pages": total_pages,
            "items": items_data,
            "data": {
                "items": items_data,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            }
        }
    )


@router.post("/simulate", response_model=ApiResponse[dict])
def simulate_transaction_risk(
    req: TransactionCreate,
    db: Session = Depends(get_db)
):
    assessment = RiskService.assess_transaction_data(db, req.dict())
    return ApiResponse(
        success=True,
        message="Risk simulation executed successfully",
        data=assessment
    )


@router.get("/{transaction_id}")
def get_transaction_details(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    data = TransactionService.get_transaction_by_id(db, transaction_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' was not found in audit logs."
        )
    return JSONResponse(
        content={
            "success": True,
            "message": "Transaction details and risk assessment loaded",
            "data": data,
            **data
        }
    )


@router.post("/{transaction_id}/feedback", response_model=ApiResponse[dict])
def submit_analyst_feedback(
    transaction_id: str,
    feedback: AnalystFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    analyst_name = current_user.username if current_user else "tariq.hassan"
    fb = TransactionService.record_feedback(
        db=db,
        transaction_id=transaction_id,
        decision=feedback.decision,
        comment=feedback.comment or "",
        analyst_id=analyst_name
    )
    return ApiResponse(
        success=True,
        message="Analyst feedback recorded successfully.",
        data={
            "id": fb.id,
            "transaction_id": fb.transaction_id,
            "decision": fb.decision,
            "comment": fb.comment,
            "analyst_id": fb.analyst_id
        }
    )
