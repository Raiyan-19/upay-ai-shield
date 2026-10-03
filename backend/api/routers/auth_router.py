from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.models.base import get_db
from backend.models.user import User
from backend.schemas.common import ApiResponse
from backend.schemas.auth import UserLogin, UserRegister, UserResponse, TokenResponse
from backend.services.auth_service import AuthService, create_access_token
from backend.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


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
