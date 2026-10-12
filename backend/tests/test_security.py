"""Dhruva.AI V2 — Unit Tests: Security, Cryptography & Token Operations.

Tests:
- Argon2id password hashing and constant-time verification
- Password complexity validation rules (length, upper, lower, digits, special characters)
- JWT access token issuance, claims encoding, expiration handling, and tampering detection
- Cryptographically secure refresh token generation and SHA-256 hashing
"""

import time
import uuid
import pytest
from datetime import timedelta
from src.core.errors import AuthenticationError, ValidationError
from src.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    validate_password_strength,
    verify_password,
)


class TestPasswordSecurity:
    """Argon2id password hashing and validation tests."""

    def test_argon2id_hash_and_verify(self):
        password = "ComplexPassword123!@#"
        pwd_hash = hash_password(password)

        assert pwd_hash is not None
        assert pwd_hash.startswith("$argon2id$")
        assert verify_password(password, pwd_hash) is True
        assert verify_password("WrongPassword123!", pwd_hash) is False

    def test_password_strength_valid(self):
        # Should not raise exception
        validate_password_strength("ValidPass123$")
        validate_password_strength("Dhruva#Secure2026")

    def test_password_strength_too_short(self):
        with pytest.raises(ValidationError) as exc:
            validate_password_strength("Ab1!xyz")
        assert exc.value.code == "WEAK_PASSWORD"
        assert "8 characters" in str(exc.value.message)

    def test_password_strength_missing_uppercase(self):
        with pytest.raises(ValidationError) as exc:
            validate_password_strength("weakpass123$")
        assert exc.value.code == "WEAK_PASSWORD"
        assert "uppercase" in str(exc.value.message)

    def test_password_strength_missing_lowercase(self):
        with pytest.raises(ValidationError) as exc:
            validate_password_strength("WEAKPASS123$")
        assert exc.value.code == "WEAK_PASSWORD"
        assert "lowercase" in str(exc.value.message)

    def test_password_strength_missing_digit(self):
        with pytest.raises(ValidationError) as exc:
            validate_password_strength("WeakPassWord$")
        assert exc.value.code == "WEAK_PASSWORD"
        assert "number" in str(exc.value.message)

    def test_password_strength_missing_special(self):
        with pytest.raises(ValidationError) as exc:
            validate_password_strength("WeakPass1234")
        assert exc.value.code == "WEAK_PASSWORD"
        assert "special" in str(exc.value.message)


class TestTokenOperations:
    """JWT and refresh token issuance, decoding, and validation tests."""

    def test_create_and_decode_access_token(self):
        user_id = str(uuid.uuid4())
        claims = {"tenant_id": str(uuid.uuid4()), "role": "STUDENT"}

        token = create_access_token(subject=user_id, claims=claims)
        assert token is not None

        decoded = decode_access_token(token)
        assert decoded["sub"] == user_id
        assert decoded["tenant_id"] == claims["tenant_id"]
        assert decoded["role"] == "STUDENT"
        assert decoded["type"] == "access"
        assert "exp" in decoded
        assert "iat" in decoded
        assert "jti" in decoded

    def test_expired_token_rejected(self):
        user_id = str(uuid.uuid4())
        # Create token that already expired 1 second ago
        token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-10))

        with pytest.raises(AuthenticationError) as exc:
            decode_access_token(token)
        assert exc.value.code == "TOKEN_EXPIRED"

    def test_tampered_token_rejected(self):
        user_id = str(uuid.uuid4())
        token = create_access_token(subject=user_id)
        # Tamper payload
        tampered_token = token[:-5] + "aaaaa"

        with pytest.raises(AuthenticationError) as exc:
            decode_access_token(tampered_token)
        assert exc.value.code == "INVALID_TOKEN"

    def test_refresh_token_generation_and_hashing(self):
        raw_token = generate_refresh_token()
        assert len(raw_token) >= 64

        hashed = hash_token(raw_token)
        assert len(hashed) == 64  # SHA-256 hex string is 64 characters

        # Deterministic hash check
        hashed_again = hash_token(raw_token)
        assert hashed == hashed_again

        # Different token produces different hash
        raw_token_2 = generate_refresh_token()
        assert hash_token(raw_token_2) != hashed
