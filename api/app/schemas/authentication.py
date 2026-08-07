"""
=========================================================
Phase 2 Authentication Schemas

MEDISCOPE
LTFU Prediction Platform

Purpose:
    Defines the Pydantic request and response models used
    by the Phase 2 authentication endpoints.

Implemented workflows:
    - email OTP verification;
    - verification OTP resend;
    - forgotten-password requests;
    - password-reset confirmation;
    - refresh-token rotation;
    - logout;
    - TOTP authenticator enrolment;
    - TOTP login verification;
    - MFA recovery-code verification;
    - MFA removal.

Security:
    These schemas validate incoming authentication data
    before it reaches the service layer.

    Sensitive values such as passwords, OTPs, refresh
    tokens and MFA recovery codes must never be written
    to application logs.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# PYDANTIC IMPORTS
# =====================================================

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)


# =====================================================
# GENERIC SECURITY RESPONSE
# =====================================================

class SecurityMessageResponse(BaseModel):
    """
    Returns a generic security-safe response message.

    Generic responses are particularly useful for email
    verification and password-reset requests because they
    help prevent account-enumeration attacks.
    """

    message: str


# =====================================================
# AUTHENTICATION TOKEN RESPONSE
# =====================================================

class AuthenticationTokensResponse(BaseModel):
    """
    Returns the access and refresh tokens issued after
    successful authentication.

    The access token is short-lived.

    The refresh token is longer-lived and is rotated each
    time it is used.
    """

    access_token: str

    refresh_token: str

    token_type: str = "bearer"


# =====================================================
# MFA CHALLENGE RESPONSE
# =====================================================

class MfaRequiredResponse(BaseModel):
    """
    Returned after successful password verification when
    the user's account has MFA enabled.

    The MFA challenge token is short-lived and cannot be
    used as a normal access token.
    """

    mfa_required: bool = True

    mfa_challenge_token: str

    message: str


# =====================================================
# EMAIL VERIFICATION REQUEST
# =====================================================

class EmailVerificationRequest(BaseModel):
    """
    Verifies a user account using a six-digit email OTP.
    """

    email: EmailStr

    otp: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )

    @field_validator(
        "email"
    )
    @classmethod
    def normalise_email(
        cls,
        value: EmailStr,
    ) -> str:
        """
        Convert the email address to a consistent format.

        Email addresses are stripped of surrounding spaces
        and stored in lowercase.
        """

        return str(
            value
        ).strip().lower()


# =====================================================
# RESEND EMAIL VERIFICATION REQUEST
# =====================================================

class ResendEmailVerificationRequest(BaseModel):
    """
    Requests a replacement email-verification OTP.
    """

    email: EmailStr

    @field_validator(
        "email"
    )
    @classmethod
    def normalise_email(
        cls,
        value: EmailStr,
    ) -> str:
        """
        Normalise the supplied email address.
        """

        return str(
            value
        ).strip().lower()


# =====================================================
# PASSWORD-RESET REQUEST
# =====================================================

class PasswordResetRequest(BaseModel):
    """
    Requests password-reset instructions.

    The API returns the same response regardless of whether
    the supplied email exists.
    """

    email: EmailStr

    @field_validator(
        "email"
    )
    @classmethod
    def normalise_email(
        cls,
        value: EmailStr,
    ) -> str:
        """
        Normalise the supplied email address.
        """

        return str(
            value
        ).strip().lower()


# =====================================================
# PASSWORD-RESET CONFIRMATION
# =====================================================

class PasswordResetConfirmRequest(BaseModel):
    """
    Confirms a password reset using a single-use token.
    """

    token: str = Field(
        min_length=20,
        max_length=500,
    )

    new_password: str = Field(
        min_length=12,
        max_length=200,
    )


# =====================================================
# REFRESH TOKEN REQUEST
# =====================================================

class RefreshTokenRequest(BaseModel):
    """
    Exchanges a valid refresh token for a newly rotated
    access-token and refresh-token pair.
    """

    refresh_token: str = Field(
        min_length=20,
        max_length=1000,
    )


# =====================================================
# LOGOUT REQUEST
# =====================================================

class LogoutRequest(BaseModel):
    """
    Revokes one refresh-token session.
    """

    refresh_token: str = Field(
        min_length=20,
        max_length=1000,
    )


# =====================================================
# START TOTP ENROLMENT RESPONSE
# =====================================================

class TotpEnrollmentStartResponse(BaseModel):
    """
    Returns the information needed to configure an
    authenticator application.

    The provisioning URI can be converted into a QR code.

    The manual secret allows the user to configure the
    authenticator application without scanning a QR code.

    Important:
        The manual secret should only be displayed during
        the enrolment process and must not be logged.
    """

    provisioning_uri: str

    manual_secret: str

    message: str


# =====================================================
# CONFIRM TOTP ENROLMENT REQUEST
# =====================================================

class TotpEnrollmentConfirmRequest(BaseModel):
    """
    Confirms TOTP enrolment using the six-digit code
    generated by the authenticator application.
    """

    code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


# =====================================================
# CONFIRM TOTP ENROLMENT RESPONSE
# =====================================================

class TotpEnrollmentConfirmResponse(BaseModel):
    """
    Returns one-time recovery codes after MFA enrolment.

    Recovery codes are displayed only once. Only their
    cryptographic hashes should be stored in PostgreSQL.
    """

    message: str

    recovery_codes: list[str]


# =====================================================
# TOTP LOGIN VERIFICATION REQUEST
# =====================================================

class TotpLoginVerifyRequest(BaseModel):
    """
    Completes MFA login using either:

    - a six-digit authenticator code; or
    - a one-time recovery code.
    """

    mfa_challenge_token: str = Field(
        min_length=20,
        max_length=2000,
    )

    code: str = Field(
        min_length=6,
        max_length=100,
    )


# =====================================================
# DISABLE TOTP MFA REQUEST
# =====================================================

class TotpDisableRequest(BaseModel):
    """
    Disables MFA after verifying both:

    - the user's current password; and
    - a valid authenticator or recovery code.
    """

    password: str = Field(
        min_length=1,
        max_length=200,
    )

    code: str = Field(
        min_length=6,
        max_length=100,
    )
