"""
=========================================================
MEDISCOPE Security Utilities

Purpose:
    Provide password hashing, password verification,
    access-token creation and access-token validation.

Security:
    - Passwords are hashed using Argon2id.
    - Access tokens are short-lived JWTs.
    - MFA completion status is stored as a token claim.
    - Sensitive values such as passwords, OTPs, refresh
      tokens and TOTP secrets must never be included in
      JWT payloads.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

from datetime import (
    UTC,
    datetime,
    timedelta,
)

from typing import Any
from uuid import UUID

import secrets


# =====================================================
# THIRD-PARTY IMPORTS
# =====================================================

import jwt

from argon2 import PasswordHasher

from argon2.exceptions import (
    InvalidHashError,
    VerifyMismatchError,
)


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from .config import get_settings


# =====================================================
# PASSWORD HASHER
# =====================================================

_hasher = PasswordHasher()


# =====================================================
# PASSWORD HASHING
# =====================================================

def hash_password(
    password: str,
) -> str:
    """
    Hash a plaintext password using Argon2id.

    Parameters
    ----------
    password:
        Plaintext password supplied by the user.

    Returns
    -------
    str
        Argon2id password hash.

    Raises
    ------
    ValueError
        If the password is shorter than the configured
        minimum password length.
    """

    settings = get_settings()

    if (
        len(password)
        < settings.password_min_length
    ):

        raise ValueError(
            "Password must contain at least "
            f"{settings.password_min_length} "
            "characters."
        )

    return _hasher.hash(
        password
    )


# =====================================================
# PASSWORD VERIFICATION
# =====================================================

def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.

    Returns False rather than exposing detailed password
    verification errors.
    """

    try:

        return _hasher.verify(
            password_hash,
            password,
        )

    except (
        VerifyMismatchError,
        InvalidHashError,
    ):

        return False


# =====================================================
# ACCESS-TOKEN CREATION
# =====================================================

def create_access_token(
    *,
    subject: UUID | str,
    role: str,
    mfa_verified: bool = False,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed, short-lived JWT access token.

    Parameters
    ----------
    subject:
        Unique identifier of the authenticated user.

    role:
        MEDISCOPE role assigned to the account.

    mfa_verified:
        Indicates whether the required second
        authentication factor has been completed.

        The default is False so older code cannot
        accidentally create a token that appears to have
        passed MFA.

    expires_delta:
        Optional custom token lifetime.

    additional_claims:
        Optional non-sensitive JWT claims.

    Returns
    -------
    str
        Encoded JWT access token.
    """

    settings = get_settings()

    issued_at = datetime.now(
        UTC
    )

    expires_at = issued_at + (
        expires_delta
        if expires_delta is not None
        else timedelta(
            minutes=(
                settings
                .access_token_expire_minutes
            )
        )
    )

    # -------------------------------------------------
    # Core access-token claims.
    # -------------------------------------------------

    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "mfa_verified": mfa_verified,
        "iat": issued_at,
        "exp": expires_at,
        "jti": secrets.token_urlsafe(16),
    }

    # -------------------------------------------------
    # Prevent additional claims from replacing
    # security-critical token fields.
    # -------------------------------------------------

    if additional_claims:

        protected_claims = {
            "sub",
            "role",
            "type",
            "mfa_verified",
            "iat",
            "exp",
            "jti",
        }

        safe_additional_claims = {
            key: value
            for key, value
            in additional_claims.items()
            if key not in protected_claims
        }

        payload.update(
            safe_additional_claims
        )

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


# =====================================================
# ACCESS-TOKEN VALIDATION
# =====================================================

def decode_access_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode and validate a MEDISCOPE access token.

    Parameters
    ----------
    token:
        Encoded JWT access token.

    Returns
    -------
    dict[str, Any]
        Validated JWT claims.

    Raises
    ------
    jwt.InvalidTokenError
        If the token is invalid, expired or has an
        unexpected token type.
    """

    settings = get_settings()

    payload: dict[str, Any] = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[
            settings.jwt_algorithm
        ],
    )

    if (
        payload.get("type")
        != "access"
    ):

        raise jwt.InvalidTokenError(
            "Unexpected token type."
        )

    return payload
