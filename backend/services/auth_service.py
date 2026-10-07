import os
import hmac
import hashlib
import json
import base64
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from backend.models.user import User, UserRole
from backend.models.audit import AuditLog

SECRET_KEY = os.environ.get("UPAY_AUTH_SECRET", "upay-ai-shield-secret-production-key-2026-bangladesh")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 86400 * 7  # 7 days


def hash_password(password: str) -> str:
    """Secure PBKDF2-HMAC-SHA256 password hash with 100,000 iterations and salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return base64.b64encode(salt + key).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored salt + key."""
    try:
        decoded = base64.b64decode(hashed_password.encode("ascii"))
        salt = decoded[:16]
        stored_key = decoded[16:]
        new_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(stored_key, new_key)
    except Exception:
        return False


def _b64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64_url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("ascii"))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed HMAC-SHA256 JWT."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()
    now = int(time.time())
    exp = now + (int(expires_delta.total_seconds()) if expires_delta else ACCESS_TOKEN_EXPIRE_SECONDS)
    payload.update({"iat": now, "exp": exp})

    h_enc = _b64_url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_enc = _b64_url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{h_enc}.{p_enc}".encode("ascii")

    sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_enc = _b64_url_encode(sig)
    return f"{h_enc}.{p_enc}.{sig_enc}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and verifies signed HMAC-SHA256 JWT."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h_enc, p_enc, sig_enc = parts
        signing_input = f"{h_enc}.{p_enc}".encode("ascii")
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _b64_url_decode(sig_enc)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_bytes = _b64_url_decode(p_enc)
        payload = json.loads(payload_bytes.decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


class AuthService:
    @staticmethod
    def get_user_by_username_or_email(db: Session, identifier: str) -> Optional[User]:
        return db.query(User).filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

    @staticmethod
    def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
        user = AuthService.get_user_by_username_or_email(db, username_or_email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def register_user(db: Session, username: str, email: str, password: str, full_name: str, role: str = "ANALYST", department: str = "Fraud Investigation Unit") -> User:
        user_id = f"USR-{int(time.time()*1000)}"
        user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role if role in UserRole.ALL else UserRole.ANALYST,
            department=department,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        audit = AuditLog(
            user_id=user.id,
            username=user.username,
            role=user.role,
            action="USER_REGISTER",
            resource_type="user",
            resource_id=user.id,
            details=f"User registered with role {user.role}"
        )
        db.add(audit)
        db.commit()
        return user

    @staticmethod
    def seed_initial_users(db: Session):
        """Seed initial production roles if not exists."""
        initial_users = [
            ("admin", "admin@upay.com.bd", "Admin@1234", "System Administrator", UserRole.ADMIN, "Fraud Operations Management"),
            ("tariq", "tariq.hassan@upay.com.bd", "Analyst@1234", "Tariq Hassan", UserRole.SENIOR_OFFICER, "Fraud Investigation Unit"),
            ("analyst", "analyst@upay.com.bd", "Analyst@1234", "Rafiqul Islam", UserRole.ANALYST, "Fraud Operations Tier 1"),
            ("viewer", "auditor@upay.com.bd", "Viewer@1234", "Farhana Sultana", UserRole.VIEWER, "Compliance & Audit"),
            ("customer", "customer@upay.com.bd", "Customer@1234", "Kamal Hossain (Customer)", UserRole.CUSTOMER, "MFS Retail Accounts (01719283746)")
        ]
        for uname, email, pwd, fname, role, dept in initial_users:
            existing = db.query(User).filter((User.username == uname) | (User.email == email)).first()
            if not existing:
                u = User(
                    id=f"USR-{uname}",
                    username=uname,
                    email=email,
                    password_hash=hash_password(pwd),
                    full_name=fname,
                    role=role,
                    department=dept,
                    is_active=True
                )
                db.add(u)
        db.commit()
