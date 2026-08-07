"""MEDISCOPE Phase 2 security helpers.

Generates and hashes OTPs and refresh tokens, creates short-lived MFA challenge
JWTs, and supports TOTP authenticator applications. Plaintext OTPs, refresh
tokens, and recovery codes must never be stored in PostgreSQL.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
import pyotp

from app.core.config import get_settings


def generate_numeric_otp(length: int = 6) -> str:
    """Return a cryptographically secure numeric OTP."""
    if length < 6:
        raise ValueError("OTP length must be at least six digits.")
    return "".join(secrets.choice("0123456789") for _ in range(length))


def generate_url_safe_token(bytes_length: int = 48) -> str:
    """Return a high-entropy URL-safe token."""
    return secrets.token_urlsafe(bytes_length)


def hash_secret(value: str) -> str:
    """Hash an already-random token, OTP, or recovery code."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def create_mfa_challenge_token(*, subject: UUID | str, role: str) -> str:
    """Create a short-lived JWT that can only complete MFA."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "mfa_challenge",
        "iat": now,
        "exp": now + timedelta(minutes=settings.mfa_challenge_expire_minutes),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_mfa_challenge_token(token: str) -> dict[str, Any]:
    """Decode and validate an MFA challenge JWT."""
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "mfa_challenge":
        raise jwt.InvalidTokenError("Unexpected token type.")
    return payload


def generate_totp_secret() -> str:
    """Generate a Base32 secret for an authenticator application."""
    return pyotp.random_base32()


def build_totp_provisioning_uri(*, email: str, secret: str) -> str:
    """Build a QR-code-compatible TOTP provisioning URI."""
    settings = get_settings()
    return pyotp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=settings.totp_issuer_name,
    )


def verify_totp_code(*, secret: str, code: str) -> bool:
    """Verify a TOTP code with one 30-second tolerance window."""
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def generate_recovery_codes(count: int | None = None) -> list[str]:
    """Generate unique one-time MFA recovery codes."""
    settings = get_settings()
    total = count if count is not None else settings.mfa_recovery_code_count
    return [secrets.token_urlsafe(10) for _ in range(total)]
