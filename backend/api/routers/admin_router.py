from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.models.base import get_db
from backend.models.user import User, UserRole
from backend.schemas.common import ApiResponse, PaginatedData
from backend.services.admin_service import AdminService
from backend.api.deps import get_current_user, require_role

router = APIRouter(prefix="/api/v1/admin", tags=["Administration"])


@router.get("/metrics", response_model=ApiResponse[dict])
def get_admin_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    metrics = AdminService.get_system_metrics(db)
    return ApiResponse(
        success=True,
        message="Admin metrics loaded",
        data=metrics
    )


@router.get("/users", response_model=ApiResponse[list])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    users = AdminService.list_users(db)
    return ApiResponse(
        success=True,
        message=f"Loaded {len(users)} system users",
        data=users
    )


@router.post("/users", response_model=ApiResponse[dict])
def create_user(
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    try:
        new_user = AdminService.create_user(db, user_data, current_user.username)
        return ApiResponse(
            success=True,
            message=f"Personnel account '@{new_user.username}' provisioned successfully with {new_user.role} clearance.",
            data={
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "role": new_user.role,
                "department": new_user.department,
                "is_active": new_user.is_active,
                "created_at": new_user.created_at.isoformat() if new_user.created_at else None
            }
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.patch("/users/{user_id}/status", response_model=ApiResponse[dict])
def toggle_user_status(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    try:
        user = AdminService.toggle_user_status(db, user_id, current_user.username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        return ApiResponse(
            success=True,
            message=f"Officer @{user.username} status toggled to {'Active' if user.is_active else 'Suspended'}.",
            data={"id": user.id, "username": user.username, "is_active": user.is_active}
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status update failed: {str(e)}")


@router.get("/audit-logs", response_model=ApiResponse[PaginatedData[dict]])
def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "SENIOR_OFFICER", "VIEWER"]))
):
    items, total = AdminService.list_audit_logs(db, limit=limit, page=page)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    paginated = PaginatedData(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(items)} audit logs",
        data=paginated
    )

