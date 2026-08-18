"""
=========================================================
MEDISCOPE Authentication Security API Routes

Purpose:
    Expose MEDISCOPE authentication-security workflows
    through FastAPI.

Implemented workflows:
    - email verification using OTP;
    - verification-code resend;
    - forgotten-password requests;
    - password-reset confirmation;
    - refresh-token rotation;
    - logout and refresh-token revocation;
    - TOTP authenticator enrolment;
    - TOTP MFA login;
    - one-time MFA recovery codes;
    - TOTP MFA removal;
    - mandatory MFA enrolment for privileged roles.

Security:
    - Registration-related email responses do not disclose
      whether an account exists.
    - Plaintext OTPs, reset tokens and refresh tokens are
      not stored in PostgreSQL.
    - MFA-enabled users do not receive access tokens until
      the second authentication factor succeeds.
    - Sensitive authentication values must never be added
      to audit logs.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

from datetime import UTC, datetime
from uuid import UUID


# =====================================================
# THIRD-PARTY IMPORTS
# =====================================================

import jwt

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)

from sqlalchemy import select


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.api.dependencies import (
    CurrentUser,
    DbSession,
)

from app.core.enums import AccountStatus, UserRole

from app.core.security import (
    create_access_token,
    verify_password,
)

from app.core.auth_security import (
    create_mfa_challenge_token,
    decode_mfa_challenge_token,
    create_mfa_setup_token,
    decode_mfa_setup_token,
)

from app.models.entities import User

from app.schemas.authentication import (
    AuthenticationTokensResponse,
    EmailVerificationRequest,
    LogoutRequest,
    MfaRequiredResponse,
    MfaSetupRequiredResponse,
    MfaSetupLoginRequest,
    MfaSetupLoginConfirmRequest,
    MfaSetupLoginCompleteResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    ResendEmailVerificationRequest,
    SecurityMessageResponse,
    TotpDisableRequest,
    TotpEnrollmentConfirmRequest,
    TotpEnrollmentConfirmResponse,
    TotpEnrollmentStartResponse,
    TotpLoginVerifyRequest,
)

from app.services.authentication import (
    PasswordResetError,
    VerificationError,
    complete_password_reset,
    issue_email_verification_otp,
    issue_password_reset,
    verify_email_otp,
)

from app.services.mfa import (
    MfaError,
    begin_totp_enrollment,
    confirm_totp_enrollment,
    disable_user_mfa,
    verify_user_mfa_code,
)

from app.services.tokens import (
    RefreshTokenError,
    create_refresh_token_session,
    revoke_refresh_token,
    rotate_refresh_token,
)

from app.services.audit import (
    write_audit_log,
)


# =====================================================
# ROUTER CONFIGURATION
# =====================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# =====================================================
# UNIFORM EMAIL RESPONSE
#
# This response is deliberately returned whether or not
# the supplied account exists.
# =====================================================

GENERIC_EMAIL_RESPONSE = (
    "If the account is eligible, further instructions "
    "will be sent to the registered email address."
)


# =====================================================
# REQUEST INFORMATION HELPER
# =====================================================

def get_client_ip(
    request: Request,
) -> str | None:
    """
    Return the request IP address when available.
    """

    if request.client is None:
        return None

    return request.client.host


# =====================================================
# ACCESS AND REFRESH TOKEN CREATION
# =====================================================

def create_login_tokens(
    db: DbSession,
    *,
    user: User,
    request: Request,
    mfa_verified: bool,
) -> AuthenticationTokensResponse:
    """
    Create a short-lived access token and a rotating,
    database-backed refresh token.

    Parameters
    ----------
    db:
        Active database session.

    user:
        Authenticated user.

    request:
        Current FastAPI request.

    mfa_verified:
        Whether the required MFA challenge was completed.
    """

    access_token = create_access_token(
        subject=user.id,
        role=user.role,
        mfa_verified=mfa_verified,
    )

    refresh_token, _ = (
        create_refresh_token_session(
            db,
            user_id=user.id,
            ip_address=get_client_ip(
                request
            ),
            user_agent=request.headers.get(
                "user-agent"
            ),
        )
    )

    return AuthenticationTokensResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


# =====================================================
# EMAIL VERIFICATION
# =====================================================

@router.post(
    "/email/verify",
    response_model=SecurityMessageResponse,
)
def verify_email(
    payload: EmailVerificationRequest,
    db: DbSession,
) -> SecurityMessageResponse:
    """
    Activate an account after verification of a valid
    email OTP.
    """

    email = str(
        payload.email
    ).strip().lower()

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if user is None:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Invalid or expired "
                "verification code."
            ),
        )

    try:
        verify_email_otp(
            db,
            user=user,
            otp=payload.otp,
        )

    except VerificationError:
        db.commit()

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Invalid or expired "
                "verification code."
            ),
        )

    db.commit()

    return SecurityMessageResponse(
        message="Email verified successfully."
    )


# =====================================================
# RESEND EMAIL VERIFICATION OTP
# =====================================================

@router.post(
    "/email/resend",
    response_model=SecurityMessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def resend_verification(
    payload: ResendEmailVerificationRequest,
    db: DbSession,
) -> SecurityMessageResponse:
    """
    Issue a replacement verification OTP without exposing
    whether the supplied account exists.
    """

    email = str(
        payload.email
    ).strip().lower()

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if (
        user is not None
        and user.email_verified_at is None
    ):
        try:
            # The service sends the OTP through email.py.
            # It does not return the plaintext OTP.
            issue_email_verification_otp(
                db,
                user=user,
            )

            db.commit()

        except VerificationError:
            db.rollback()

    return SecurityMessageResponse(
        message=GENERIC_EMAIL_RESPONSE
    )


# =====================================================
# FORGOTTEN PASSWORD REQUEST
# =====================================================

@router.post(
    "/password/forgot",
    response_model=SecurityMessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def forgot_password(
    payload: PasswordResetRequest,
    db: DbSession,
) -> SecurityMessageResponse:
    """
    Issue password-reset instructions without disclosing
    whether the supplied email address exists.
    """

    email = str(
        payload.email
    ).strip().lower()

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if user is not None:
        try:
            # The plaintext reset token is sent through
            # email.py and is not returned by the service.
            issue_password_reset(
                db,
                user=user,
            )

            db.commit()

        except PasswordResetError:
            db.rollback()

    return SecurityMessageResponse(
        message=GENERIC_EMAIL_RESPONSE
    )


# =====================================================
# PASSWORD RESET CONFIRMATION
# =====================================================

@router.post(
    "/password/reset",
    response_model=SecurityMessageResponse,
)
def reset_password(
    payload: PasswordResetConfirmRequest,
    db: DbSession,
) -> SecurityMessageResponse:
    """
    Complete a password reset and revoke every existing
    refresh-token session for the user.
    """

    try:
        complete_password_reset(
            db,
            plaintext_token=payload.token,
            new_password=payload.new_password,
        )

    except (
        PasswordResetError,
        ValueError,
    ):
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Invalid or expired "
                "password-reset token."
            ),
        )

    db.commit()

    return SecurityMessageResponse(
        message=(
            "Password reset completed. "
            "Please sign in again."
        )
    )


# =====================================================
# REFRESH TOKEN ROTATION
# =====================================================

@router.post(
    "/token/refresh",
    response_model=AuthenticationTokensResponse,
)
def refresh_access_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: DbSession,
) -> AuthenticationTokensResponse:
    """
    Rotate a valid refresh token and issue a new access
    token and replacement refresh token.
    """

    try:
        user_id, replacement_token = (
            rotate_refresh_token(
                db,
                plaintext_token=(
                    payload.refresh_token
                ),
                ip_address=get_client_ip(
                    request
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
            )
        )

    except RefreshTokenError:
        # Committing preserves token-family revocation when
        # refresh-token reuse has been detected.
        db.commit()

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid refresh token.",
        )

    user = db.get(
        User,
        user_id,
    )

    if (
        user is None
        or user.account_status
        != AccountStatus.ACTIVE.value
    ):
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid refresh token.",
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role,
        # The original login already required MFA when the
        # account had it enabled. The refresh session was
        # created only after that successful authentication.
        mfa_verified=True,
    )

    db.commit()

    return AuthenticationTokensResponse(
        access_token=access_token,
        refresh_token=replacement_token,
        token_type="bearer",
    )


# =====================================================
# LOGOUT
# =====================================================

@router.post(
    "/logout",
    response_model=SecurityMessageResponse,
)
def logout(
    payload: LogoutRequest,
    db: DbSession,
) -> SecurityMessageResponse:
    """
    Revoke the supplied refresh-token session.
    """

    revoke_refresh_token(
        db,
        plaintext_token=(
            payload.refresh_token
        ),
    )

    db.commit()

    return SecurityMessageResponse(
        message="Signed out successfully."
    )


# =====================================================
# START TOTP ENROLMENT
# =====================================================

@router.post(
    "/mfa/totp/setup",
    response_model=TotpEnrollmentStartResponse,
)
def start_totp_setup(
    current_user: CurrentUser,
    db: DbSession,
) -> TotpEnrollmentStartResponse:
    """
    Start authenticator-application enrolment.
    """

    provisioning_uri, secret = (
        begin_totp_enrollment(
            db,
            user=current_user,
        )
    )

    db.commit()

    return TotpEnrollmentStartResponse(
        provisioning_uri=provisioning_uri,
        manual_secret=secret,
        message=(
            "Confirm enrolment using a current "
            "authenticator code."
        ),
    )


# =====================================================
# CONFIRM TOTP ENROLMENT
# =====================================================

@router.post(
    "/mfa/totp/confirm",
    response_model=(
        TotpEnrollmentConfirmResponse
    ),
)
def confirm_totp_setup(
    payload: TotpEnrollmentConfirmRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> TotpEnrollmentConfirmResponse:
    """
    Confirm TOTP enrolment and return the user's one-time
    recovery codes.

    Recovery codes are shown only once.
    """

    try:
        recovery_codes = (
            confirm_totp_enrollment(
                db,
                user=current_user,
                code=payload.code,
            )
        )

    except MfaError as error:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        )

    db.commit()

    return TotpEnrollmentConfirmResponse(
        message=(
            "Two-factor authentication enabled. "
            "Store the recovery codes securely."
        ),
        recovery_codes=recovery_codes,
    )


# =====================================================
# COMPLETE MFA LOGIN
# =====================================================

@router.post(
    "/mfa/totp/login",
    response_model=AuthenticationTokensResponse,
)
def complete_mfa_login(
    payload: TotpLoginVerifyRequest,
    request: Request,
    db: DbSession,
) -> AuthenticationTokensResponse:
    """
    Complete login using either a TOTP authenticator code
    or a one-time MFA recovery code.
    """

    try:
        claims = decode_mfa_challenge_token(
            payload.mfa_challenge_token
        )

        user_id = UUID(
            str(claims["sub"])
        )

    except (
        jwt.InvalidTokenError,
        KeyError,
        ValueError,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid MFA challenge.",
        )

    user = db.get(
        User,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid MFA code.",
        )

    if not user.mfa_enabled:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid MFA code.",
        )

    code_valid = verify_user_mfa_code(
        db,
        user=user,
        code=payload.code,
    )

    if not code_valid:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid MFA code.",
        )

    response = create_login_tokens(
        db,
        user=user,
        request=request,
        mfa_verified=True,
    )

    user.last_login_at = datetime.now(
        UTC
    )

    db.commit()

    return response


# =====================================================
# DISABLE TOTP MFA
# =====================================================

@router.post(
    "/mfa/totp/disable",
    response_model=SecurityMessageResponse,
)
def disable_totp(
    payload: TotpDisableRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> SecurityMessageResponse:
    """
    Disable MFA after verifying both the user's password
    and current authentication factor.
    """

    if current_user.role in {
        UserRole.CLINICIAN.value,
        UserRole.ADMINISTRATOR.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Multi-factor authentication is mandatory "
                "for clinician and administrator accounts."
            ),
        )

    password_valid = verify_password(
        payload.password,
        current_user.password_hash,
    )

    if not password_valid:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Password or MFA code is invalid."
            ),
        )

    code_valid = verify_user_mfa_code(
        db,
        user=current_user,
        code=payload.code,
    )

    if not code_valid:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Password or MFA code is invalid."
            ),
        )

    disable_user_mfa(
        db,
        user=current_user,
    )

    db.commit()

    return SecurityMessageResponse(
        message=(
            "Two-factor authentication disabled."
        )
    )


# =====================================================
# SUCCESSFUL PASSWORD-LOGIN RESPONSE
# =====================================================

def build_login_response(
    db: DbSession,
    *,
    user: User,
    request: Request,
) -> (
    AuthenticationTokensResponse
    | MfaRequiredResponse
    | MfaSetupRequiredResponse
):
    """Build the secure response after password validation."""

    # Accounts that already use MFA must prove the second
    # factor before receiving normal tokens.
    if user.mfa_enabled:
        return MfaRequiredResponse(
            mfa_required=True,
            mfa_challenge_token=create_mfa_challenge_token(
                subject=user.id,
                role=user.role,
            ),
            message="A second authentication factor is required.",
        )

    privileged_roles = {
        UserRole.CLINICIAN.value,
        UserRole.ADMINISTRATOR.value,
    }

    # A privileged account without MFA gets only a
    # short-lived setup token, never an access token.
    if user.role in privileged_roles:
        return MfaSetupRequiredResponse(
            mfa_setup_required=True,
            mfa_setup_token=create_mfa_setup_token(
                subject=user.id,
                role=user.role,
            ),
            message=(
                "Multi-factor authentication must be configured "
                "before this role can sign in."
            ),
        )

    # Standard USER may continue without MFA.
    return create_login_tokens(
        db,
        user=user,
        request=request,
        mfa_verified=False,
    )


def _user_from_mfa_setup_token(
    db: DbSession,
    token: str,
) -> User:
    try:
        claims = decode_mfa_setup_token(token)
        user_id = UUID(str(claims["sub"]))
    except (
        jwt.InvalidTokenError,
        KeyError,
        ValueError,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA setup challenge.",
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA setup challenge.",
        )

    if user.role not in {
        UserRole.CLINICIAN.value,
        UserRole.ADMINISTRATOR.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA setup is not required for this login.",
        )

    if user.account_status != AccountStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not active.",
        )

    return user


@router.post(
    "/mfa/totp/setup/login",
    response_model=TotpEnrollmentStartResponse,
)
def start_required_totp_setup(
    payload: MfaSetupLoginRequest,
    db: DbSession,
) -> TotpEnrollmentStartResponse:
    user = _user_from_mfa_setup_token(
        db,
        payload.mfa_setup_token,
    )

    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MFA is already enabled.",
        )

    provisioning_uri, secret = begin_totp_enrollment(
        db,
        user=user,
    )

    db.commit()

    return TotpEnrollmentStartResponse(
        provisioning_uri=provisioning_uri,
        manual_secret=secret,
        message="Scan the QR code and confirm the current authenticator code.",
    )


@router.post(
    "/mfa/totp/confirm/login",
    response_model=MfaSetupLoginCompleteResponse,
)
def confirm_required_totp_setup(
    payload: MfaSetupLoginConfirmRequest,
    request: Request,
    db: DbSession,
) -> MfaSetupLoginCompleteResponse:
    user = _user_from_mfa_setup_token(
        db,
        payload.mfa_setup_token,
    )

    try:
        recovery_codes = confirm_totp_enrollment(
            db,
            user=user,
            code=payload.code,
        )
    except MfaError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    tokens = create_login_tokens(
        db,
        user=user,
        request=request,
        mfa_verified=True,
    )

    user.last_login_at = datetime.now(UTC)

    write_audit_log(
        db,
        actor_user_id=user.id,
        action="MFA_REQUIRED_ENROLMENT_COMPLETED",
        outcome="SUCCESS",
        resource_type="USER",
        resource_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    db.commit()

    return MfaSetupLoginCompleteResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        message="MFA enabled successfully. Store the recovery codes securely.",
        recovery_codes=recovery_codes,
    )
