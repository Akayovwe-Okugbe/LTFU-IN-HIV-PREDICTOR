"""
=========================================================
MEDISCOPE Multi-Factor Authentication Service

Purpose:
    Implement TOTP authenticator enrolment, verification,
    recovery-code authentication and MFA removal.

Security:
    - TOTP secrets are encrypted before persistence.
    - Plaintext TOTP secrets exist only transiently during
      provisioning or verification.
    - Recovery codes are persisted only as hashes.
    - Recovery codes are single use.
    - Invalid or undecryptable TOTP secrets fail closed.
    - Sensitive MFA values must never be written to logs.

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

from sqlalchemy.orm import (
    Session,
)


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.core.auth_security import (
    build_totp_provisioning_uri,
    generate_recovery_codes,
    generate_totp_secret,
    hash_secret,
    verify_totp_code,
)

from app.core.secret_encryption import (
    SecretEncryptionError,
    decrypt_totp_secret,
    encrypt_totp_secret,
)

from app.models.authentication import (
    MfaRecoveryCode,
    PendingTotpEnrollment,
)

from app.models.entities import (
    User,
)


# =====================================================
# MFA DOMAIN ERROR
# =====================================================

class MfaError(
    ValueError
):
    """
    Raised when an MFA workflow cannot be safely
    completed.
    """


# =====================================================
# START TOTP ENROLMENT
# =====================================================

def begin_totp_enrollment(
    db: Session,
    *,
    user: User,
) -> tuple[str, str]:
    """
    Create or replace a pending TOTP enrolment.

    The plaintext TOTP secret is returned only because the
    caller must provide it to the user's authenticator
    application through the provisioning URI/manual setup
    value.

    PostgreSQL receives only encrypted ciphertext.
    """

    # -------------------------------------------------
    # GENERATE NEW TOTP SECRET
    # -------------------------------------------------

    secret = (
        generate_totp_secret()
    )


    # -------------------------------------------------
    # ENCRYPT BEFORE PERSISTENCE
    # -------------------------------------------------

    try:
        encrypted_secret = (
            encrypt_totp_secret(
                secret
            )
        )

    except SecretEncryptionError as error:
        raise MfaError(
            "Unable to start MFA enrolment securely."
        ) from error


    # -------------------------------------------------
    # REMOVE ANY PREVIOUS PENDING ENROLMENT
    # -------------------------------------------------

    existing = db.scalar(
        select(
            PendingTotpEnrollment
        ).where(
            PendingTotpEnrollment
            .user_id
            == user.id
        )
    )

    if existing is not None:
        db.delete(
            existing
        )

        db.flush()


    # -------------------------------------------------
    # STORE ENCRYPTED PENDING SECRET
    # -------------------------------------------------

    db.add(
        PendingTotpEnrollment(
            user_id=user.id,

            secret_encrypted=(
                encrypted_secret
            ),

            expires_at=(
                datetime.now(UTC)
                +
                timedelta(
                    minutes=10,
                )
            ),
        )
    )


    # -------------------------------------------------
    # PROVISIONING INFORMATION
    #
    # The authenticator application requires the original
    # plaintext secret. It is never persisted here.
    # -------------------------------------------------

    provisioning_uri = (
        build_totp_provisioning_uri(
            email=user.email,
            secret=secret,
        )
    )

    return (
        provisioning_uri,
        secret,
    )


# =====================================================
# CONFIRM TOTP ENROLMENT
# =====================================================

def confirm_totp_enrollment(
    db: Session,
    *,
    user: User,
    code: str,
) -> list[str]:
    """
    Confirm a pending authenticator enrolment.

    Successful confirmation:

        - decrypts the temporary TOTP secret;
        - validates the submitted authenticator code;
        - copies encrypted ciphertext to the user's
          permanent MFA field;
        - replaces previous recovery codes;
        - removes the pending enrolment;
        - returns new plaintext recovery codes exactly
          once.
    """

    pending = db.scalar(
        select(
            PendingTotpEnrollment
        ).where(
            PendingTotpEnrollment
            .user_id
            == user.id
        )
    )


    # -------------------------------------------------
    # PENDING ENROLMENT REQUIRED
    # -------------------------------------------------

    if pending is None:
        raise MfaError(
            "No pending MFA enrolment exists."
        )


    # -------------------------------------------------
    # EXPIRY
    # -------------------------------------------------

    if (
        pending.expires_at
        <= datetime.now(UTC)
    ):
        db.delete(
            pending
        )

        raise MfaError(
            "MFA enrolment has expired."
        )


    # -------------------------------------------------
    # DECRYPT THE TEMPORARY SECRET
    # -------------------------------------------------

    try:
        secret = (
            decrypt_totp_secret(
                pending
                .secret_encrypted
            )
        )

    except SecretEncryptionError as error:
        # A pending value that cannot be decrypted may
        # have been created before encryption was enabled,
        # tampered with, or encrypted using another key.
        #
        # Remove it and require a clean enrolment.
        db.delete(
            pending
        )

        raise MfaError(
            "MFA enrolment could not be validated. "
            "Please start authenticator setup again."
        ) from error


    # -------------------------------------------------
    # VERIFY AUTHENTICATOR CODE
    # -------------------------------------------------

    if not verify_totp_code(
        secret=secret,
        code=code,
    ):
        raise MfaError(
            "Invalid authenticator code."
        )


    # -------------------------------------------------
    # ACTIVATE MFA
    #
    # IMPORTANT:
    # Copy the encrypted database value rather than the
    # decrypted plaintext secret.
    # -------------------------------------------------

    user.mfa_secret_encrypted = (
        pending
        .secret_encrypted
    )

    user.mfa_enabled = True


    # -------------------------------------------------
    # REPLACE EXISTING RECOVERY CODES
    # -------------------------------------------------

    db.execute(
        delete(
            MfaRecoveryCode
        ).where(
            MfaRecoveryCode
            .user_id
            == user.id
        )
    )


    plaintext_codes = (
        generate_recovery_codes()
    )

    for plaintext_code in (
        plaintext_codes
    ):
        db.add(
            MfaRecoveryCode(
                user_id=user.id,

                code_hash=hash_secret(
                    plaintext_code
                ),
            )
        )


    # -------------------------------------------------
    # PENDING ENROLMENT IS SINGLE USE
    # -------------------------------------------------

    db.delete(
        pending
    )

    return plaintext_codes


# =====================================================
# VERIFY MFA CODE
# =====================================================

def verify_user_mfa_code(
    db: Session,
    *,
    user: User,
    code: str,
) -> bool:
    """
    Verify either:

        1. a current TOTP authenticator code; or
        2. one unused MFA recovery code.

    A corrupted, legacy plaintext or otherwise
    undecryptable TOTP secret never falls back to plaintext
    interpretation.

    Recovery codes remain usable independently because they
    provide the user's intended recovery path when access
    to the authenticator factor is unavailable.
    """

    # -------------------------------------------------
    # TOTP VERIFICATION
    # -------------------------------------------------

    if (
        user.mfa_secret_encrypted
    ):
        try:
            secret = (
                decrypt_totp_secret(
                    user
                    .mfa_secret_encrypted
                )
            )

        except SecretEncryptionError:
            # Fail closed for TOTP rather than exposing
            # cryptographic details or attempting plaintext
            # compatibility.
            secret = None


        if (
            secret is not None
            and
            verify_totp_code(
                secret=secret,
                code=code,
            )
        ):
            return True


    # -------------------------------------------------
    # RECOVERY-CODE VERIFICATION
    #
    # Recovery codes are random values whose SHA-256
    # hashes are persisted. A successful use is marked as
    # consumed immediately within the current transaction.
    # -------------------------------------------------

    recovery = db.scalar(
        select(
            MfaRecoveryCode
        ).where(
            MfaRecoveryCode
            .user_id
            == user.id,

            MfaRecoveryCode
            .code_hash
            == hash_secret(
                code
            ),

            MfaRecoveryCode
            .consumed_at
            .is_(None),
        )
    )


    if recovery is None:
        return False


    recovery.consumed_at = (
        datetime.now(
            UTC
        )
    )

    return True


# =====================================================
# DISABLE MFA
# =====================================================

def disable_user_mfa(
    db: Session,
    *,
    user: User,
) -> None:
    """
    Disable MFA and remove associated authenticator state.

    This service removes:

        - the user's permanent encrypted TOTP secret;
        - all recovery codes;
        - any pending enrolment.

    Route-level authorisation remains responsible for
    preventing MFA removal where it is mandatory for the
    user's role.
    """

    user.mfa_enabled = False

    user.mfa_secret_encrypted = (
        None
    )


    db.execute(
        delete(
            MfaRecoveryCode
        ).where(
            MfaRecoveryCode
            .user_id
            == user.id
        )
    )


    db.execute(
        delete(
            PendingTotpEnrollment
        ).where(
            PendingTotpEnrollment
            .user_id
            == user.id
        )
    )
