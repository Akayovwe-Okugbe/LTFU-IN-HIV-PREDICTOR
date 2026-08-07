"""MEDISCOPE TOTP enrolment, verification, recovery, and disable workflows."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.auth_security import (
    build_totp_provisioning_uri,
    generate_recovery_codes,
    generate_totp_secret,
    hash_secret,
    verify_totp_code,
)
from app.models.authentication import MfaRecoveryCode, PendingTotpEnrollment
from app.models.entities import User


class MfaError(ValueError):
    """Raised when an MFA operation fails validation."""


def begin_totp_enrollment(db: Session, *, user: User) -> tuple[str, str]:
    """Create or replace a pending TOTP enrolment."""
    secret = generate_totp_secret()
    existing = db.scalar(
        select(PendingTotpEnrollment).where(PendingTotpEnrollment.user_id == user.id)
    )
    if existing is not None:
        db.delete(existing)
        db.flush()
    db.add(
        PendingTotpEnrollment(
            user_id=user.id,
            secret_encrypted=secret,
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
    )
    return build_totp_provisioning_uri(email=user.email, secret=secret), secret


def confirm_totp_enrollment(db: Session, *, user: User, code: str) -> list[str]:
    """Confirm enrolment and return recovery codes exactly once."""
    pending = db.scalar(
        select(PendingTotpEnrollment).where(PendingTotpEnrollment.user_id == user.id)
    )
    if pending is None:
        raise MfaError("No pending MFA enrolment exists.")
    if pending.expires_at <= datetime.now(UTC):
        db.delete(pending)
        raise MfaError("MFA enrolment has expired.")
    if not verify_totp_code(secret=pending.secret_encrypted, code=code):
        raise MfaError("Invalid authenticator code.")

    user.mfa_secret_encrypted = pending.secret_encrypted
    user.mfa_enabled = True
    db.execute(delete(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user.id))
    plaintext_codes = generate_recovery_codes()
    for plaintext in plaintext_codes:
        db.add(MfaRecoveryCode(user_id=user.id, code_hash=hash_secret(plaintext)))
    db.delete(pending)
    return plaintext_codes


def verify_user_mfa_code(db: Session, *, user: User, code: str) -> bool:
    """Verify a TOTP code or consume one unused recovery code."""
    if user.mfa_secret_encrypted and verify_totp_code(
        secret=user.mfa_secret_encrypted,
        code=code,
    ):
        return True
    recovery = db.scalar(
        select(MfaRecoveryCode).where(
            MfaRecoveryCode.user_id == user.id,
            MfaRecoveryCode.code_hash == hash_secret(code),
            MfaRecoveryCode.consumed_at.is_(None),
        )
    )
    if recovery is None:
        return False
    recovery.consumed_at = datetime.now(UTC)
    return True


def disable_user_mfa(db: Session, *, user: User) -> None:
    """Disable MFA and remove pending and recovery data."""
    user.mfa_enabled = False
    user.mfa_secret_encrypted = None
    db.execute(delete(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user.id))
    db.execute(
        delete(PendingTotpEnrollment).where(PendingTotpEnrollment.user_id == user.id)
    )
