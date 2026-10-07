from typing import Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.models.base import get_db
from backend.models.user import User
from backend.models.case import Case, CaseEvent
from backend.schemas.common import ApiResponse, PaginatedData
from backend.schemas.case import CaseResponse, CaseUpdate, CaseDecision
from backend.services.case_service import CaseService
from backend.api.deps import get_current_user_optional, get_current_user

router = APIRouter(prefix="/api/v1/cases", tags=["Cases"])


@router.get("")
def list_cases(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    assigned_analyst: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_preset: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_dir: Optional[str] = Query("desc"),
    db: Session = Depends(get_db)
):
    items, total = CaseService.list_cases(
        db=db,
        page=page,
        limit=limit,
        status=status_filter,
        priority=priority,
        assigned_analyst=assigned_analyst,
        search=search,
        date_preset=date_preset,
        specific_date=date,
        sort_by=sort_by or "created_at",
        sort_dir=sort_dir or "desc"
    )

    items_data = []
    for c in items:
        tx = c.transaction
        items_data.append({
            "case_id": c.case_id,
            "transaction_id": c.transaction_id,
            "customer_id": c.customer_id,
            "status": c.status,
            "priority": c.priority,
            "assigned_analyst": c.assigned_analyst,
            "analyst_notes": c.analyst_notes,
            "risk_score": c.risk_score,
            "risk_level": c.risk_level,
            "decision": c.decision,
            "amount": tx.amount if tx else None,
            "transaction_type": tx.transaction_type if tx else "SEND_MONEY",
            "channel": tx.channel if tx else "APP",
            "location": tx.location if tx else "Dhaka",
            "device_id": tx.device_id if tx else None,
            "receiver_id": tx.receiver_id if tx else None,
            "amount_deviation": tx.amount_deviation if tx else 1.0,
            "is_fraud": tx.is_fraud if tx else 0,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        })

    total_pages = (total + limit - 1) // limit if total > 0 else 1

    # Statutory Case KPIs computed dynamically from database
    all_count = db.query(Case).count()
    open_count = db.query(Case).filter(Case.status == "OPEN").count()
    review_count = db.query(Case).filter(Case.status == "UNDER_REVIEW").count()
    needs_info_count = db.query(Case).filter(Case.status == "NEEDS_MORE_INFORMATION").count()
    resolved_count = db.query(Case).filter(Case.status == "RESOLVED").count()
    res_rate = round((resolved_count / all_count * 100) if all_count else 0.0, 1)

    kpis_dict = {
        "total_cases": all_count,
        "open": open_count,
        "under_review": review_count,
        "needs_more_info": needs_info_count,
        "resolved": resolved_count,
        "resolution_rate_pct": res_rate
    }

    return JSONResponse(
        content={
            "success": True,
            "message": f"Retrieved {len(items_data)} investigation cases",
            "page": page,
            "limit": limit,
            "total": total,
            "total_count": total,
            "total_pages": total_pages,
            "kpis": kpis_dict,
            "items": items_data,
            "data": {
                "items": items_data,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "kpis": kpis_dict
            }
        }
    )


@router.get("/timeline")
def get_cases_timeline(db: Session = Depends(get_db)):
    from sqlalchemy import func
    from backend.models.transaction import Transaction

    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    # 1. Dynamic Daily Breakdown (past 14 active days)
    daily = []
    for d in range(14):
        start = today_start - timedelta(days=d)
        end = start + timedelta(days=1)
        count = db.query(Case).filter(Case.created_at >= start, Case.created_at < end).count()
        if count == 0 and d > 7:
            continue
        resolved = db.query(Case).filter(Case.created_at >= start, Case.created_at < end, Case.status == "RESOLVED").count()
        under_review = db.query(Case).filter(Case.created_at >= start, Case.created_at < end, Case.status == "UNDER_REVIEW").count()
        open_cases = db.query(Case).filter(Case.created_at >= start, Case.created_at < end, Case.status == "OPEN").count()
        needs_info = db.query(Case).filter(Case.created_at >= start, Case.created_at < end, Case.status == "NEEDS_MORE_INFORMATION").count()
        avg_score = db.query(func.avg(Case.risk_score)).filter(Case.created_at >= start, Case.created_at < end).scalar() or 0.0

        daily.append({
            "date": start.strftime("%Y-%m-%d"),
            "date_bengali": start.strftime("%d %b, %Y"),
            "total_cases": count,
            "resolved_cases": resolved,
            "under_review_cases": under_review,
            "open_cases": open_cases,
            "needs_info_cases": needs_info,
            "resolution_rate_pct": round((resolved / count * 100), 1) if count else 0.0,
            "avg_risk_score": round(float(avg_score), 1)
        })

    # 2. Dynamic Weekly Breakdown (past 6 weeks)
    weekly = []
    for w in range(6):
        start = today_start - timedelta(days=(w + 1) * 7)
        end = today_start - timedelta(days=w * 7)
        count = db.query(Case).filter(Case.created_at >= start, Case.created_at < end).count()
        resolved = db.query(Case).filter(Case.created_at >= start, Case.created_at < end, Case.status == "RESOLVED").count()

        vol_protected = db.query(func.sum(Transaction.amount)).join(
            Case, Case.transaction_id == Transaction.transaction_id
        ).filter(
            Case.created_at >= start, Case.created_at < end, Case.status == "RESOLVED"
        ).scalar() or 0.0

        label = f"Week {start.strftime('%U')} (Current)" if w == 0 else f"Week {start.strftime('%U')} ({start.strftime('%d %b')} – {end.strftime('%d %b')})"
        velocity = f"{round(resolved / 7, 1)} cases/day"

        weekly.append({
            "week": label,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "cases": count,
            "resolved": resolved,
            "velocity": velocity,
            "volume_protected_bdt": round(float(vol_protected), 2)
        })

    # 3. Dynamic Monthly Breakdown (past 3 calendar months)
    monthly = []
    curr_month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    for m in range(3):
        year = curr_month_start.year
        month = curr_month_start.month - m
        while month < 1:
            month += 12
            year -= 1
        m_start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            m_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            m_end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        count = db.query(Case).filter(Case.created_at >= m_start, Case.created_at < m_end).count()
        resolved = db.query(Case).filter(Case.created_at >= m_start, Case.created_at < m_end, Case.status == "RESOLVED").count()
        vol_protected = db.query(func.sum(Transaction.amount)).join(
            Case, Case.transaction_id == Transaction.transaction_id
        ).filter(
            Case.created_at >= m_start, Case.created_at < m_end, Case.status == "RESOLVED"
        ).scalar() or 0.0

        monthly.append({
            "month": m_start.strftime("%B %Y"),
            "cases": count,
            "resolved": resolved,
            "resolution_rate_pct": round(resolved / count * 100, 1) if count else 0.0,
            "volume_protected_bdt": round(float(vol_protected), 2)
        })

    return JSONResponse(
        content={
            "success": True,
            "message": "Case timeline retrieved",
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
            "data": {
                "daily": daily,
                "weekly": weekly,
                "monthly": monthly
            }
        }
    )


@router.get("/{case_id}")
def get_case_details(
    case_id: str,
    db: Session = Depends(get_db)
):
    case_data = CaseService.get_case_by_id(db, case_id)
    if not case_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation Case '{case_id}' was not found."
        )
    return JSONResponse(
        content={
            "success": True,
            "message": "Case details and timeline loaded",
            "data": case_data,
            **case_data
        }
    )



@router.patch("/{case_id}", response_model=ApiResponse[dict])
def update_case(
    case_id: str,
    updates: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    analyst_name = current_user.username if current_user else "Tariq Hassan"
    updated_case = CaseService.update_case(
        db=db,
        case_id=case_id,
        analyst_user=analyst_name,
        status=updates.status,
        priority=updates.priority,
        assigned_analyst=updates.assigned_analyst,
        notes=updates.analyst_notes
    )
    if not updated_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found.")

    return ApiResponse(
        success=True,
        message="Case updated successfully.",
        data={
            "case_id": updated_case.case_id,
            "status": updated_case.status,
            "priority": updated_case.priority,
            "assigned_analyst": updated_case.assigned_analyst,
            "updated_at": updated_case.updated_at.isoformat() if updated_case.updated_at else None
        }
    )


@router.post("/{case_id}/decision", response_model=ApiResponse[dict])
def record_case_decision(
    case_id: str,
    decision_req: CaseDecision,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    analyst_name = current_user.username if current_user else "Tariq Hassan"
    resolved_case = CaseService.record_decision(
        db=db,
        case_id=case_id,
        decision=decision_req.decision,
        notes=decision_req.notes or "",
        analyst_user=analyst_name
    )
    if not resolved_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found.")

    return ApiResponse(
        success=True,
        message=f"Case resolved with decision '{decision_req.decision}'.",
        data={
            "case_id": resolved_case.case_id,
            "decision": resolved_case.decision,
            "status": resolved_case.status
        }
    )
