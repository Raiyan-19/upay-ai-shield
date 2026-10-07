from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.models.base import get_db
from backend.models.user import User
from backend.models.audit import AuditLog
from backend.schemas.common import ApiResponse
from backend.schemas.auth import UserLogin, UserRegister, UserResponse, TokenResponse, SwitchSessionRequest
from backend.services.auth_service import AuthService, create_access_token, verify_password
from backend.api.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.get("/sessions", response_model=ApiResponse[list])
def list_switchable_sessions(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Retrieve all operational personnel desks available for real-time session switching."""
    users = db.query(User).filter(User.is_active == True).order_by(User.role, User.username).all()
    session_list = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "department": u.department,
            "is_active": u.is_active,
            "is_demo_preset": u.username in ["admin", "tariq", "analyst", "viewer"],
            "last_login": u.last_login.isoformat() if u.last_login else None
        }
        for u in users
    ]
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(session_list)} active officer desks.",
        data=session_list
    )


@router.post("/switch-session", response_model=ApiResponse[TokenResponse])
def switch_active_session(
    req: SwitchSessionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Seamlessly switch active personnel session desk in real-time with statutory audit logging."""
    target_user = db.query(User).filter(User.username == req.target_username).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Officer desk '@{req.target_username}' not found in personnel registry."
        )
    if not target_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Officer account '@{req.target_username}' is suspended. Cannot activate session desk."
        )

    # Clearance verification:
    # 1. Preset demo desks ('admin', 'tariq', 'analyst', 'viewer') allow instant evaluation switching
    # 2. An already-authenticated ADMIN can switch to any desk
    # 3. Otherwise, valid password must be provided
    is_demo = target_user.username in ["admin", "tariq", "analyst", "viewer"]
    is_admin_operator = current_user is not None and current_user.role == "ADMIN"

    if req.password:
        if not verify_password(req.password, target_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password credentials for this officer desk."
            )
    elif not is_demo and not is_admin_operator:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password credentials required to switch to custom officer desks."
        )

    # Update activity timestamp
    target_user.last_login = datetime.now(timezone.utc)
    
    # Statutory immutable audit log entry
    caller_desk = current_user.username if current_user else "unassigned_terminal"
    audit = AuditLog(
        user_id=target_user.id,
        username=caller_desk,
        role=current_user.role if current_user else "VIEWER",
        action="SESSION_SWITCH",
        resource_type="USER_SESSION",
        resource_id=target_user.id,
        details=f"Desk session transferred from @{caller_desk} to @{target_user.username} ({target_user.role})"
    )
    db.add(audit)
    db.commit()
    db.refresh(target_user)

    token = create_access_token(data={"sub": target_user.username, "role": target_user.role, "name": target_user.full_name})
    user_resp = UserResponse.from_orm(target_user)
    token_resp = TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=86400 * 7,
        user=user_resp
    )
    return ApiResponse(
        success=True,
        message=f"Desk session successfully activated for {target_user.full_name} ({target_user.role}).",
        data=token_resp
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, credentials.username_or_email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password. Please verify credentials."
        )

    token = create_access_token(data={"sub": user.username, "role": user.role, "name": user.full_name})
    user_resp = UserResponse.from_orm(user)
    token_resp = TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=86400 * 7,
        user=user_resp
    )
    return ApiResponse(
        success=True,
        message=f"Welcome back, {user.full_name}!",
        data=token_resp
    )


@router.post("/register", response_model=ApiResponse[UserResponse])
def register(req: UserRegister, db: Session = Depends(get_db)):
    existing = AuthService.get_user_by_username_or_email(db, req.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken.")
    existing_email = db.query(User).filter(User.email == req.email).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered.")

    user = AuthService.register_user(
        db,
        username=req.username,
        email=req.email,
        password=req.password,
        full_name=req.full_name,
        role=req.role or "ANALYST",
        department=req.department or "Fraud Investigation Unit"
    )
    return ApiResponse(
        success=True,
        message="User account created successfully.",
        data=UserResponse.from_orm(user)
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
def get_me(current_user: User = Depends(get_current_user)):
    return ApiResponse(
        success=True,
        message="Current session profile retrieved.",
        data=UserResponse.from_orm(current_user)
    )


@router.post("/logout", response_model=ApiResponse[dict])
def logout(current_user: User = Depends(get_current_user)):
    return ApiResponse(
        success=True,
        message="Logged out successfully.",
        data={"user": current_user.username}
    )
