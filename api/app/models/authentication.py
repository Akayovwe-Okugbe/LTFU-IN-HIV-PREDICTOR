"""MEDISCOPE Phase 2 authentication database models.

Stores rotating refresh-token sessions, pending TOTP enrolments, and hashed MFA
recovery codes. Plaintext secrets are never persisted.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.entities import IdMixin, utcnow


class RefreshTokenSession(IdMixin, Base):
    """Store a hashed refresh token and its rotation state."""
    __tablename__ = "refresh_token_sessions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    family_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    parent_session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("refresh_token_sessions.id", ondelete="SET NULL"), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    replaced_by_session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("refresh_token_sessions.id", ondelete="SET NULL"), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)


class PendingTotpEnrollment(IdMixin, Base):
    """Store a temporary TOTP secret until enrolment is confirmed."""
    __tablename__ = "pending_totp_enrollments"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    secret_encrypted: Mapped[str] = mapped_column(String(1024), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class MfaRecoveryCode(IdMixin, Base):
    """Store one hashed, single-use MFA recovery code."""
    __tablename__ = "mfa_recovery_codes"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
