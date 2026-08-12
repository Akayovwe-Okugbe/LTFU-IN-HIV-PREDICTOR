"""
=========================================================
MEDISCOPE Authentication Schemas

Purpose:
    Define the Pydantic request and response models used
    by MEDISCOPE authentication and account-security
    workflows.

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
    - MFA removal;
    - mandatory MFA enrolment for privileged roles.

Security:
    These schemas validate incoming authentication data
    before it reaches the authentication service or route
    logic.

    Sensitive values such as passwords, OTPs, refresh
    tokens, MFA setup tokens, MFA challenge tokens and
    recovery codes must never be written to application
    logs.

    MFA challenge and MFA setup tokens are workflow tokens
    only. They must never be treated as normal access
    tokens.

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
    Return a generic security-safe response message.

    Generic responses are useful for workflows such as
    password reset and verification-code resend because
    they help prevent account-enumeration attacks.
    """

    message: str


# =====================================================
# AUTHENTICATION TOKEN RESPONSE
# =====================================================

class AuthenticationTokensResponse(BaseModel):
    """
    Return the normal authentication credentials issued
    after successful authentication.

    access_token:
        Short-lived JWT used to access protected API
        endpoints.

    refresh_token:
        Longer-lived opaque token backed by a database
        session and rotated whenever it is used.

    token_type:
        Standard Bearer authentication token type.
    """

    access_token: str

    refresh_token: str

    token_type: str = "bearer"


# =====================================================
# MFA LOGIN CHALLENGE RESPONSE
# =====================================================

class MfaRequiredResponse(BaseModel):
    """
    Returned after successful password verification when
    the account already has MFA enabled.

    No normal access or refresh tokens are returned at
    this stage.

    The MFA challenge token is short-lived and can only be
    used to complete the second-factor login workflow.
    """

    mfa_required: bool = True

    mfa_challenge_token: str

    message: str


# =====================================================
# MANDATORY MFA SETUP RESPONSE
# =====================================================

class MfaSetupRequiredResponse(BaseModel):
    """
    Returned after successful password verification when
    a privileged account has not yet configured mandatory
    MFA.

    This applies to roles such as:

    - CLINICIAN;
    - ADMINISTRATOR.

    The account must complete TOTP enrolment before normal
    access and refresh tokens are issued.
    """

    mfa_setup_required: bool = True

    mfa_setup_token: str

    message: str


# =====================================================
# PRIVILEGED MFA SETUP REQUEST
# =====================================================

class MfaSetupLoginRequest(BaseModel):
    """
    Start privileged-role MFA enrolment during login.

    The supplied token proves that password verification
    has already succeeded.

    Important:
        The MFA setup token is not an access token.
    """

    mfa_setup_token: str = Field(
        min_length=20,
        max_length=2000,
    )


# =====================================================
# PRIVILEGED MFA SETUP CONFIRMATION
# =====================================================

class MfaSetupLoginConfirmRequest(
    MfaSetupLoginRequest
):
    """
    Confirm mandatory privileged-role TOTP enrolment.

    The six-digit code must come from the authenticator
    application configured using the provisioning URI or
    manual secret returned during setup.
    """

    code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


# =====================================================
# PRIVILEGED MFA SETUP COMPLETION RESPONSE
# =====================================================

class MfaSetupLoginCompleteResponse(
    AuthenticationTokensResponse
):
    """
    Return normal authentication credentials after a
    clinician or administrator successfully completes
    mandatory MFA enrolment.

    Recovery codes are returned only once and should be
    stored securely by the user.
    """

    message: str

    recovery_codes: list[str]


# =====================================================
# EMAIL VERIFICATION REQUEST
# =====================================================

class EmailVerificationRequest(BaseModel):
    """
    Verify a user account using a six-digit email OTP.
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
        Strip surrounding whitespace and convert the email
        address to lowercase.
        """

        return (
            str(value)
            .strip()
            .lower()
        )


# =====================================================
# RESEND EMAIL VERIFICATION REQUEST
# =====================================================

class ResendEmailVerificationRequest(BaseModel):
    """
    Request a replacement email-verification OTP.

    The route should return a uniform response whether or
    not the supplied account exists.
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
        """Normalise the supplied email address."""

        return (
            str(value)
            .strip()
            .lower()
        )


# =====================================================
# PASSWORD-RESET REQUEST
# =====================================================

class PasswordResetRequest(BaseModel):
    """
    Request password-reset instructions.

    The API should return the same response regardless of
    whether the supplied email exists.
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
        """Normalise the supplied email address."""

        return (
            str(value)
            .strip()
            .lower()
        )


# =====================================================
# PASSWORD-RESET CONFIRMATION
# =====================================================

class PasswordResetConfirmRequest(BaseModel):
    """
    Complete a password reset using a single-use token.
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
    Exchange a valid refresh token for a newly rotated
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
    Revoke one refresh-token session.
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
    Return the information needed to configure a TOTP
    authenticator application.

    provisioning_uri:
        otpauth:// URI suitable for rendering as a QR code.

    manual_secret:
        Base32 secret that may be manually entered into the
        authenticator application.

    Security:
        The manual secret should only be displayed during
        enrolment and must never be written to logs.
    """

    provisioning_uri: str

    manual_secret: str

    message: str


# =====================================================
# CONFIRM TOTP ENROLMENT REQUEST
# =====================================================

class TotpEnrollmentConfirmRequest(BaseModel):
    """
    Confirm normal authenticated TOTP enrolment using the
    six-digit code generated by the authenticator.
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
    Return one-time recovery codes after MFA enrolment.

    Recovery codes should be displayed only once. Only
    cryptographic hashes should be persisted.
    """

    message: str

    recovery_codes: list[str]


# =====================================================
# TOTP LOGIN VERIFICATION REQUEST
# =====================================================

class TotpLoginVerifyRequest(BaseModel):
    """
    Complete MFA login using either:

    - a six-digit TOTP authenticator code; or
    - a one-time recovery code.
    """

    mfa_challenge_token: str = Field(
        min_length=20,
        max_length=2000,
    )

    # Recovery codes may be longer than six characters,
    # therefore this field deliberately allows a larger
    # maximum length than the enrolment-confirmation code.
    code: str = Field(
        min_length=6,
        max_length=100,
    )


# =====================================================
# DISABLE TOTP MFA REQUEST
# =====================================================

class TotpDisableRequest(BaseModel):
    """
    Disable MFA after verifying both:

    - the user's current password; and
    - a current TOTP or one-time recovery code.

    Note:
        The route layer should reject this operation for
        roles where MFA is mandatory, such as CLINICIAN
        and ADMINISTRATOR.
    """

    password: str = Field(
        min_length=1,
        max_length=200,
    )

    code: str = Field(
        min_length=6,
        max_length=100,
    )
