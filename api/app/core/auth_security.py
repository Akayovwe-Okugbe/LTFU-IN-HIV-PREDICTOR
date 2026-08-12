"""
=========================================================
MEDISCOPE Authentication Security Helpers

Purpose:
    Provide security helpers used by MEDISCOPE
    authentication workflows that sit outside the core
    password/access-token utilities.

Implemented:
    - numeric email-verification OTP generation;
    - high-entropy URL-safe token generation;
    - secure hashing of already-random secrets;
    - MFA login challenge JWT creation/validation;
    - privileged-role MFA setup JWT creation/validation;
    - TOTP secret generation;
    - authenticator provisioning URI generation;
    - TOTP verification;
    - MFA recovery-code generation.

Security:
    - Plaintext OTPs must never be stored in PostgreSQL.
    - Plaintext password-reset or refresh tokens must never
      be stored in PostgreSQL.
    - Plaintext recovery codes must never be stored after
      their one-time presentation to the user.
    - MFA challenge tokens are not normal access tokens.
    - MFA setup tokens are not normal access tokens.
    - Token type is validated before a workflow token is
      accepted for its intended purpose.

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

import hashlib
import secrets

from datetime import (
    UTC,
    datetime,
    timedelta,
)

from typing import Any
from uuid import UUID


# =====================================================
# THIRD-PARTY IMPORTS
# =====================================================

import jwt
import pyotp


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.core.config import (
    get_settings,
)


# =====================================================
# NUMERIC OTP GENERATION
# =====================================================

def generate_numeric_otp(
    length: int = 6,
) -> str:
    """
    Generate a cryptographically secure numeric OTP.

    Parameters
    ----------
    length:
        Number of digits to generate.

        MEDISCOPE requires at least six digits.

    Returns
    -------
    str
        Numeric one-time password.

    Raises
    ------
    ValueError
        If fewer than six digits are requested.
    """

    if length < 6:
        raise ValueError(
            "OTP length must be at least six digits."
        )

    return "".join(
        secrets.choice(
            "0123456789"
        )
        for _ in range(
            length
        )
    )


# =====================================================
# URL-SAFE TOKEN GENERATION
# =====================================================

def generate_url_safe_token(
    bytes_length: int = 48,
) -> str:
    """
    Generate a high-entropy URL-safe token.

    Suitable for values such as password-reset or refresh
    token plaintext values before hashing/persistence.
    """

    return secrets.token_urlsafe(
        bytes_length
    )


# =====================================================
# RANDOM-SECRET HASHING
# =====================================================

def hash_secret(
    value: str,
) -> str:
    """
    Hash an already-random secret using SHA-256.

    This helper is intended for high-entropy or short-lived
    authentication values such as:

    - OTPs;
    - password-reset tokens;
    - refresh tokens;
    - MFA recovery codes.

    It is deliberately not used for user passwords, which
    are handled separately with Argon2id.
    """

    return hashlib.sha256(
        value.encode(
            "utf-8"
        )
    ).hexdigest()


# =====================================================
# INTERNAL SHORT-LIVED JWT CREATION
# =====================================================

def _create_short_lived_token(
    *,
    subject: UUID | str,
    role: str,
    token_type: str,
) -> str:
    """
    Create a signed short-lived authentication workflow JWT.

    This helper centralises the common claims used by MFA
    workflow tokens so they remain consistent.

    Parameters
    ----------
    subject:
        User UUID.

    role:
        MEDISCOPE account role.

    token_type:
        Explicit workflow-token type.

        Examples:
        - "mfa_challenge"
        - "mfa_setup"

    Returns
    -------
    str
        Signed JWT.
    """

    settings = get_settings()

    issued_at = datetime.now(
        UTC
    )

    payload: dict[
        str,
        Any,
    ] = {
        "sub": str(
            subject
        ),
        "role": role,
        "type": token_type,
        "iat": issued_at,
        "exp": (
            issued_at
            + timedelta(
                minutes=(
                    settings
                    .mfa_challenge_expire_minutes
                )
            )
        ),
        "jti": secrets.token_urlsafe(
            16
        ),
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=(
            settings.jwt_algorithm
        ),
    )


# =====================================================
# INTERNAL SHORT-LIVED JWT VALIDATION
# =====================================================

def _decode_short_lived_token(
    token: str,
    *,
    expected_type: str,
) -> dict[str, Any]:
    """
    Decode and validate one authentication workflow token.

    The token signature, expiry and algorithm are validated
    by PyJWT. MEDISCOPE additionally validates the custom
    workflow-token type.

    Raises
    ------
    jwt.InvalidTokenError
        If the token is invalid, expired, signed with an
        unexpected algorithm, or has the wrong token type.
    """

    settings = get_settings()

    payload: dict[
        str,
        Any,
    ] = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[
            settings.jwt_algorithm
        ],
    )

    if (
        payload.get(
            "type"
        )
        != expected_type
    ):
        raise jwt.InvalidTokenError(
            "Unexpected token type."
        )

    return payload


# =====================================================
# NORMAL MFA LOGIN CHALLENGE
# =====================================================

def create_mfa_challenge_token(
    *,
    subject: UUID | str,
    role: str,
) -> str:
    """
    Create a short-lived MFA login challenge token.

    This token is returned only after successful password
    authentication for an account that already has MFA
    enabled.

    It cannot be used as a normal access token.
    """

    return _create_short_lived_token(
        subject=subject,
        role=role,
        token_type="mfa_challenge",
    )


def decode_mfa_challenge_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode and validate an MFA login challenge token.
    """

    return _decode_short_lived_token(
        token,
        expected_type="mfa_challenge",
    )


# =====================================================
# PRIVILEGED-ROLE MFA SETUP CHALLENGE
# =====================================================

def create_mfa_setup_token(
    *,
    subject: UUID | str,
    role: str,
) -> str:
    """
    Create a short-lived privileged-role MFA setup token.

    This token is used when a clinician or administrator
    successfully enters their password but has not yet
    configured mandatory MFA.

    Important:
        This token must never grant access to normal
        authenticated MEDISCOPE routes.

        It is accepted only by dedicated MFA enrolment
        endpoints.
    """

    return _create_short_lived_token(
        subject=subject,
        role=role,
        token_type="mfa_setup",
    )


def decode_mfa_setup_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode and validate a privileged-role MFA setup token.
    """

    return _decode_short_lived_token(
        token,
        expected_type="mfa_setup",
    )


# =====================================================
# TOTP SECRET GENERATION
# =====================================================

def generate_totp_secret() -> str:
    """
    Generate a new Base32 TOTP secret.

    The secret can be imported into applications such as:

    - Microsoft Authenticator;
    - Google Authenticator;
    - Authy;
    - other RFC-compatible TOTP applications.
    """

    return pyotp.random_base32()


# =====================================================
# TOTP PROVISIONING URI
# =====================================================

def build_totp_provisioning_uri(
    *,
    email: str,
    secret: str,
) -> str:
    """
    Build a QR-code-compatible TOTP provisioning URI.

    The returned otpauth:// URI can be rendered as a QR
    code by the React frontend.

    Parameters
    ----------
    email:
        Account identifier displayed in the authenticator.

    secret:
        Base32 TOTP secret.

    Returns
    -------
    str
        TOTP provisioning URI.
    """

    settings = get_settings()

    return pyotp.TOTP(
        secret
    ).provisioning_uri(
        name=email,
        issuer_name=(
            settings
            .totp_issuer_name
        ),
    )


# =====================================================
# TOTP VERIFICATION
# =====================================================

def verify_totp_code(
    *,
    secret: str,
    code: str,
) -> bool:
    """
    Verify a TOTP authenticator code.

    A one-window tolerance is allowed to accommodate small
    clock differences between the server and authenticator
    device.

    With the standard 30-second TOTP interval, valid_window=1
    permits the immediately previous/current/next interval.
    """

    return pyotp.TOTP(
        secret
    ).verify(
        code,
        valid_window=1,
    )


# =====================================================
# MFA RECOVERY CODES
# =====================================================

def generate_recovery_codes(
    count: int | None = None,
) -> list[str]:
    """
    Generate unique one-time MFA recovery codes.

    Parameters
    ----------
    count:
        Optional number of codes to create.

        When omitted, the configured
        mfa_recovery_code_count value is used.

    Returns
    -------
    list[str]
        Plaintext recovery codes.

    Security:
        These plaintext values should be returned to the
        user only once. Persistence must contain hashes
        rather than the plaintext codes.
    """

    settings = get_settings()

    total = (
        count
        if count is not None
        else (
            settings
            .mfa_recovery_code_count
        )
    )

    return [
        secrets.token_urlsafe(
            10
        )
        for _ in range(
            total
        )
    ]
