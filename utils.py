import hashlib
import hmac
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.config import settings


# =========================
# PAYSTACK SECURITY
# =========================
def verify_paystack_signature(request_body: bytes, signature: Optional[str]) -> bool:
    """
    Verify Paystack webhook signature using HMAC SHA512
    """
    if not signature:
        return False

    computed_hash = hmac.new(
        settings.PAYSTACK_WEBHOOK_SECRET.encode("utf-8"),
        request_body,
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(computed_hash, signature)


# =========================
# JWT TOKEN FUNCTIONS
# =========================
def create_access_token(data: dict) -> str:
    """
    Generate JWT access token
    """
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def verify_access_token(token: str):
    """
    Decode and validate JWT token
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# =========================
# AUTH DEPENDENCY (Protect routes)
# =========================
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return payload


# =========================
# HELPER FUNCTIONS
# =========================
def generate_reference(prefix: str = "txn") -> str:
    """
    Generate unique transaction reference
    """
    return f"{prefix}_{uuid.uuid4().hex}"


def convert_to_kobo(amount: int) -> int:
    """
    Convert Naira → Kobo
    """
    return amount * 100


def convert_from_kobo(amount: int) -> float:
    """
    Convert Kobo → Naira
    """
    return amount / 100


def hash_string(value: str) -> str:
    """
    SHA256 hash (for safe logging or IDs)
    """
    return hashlib.sha256(value.encode()).hexdigest()


def safe_compare(val1: str, val2: str) -> bool:
    """
    Constant-time comparison (prevents timing attacks)
    """
    return hmac.compare_digest(val1, val2)