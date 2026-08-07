"""
=========================================================
Authentication Workflow Service

MEDISCOPE
LTFU Prediction Platform

Purpose:
    Implements reusable authentication workflows that are
    independent of FastAPI route handling.

    This service supports:

    - issuing email-verification OTPs;
    - validating email-verification OTPs;
    - issuing password-reset tokens;
    - completing password resets;
    - invalidating active refresh-token sessions after
      sensitive account changes.

Security:
    - Plaintext OTPs are never stored.
    - Plaintext password-reset tokens are never stored.
    - Existing verification and reset tokens are invalidated
      before new ones are created.
    - Password resets revoke all active refresh tokens.

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


# =====================================================
# SQLALCHEMY IMPORTS
# =====================================================

from sqlalchemy import (
    delete,
    select,
)
from sqlalchemy.orm import Session


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.core.config import get_settings

from app.core.enums import AccountStatus

from app.core.security import hash_password

from app.core.auth_security import (
    generate_numeric_otp,
    generate_url_safe_token,
    hash_secret,
)

from app.models.entities import (
    EmailVerificationToken,
    PasswordResetToken,
    User,
)

from app.services.email import (
    send_password_reset,
    send_verification_otp,
)

from app.services.tokens import (
    revoke_all_user_refresh_tokens,
)


# =====================================================
# CUSTOM AUTHENTICATION EXCEPTIONS
# =====================================================

class VerificationError(ValueError):
    """
    Raised when an email-verification request cannot be
    completed.
    """


class PasswordResetError(ValueError):
    """
    Raised when a password-reset request cannot be
    completed.
    """


# =====================================================
# ISSUE EMAIL-VERIFICATION OTP
# =====================================================

def issue_email_verification_otp(
    db: Session,
    *,
    user: User,
) -> None:
    """
    Generate and send a new email-verification OTP.

    Existing unused verification tokens for the user are
    deleted before a replacement token is created.

    Parameters
    ----------
    db:
        Active SQLAlchemy database session.

    user:
        User account requiring email verification.
    """

    settings = get_settings()

    # -------------------------------------------------
    # Generate the plaintext OTP.
    #
    # The plaintext value is sent to the user but is not
    # stored in PostgreSQL.
    # -------------------------------------------------

    otp = generate_numeric_otp()

    # -------------------------------------------------
    # Invalidate previous unused OTP records.
    # -------------------------------------------------

    db.execute(
        delete(
            EmailVerificationToken
        ).where(
            EmailVerificationToken.user_id
            == user.id,

            EmailVerificationToken.consumed_at
            .is_(None),
        )
    )

    # -------------------------------------------------
    # Store only the OTP hash.
    # -------------------------------------------------

    verification_token = EmailVerificationToken(
        user_id=user.id,

        token_hash=hash_secret(
            otp
        ),

        expires_at=(
            datetime.now(UTC)
            +
            timedelta(
                minutes=(
                    settings
                    .otp_expire_minutes
                )
            )
        ),

        attempts=0,
    )

    db.add(
        verification_token
    )

    # -------------------------------------------------
    # Send the OTP.
    #
    # During local development, the email service may
    # display the message in the API terminal.
    # -------------------------------------------------

    sent = send_verification_otp(
        db,
        user_id=user.id,
        recipient=user.email,
        otp=otp,
    )

    if not sent:
        raise VerificationError(
            "Unable to deliver the verification code."
        )


# =====================================================
# VERIFY EMAIL OTP
# =====================================================

def verify_email_otp(
    db: Session,
    *,
    user: User,
    otp: str,
) -> None:
    """
    Validate the most recent active email-verification OTP.

    A successful verification:

    - marks the OTP as consumed;
    - records the email-verification time;
    - activates the user account.

    Parameters
    ----------
    db:
        Active SQLAlchemy database session.

    user:
        User account being verified.

    otp:
        Plaintext OTP entered by the user.

    Raises
    ------
    VerificationError:
        If the OTP is missing, expired, invalid or has
        exceeded the configured attempt limit.
    """

    settings = get_settings()

    # -------------------------------------------------
    # Retrieve the most recently created unused token.
    # -------------------------------------------------

    token = db.scalar(
        select(
            EmailVerificationToken
        )
        .where(
            EmailVerificationToken.user_id
            == user.id,

            EmailVerificationToken.consumed_at
            .is_(None),
        )
        .order_by(
            EmailVerificationToken
            .created_at
            .desc()
        )
    )

    if token is None:
        raise VerificationError(
            "No active verification code exists."
        )

    current_time = datetime.now(
        UTC
    )

    # -------------------------------------------------
    # Reject expired tokens.
    # -------------------------------------------------

    if token.expires_at <= current_time:

        raise VerificationError(
            "Verification code has expired."
        )

    # -------------------------------------------------
    # Reject tokens that have exceeded the permitted
    # number of unsuccessful attempts.
    # -------------------------------------------------

    if (
        token.attempts
        >= settings.otp_max_attempts
    ):

        raise VerificationError(
            "Verification attempt limit reached."
        )

    # Count the current attempt before checking the OTP.
    token.attempts += 1

    # -------------------------------------------------
    # Compare the stored hash with the supplied OTP hash.
    # -------------------------------------------------

    if (
        token.token_hash
        != hash_secret(otp)
    ):

        raise VerificationError(
            "Invalid verification code."
        )

    # -------------------------------------------------
    # Complete verification.
    # -------------------------------------------------

    token.consumed_at = current_time

    user.email_verified_at = current_time

    user.account_status = (
        AccountStatus.ACTIVE.value
    )


# =====================================================
# ISSUE PASSWORD-RESET TOKEN
# =====================================================

def issue_password_reset(
    db: Session,
    *,
    user: User,
) -> None:
    """
    Generate and send a single-use password-reset token.

    Existing unused password-reset tokens for the account
    are invalidated before a replacement is created.

    Parameters
    ----------
    db:
        Active SQLAlchemy database session.

    user:
        User requesting a password reset.
    """

    settings = get_settings()

    # -------------------------------------------------
    # Generate a high-entropy plaintext reset token.
    # -------------------------------------------------

    plaintext_token = (
        generate_url_safe_token()
    )

    # -------------------------------------------------
    # Invalidate previous unused reset tokens.
    # -------------------------------------------------

    db.execute(
        delete(
            PasswordResetToken
        ).where(
            PasswordResetToken.user_id
            == user.id,

            PasswordResetToken.consumed_at
            .is_(None),
        )
    )

    # -------------------------------------------------
    # Store only the reset-token hash.
    # -------------------------------------------------

    reset_token = PasswordResetToken(
        user_id=user.id,

        token_hash=hash_secret(
            plaintext_token
        ),

        expires_at=(
            datetime.now(UTC)
            +
            timedelta(
                minutes=(
                    settings
                    .password_reset_expire_minutes
                )
            )
        ),
    )

    db.add(
        reset_token
    )

    # -------------------------------------------------
    # Send the plaintext token through the configured
    # email backend.
    # -------------------------------------------------

    sent = send_password_reset(
        db,
        user_id=user.id,
        recipient=user.email,
        reset_token=plaintext_token,
    )

    if not sent:
        raise PasswordResetError(
            "Unable to deliver password-reset instructions."
        )


# =====================================================
# COMPLETE PASSWORD RESET
# =====================================================

def complete_password_reset(
    db: Session,
    *,
    plaintext_token: str,
    new_password: str,
) -> User:
    """
    Complete a password reset using a valid single-use
    token.

    The function:

    - verifies the supplied reset token;
    - checks token expiry;
    - hashes and stores the new password;
    - clears login lockout information;
    - marks the reset token as consumed;
    - revokes all active refresh-token sessions.

    Parameters
    ----------
    db:
        Active SQLAlchemy database session.

    plaintext_token:
        Password-reset token supplied by the user.

    new_password:
        New plaintext password. It is immediately hashed
        and is never stored directly.

    Returns
    -------
    User
        Updated user account.

    Raises
    ------
    PasswordResetError:
        If the token is invalid, expired, consumed or not
        associated with an existing account.
    """

    token_hash = hash_secret(
        plaintext_token
    )

    # -------------------------------------------------
    # Locate the unused reset-token record.
    # -------------------------------------------------

    reset_token = db.scalar(
        select(
            PasswordResetToken
        ).where(
            PasswordResetToken.token_hash
            == token_hash,

            PasswordResetToken.consumed_at
            .is_(None),
        )
    )

    if reset_token is None:

        raise PasswordResetError(
            "Invalid password-reset token."
        )

    current_time = datetime.now(
        UTC
    )

    # -------------------------------------------------
    # Reject expired tokens.
    # -------------------------------------------------

    if (
        reset_token.expires_at
        <= current_time
    ):

        raise PasswordResetError(
            "Password-reset token has expired."
        )

    # -------------------------------------------------
    # Retrieve the associated user.
    # -------------------------------------------------

    user = db.get(
        User,
        reset_token.user_id,
    )

    if user is None:

        raise PasswordResetError(
            "Associated account no longer exists."
        )

    # -------------------------------------------------
    # Hash and save the new password.
    # -------------------------------------------------

    user.password_hash = hash_password(
        new_password
    )

    # Clear account lockout state.
    user.failed_login_count = 0
    user.locked_until = None

    # Mark the reset token as permanently consumed.
    reset_token.consumed_at = current_time

    # -------------------------------------------------
    # Revoke every active session.
    #
    # This prevents an attacker with an existing refresh
    # token from retaining access after the password has
    # been changed.
    # -------------------------------------------------

    revoke_all_user_refresh_tokens(
        db,
        user_id=user.id,
    )

    return user
