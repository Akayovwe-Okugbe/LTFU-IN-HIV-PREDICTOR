"""
=========================================================
Authentication API

MEDISCOPE
LTFU Prediction Platform

Purpose:
    Provides user registration and login endpoints.

Security:
    • Uniform registration responses prevent account
      enumeration.
    • Passwords are stored using Argon2id hashing.
    • Every authentication event is written to the audit log.
    • Email verification is required before login.
    • Login automatically supports optional MFA through
      the Phase 2 authentication workflow.

Author:
    Akayovwe Okugbe

=========================================================
"""

from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import select

from api.app import db
from app.api.dependencies import DbSession
from app.core.enums import (
    AccountStatus,
    UserRole,
)
from app.core.security import (
    hash_password,
    verify_password,
)
from app.models.entities import User
from app.schemas.auth import (
    GenericResponse,
    LoginRequest,
    RegisterRequest,
)
from app.schemas.authentication import (
    AuthenticationTokensResponse,
    MfaRequiredResponse,
    MfaSetupRequiredResponse,
)
from app.services.audit import write_audit_log

# =====================================================
# PHASE 2 AUTHENTICATION SERVICES
# =====================================================

from app.services.authentication import (
    issue_email_verification_otp,
)

from app.api.routes.authentication_phase2 import (
    build_login_response,
)

# =====================================================
# PHASE 3 NOTIFICATION SERVICES
# =====================================================

from app.services.notifications import (
    notify_administrators_of_registration,
    send_welcome_message,
)

# =====================================================
# ROUTER CONFIGURATION
# =====================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# =====================================================
# UNIFORM REGISTRATION RESPONSE
#
# Returned regardless of whether the email already
# exists. Prevents attackers discovering registered
# accounts through the registration endpoint.
# =====================================================

_UNIFORM_MESSAGE = (
    "If this email can be registered or is already "
    "associated with an account, further instructions "
    "will be sent."
)


# =====================================================
# USER REGISTRATION
# =====================================================

@router.post(
    "/register",
    response_model=GenericResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def register(
    payload: RegisterRequest,
    request: Request,
    db: DbSession,
) -> GenericResponse:
    """
    Register a new MEDISCOPE user.

    The endpoint deliberately returns the same response
    whether or not the email already exists to reduce
    account-enumeration attacks.
    """

    email = str(payload.email).lower()

    existing = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    # -------------------------------------------------
    # CREATE NEW ACCOUNT
    # -------------------------------------------------

    if existing is None:

        user = User(
            email=email,
            password_hash=hash_password(
                payload.password
            ),
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            date_of_birth=payload.date_of_birth,
            phone=payload.phone,
            gender=payload.gender,
            role=UserRole.USER.value,
            account_status=(
                AccountStatus
                .PENDING_EMAIL_VERIFICATION
                .value
            ),
        )

        db.add(user)

        # Flush obtains the generated UUID before commit.
        db.flush()

        # ---------------------------------------------
        # Generate and store a verification OTP.
        #
        # Current implementation may print the OTP to
        # the console for development.
        #
        # Later this will send the OTP by email.
        # ---------------------------------------------

        issue_email_verification_otp(
            db,
            user=user,
        )

        send_welcome_message(db, user=user)
        notify_administrators_of_registration(db, new_user=user)

        # ---------------------------------------------
        # Audit successful registration.
        # ---------------------------------------------

        write_audit_log(
            db,
            actor_user_id=user.id,
            action="ACCOUNT_REGISTERED",
            outcome="SUCCESS",
            resource_type="USER",
            resource_id=user.id,
            ip_address=(
                request.client.host
                if request.client
                else None
            ),
            user_agent=request.headers.get(
                "user-agent"
            ),
        )

    # -------------------------------------------------
    # DUPLICATE REGISTRATION
    # -------------------------------------------------

    else:

        write_audit_log(
            db,
            actor_user_id=existing.id,
            action="DUPLICATE_REGISTRATION_ATTEMPT",
            outcome="REJECTED",
            resource_type="USER",
            resource_id=existing.id,
            ip_address=(
                request.client.host
                if request.client
                else None
            ),
            user_agent=request.headers.get(
                "user-agent"
            ),
        )

    db.commit()

    return GenericResponse(
        message=_UNIFORM_MESSAGE
    )


# =====================================================
# USER LOGIN
# =====================================================

@router.post(
    "/login",
    response_model=(
        AuthenticationTokensResponse
        | MfaRequiredResponse
        | MfaSetupRequiredResponse
    ),
)
def login(
    payload: LoginRequest,
    request: Request,
    db: DbSession,
) -> (
    AuthenticationTokensResponse
    | MfaRequiredResponse
    | MfaSetupRequiredResponse
):
    """
    Authenticate a MEDISCOPE user.

    Login is completed in two stages:

    1. Verify the email address and password.
    2. If MFA is enabled, return an MFA challenge rather
       than full authentication tokens.

    Accounts without MFA receive access and refresh tokens
    immediately after successful authentication.
    """

    # -------------------------------------------------
    # NORMALISE EMAIL
    # -------------------------------------------------

    email = str(
        payload.email
    ).strip().lower()

    # -------------------------------------------------
    # RETRIEVE USER ACCOUNT
    # -------------------------------------------------

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    # -------------------------------------------------
    # HANDLE UNKNOWN EMAIL ADDRESS
    #
    # This check explicitly narrows the type from
    # User | None to User for Pylance and subsequent code.
    # -------------------------------------------------

    if user is None:

        write_audit_log(
            db,
            actor_user_id=None,
            action="LOGIN_ATTEMPT",
            outcome="FAILED",
            resource_type="USER",
            resource_id=None,
            ip_address=(
                request.client.host
                if request.client
                else None
            ),
            user_agent=request.headers.get(
                "user-agent"
            ),
        )

        db.commit()

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid email or password.",
        )

    # From this point onward, Pylance knows that user is
    # definitely a User instance rather than None.

    # -------------------------------------------------
    # VERIFY PASSWORD
    # -------------------------------------------------

    password_valid = verify_password(
        payload.password,
        user.password_hash,
    )

    if not password_valid:

        # Record the failed login attempt.
        user.failed_login_count += 1

        write_audit_log(
            db,
            actor_user_id=user.id,
            action="LOGIN_ATTEMPT",
            outcome="FAILED",
            resource_type="USER",
            resource_id=user.id,
            ip_address=(
                request.client.host
                if request.client
                else None
            ),
            user_agent=request.headers.get(
                "user-agent"
            ),
        )

        db.commit()

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid email or password.",
        )

    # -------------------------------------------------
    # VERIFY ACCOUNT STATUS
    # -------------------------------------------------

    if (
        user.account_status
        != AccountStatus.ACTIVE.value
    ):

        write_audit_log(
            db,
            actor_user_id=user.id,
            action="LOGIN_ATTEMPT",
            outcome="REJECTED",
            resource_type="USER",
            resource_id=user.id,
            ip_address=(
                request.client.host
                if request.client
                else None
            ),
            user_agent=request.headers.get(
                "user-agent"
            ),
            details={
                "reason": (
                    "Account verification or "
                    "activation required."
                )
            },
        )

        db.commit()

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Account verification or "
                "activation is required."
            ),
        )

    # -------------------------------------------------
    # RESET LOGIN-FAILURE STATE
    # -------------------------------------------------

    user.failed_login_count = 0

    user.locked_until = None

    # The final successful login time is set here for
    # accounts without MFA. For MFA-enabled users, it may
    # also be updated again when the second factor succeeds.
    user.last_login_at = datetime.now(
        UTC
    )

    # -------------------------------------------------
    # AUDIT SUCCESSFUL PASSWORD AUTHENTICATION
    # -------------------------------------------------

    write_audit_log(
        db,
        actor_user_id=user.id,
        action="LOGIN_ATTEMPT",
        outcome="SUCCESS",
        resource_type="USER",
        resource_id=user.id,
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
        user_agent=request.headers.get(
            "user-agent"
        ),
    )

    # -------------------------------------------------
    # BUILD PHASE 2 LOGIN RESPONSE
    #
    # MFA-enabled users receive a temporary challenge.
    # Other users receive access and refresh tokens.
    # -------------------------------------------------

    response = build_login_response(
        db=db,
        user=user,
        request=request,
    )

    db.commit()

    return response
