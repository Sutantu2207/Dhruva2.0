"""Dhruva.AI V2 — Security, Cryptography & Token Management.

Implements Argon2id password hashing, strict password validation,
and high-entropy dual-token (access + refresh) issuance and verification.
"""

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from jose import JWTError, jwt
from src.core.config import get_settings
from src.core.errors import AuthenticationError, ValidationError


settings = get_settings()

# Initialize Argon2id hasher with OWASP parameters
_hasher = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash plaintext password using Argon2id."""
    return _hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against an Argon2id hash."""
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def validate_password_strength(password: str) -> None:
    """Validate password against institutional security policies.

    Enforces:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special symbol
    """
    if len(password) < 8:
        raise ValidationError(
            message="Password must be at least 8 characters long",
            code="WEAK_PASSWORD",
            details=[{"field": "password", "issue": "Minimum 8 characters required"}],
        )
    if not re.search(r"[A-Z]", password):
        raise ValidationError(
            message="Password must contain at least one uppercase letter",
            code="WEAK_PASSWORD",
            details=[{"field": "password", "issue": "Must contain uppercase letter"}],
        )
    if not re.search(r"[a-z]", password):
        raise ValidationError(
            message="Password must contain at least one lowercase letter",
            code="WEAK_PASSWORD",
            details=[{"field": "password", "issue": "Must contain lowercase letter"}],
        )
    if not re.search(r"\d", password):
        raise ValidationError(
            message="Password must contain at least one number",
            code="WEAK_PASSWORD",
            details=[{"field": "password", "issue": "Must contain digit"}],
        )
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationError(
            message="Password must contain at least one special character",
            code="WEAK_PASSWORD",
            details=[{"field": "password", "issue": "Must contain special character"}],
        )


def create_access_token(
    subject: str,
    claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate short-lived signed JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": secrets.token_hex(16),
        "type": "access",
    }
    if claims:
        to_encode.update(claims)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type", code="INVALID_TOKEN_TYPE")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Access token has expired", code="TOKEN_EXPIRED")
    except JWTError:
        raise AuthenticationError("Could not validate credentials", code="INVALID_TOKEN")


def generate_refresh_token() -> str:
    """Generate high-entropy cryptographically random refresh token string."""
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    """Generate deterministic SHA-256 hash of a token for secure storage/lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
