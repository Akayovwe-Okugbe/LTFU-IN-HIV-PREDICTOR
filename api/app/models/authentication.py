"""
=========================================================
MEDISCOPE Authentication Database Models

Purpose:
    Define persistence models used by MEDISCOPE's
    authentication-session and multi-factor authentication
    workflows.

Implemented persistence:
    - rotating refresh-token sessions;
    - pending TOTP enrolments;
    - hashed one-time MFA recovery codes.

Security:
    - Plaintext refresh tokens are never persisted.
    - Pending TOTP secrets are stored only in protected
      form during enrolment.
    - MFA recovery codes are stored as hashes and are
      single use.
    - Authentication-session data is kept separate from
      the main clinical/domain entities.
    - Sensitive authentication values must never be
      exposed through API responses or audit logs.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

from datetime import datetime
from uuid import UUID


# =====================================================
# SQLALCHEMY IMPORTS
# =====================================================

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.db.base import Base

from app.models.entities import (
    IdMixin,
    utcnow,
)


# =====================================================
# REFRESH-TOKEN SESSION
# =====================================================

class RefreshTokenSession(
    IdMixin,
    Base,
):
    """
    Store a hashed refresh-token session together with its
    rotation and revocation state.

    Refresh-token sessions support:

    - refresh-token rotation;
    - token-family tracking;
    - reuse detection;
    - explicit logout/revocation;
    - session metadata for security auditing.

    Security:
        Only a cryptographic hash of the refresh token is
        stored. The plaintext refresh token is returned to
        the client only when issued and must never be saved
        in this table.
    """

    __tablename__ = "refresh_token_sessions"


    # -------------------------------------------------
    # ACCOUNT RELATIONSHIP
    # -------------------------------------------------

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )


    # -------------------------------------------------
    # TOKEN IDENTITY
    # -------------------------------------------------

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    # All rotated descendants of one refresh-token chain
    # share the same family identifier. This allows the
    # application to revoke a token family if reuse is
    # detected.
    family_id: Mapped[UUID] = mapped_column(
        index=True,
        nullable=False,
    )


    # -------------------------------------------------
    # TOKEN ROTATION LINKS
    # -------------------------------------------------

    parent_session_id: Mapped[
        UUID | None
    ] = mapped_column(
        ForeignKey(
            "refresh_token_sessions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    replaced_by_session_id: Mapped[
        UUID | None
    ] = mapped_column(
        ForeignKey(
            "refresh_token_sessions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )


    # -------------------------------------------------
    # SESSION LIFECYCLE
    # -------------------------------------------------

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    last_used_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    # -------------------------------------------------
    # REQUEST METADATA
    #
    # These values support security review and session
    # auditing. They are not treated as authentication
    # factors.
    # -------------------------------------------------

    ip_address: Mapped[
        str | None
    ] = mapped_column(
        String(64),
        nullable=True,
    )

    user_agent: Mapped[
        str | None
    ] = mapped_column(
        String(500),
        nullable=True,
    )


# =====================================================
# PENDING TOTP ENROLMENT
# =====================================================

class PendingTotpEnrollment(
    IdMixin,
    Base,
):
    """
    Store a temporary protected TOTP secret while an MFA
    enrolment is awaiting confirmation.

    A pending enrolment exists only between:

        1. beginning authenticator setup; and
        2. successfully confirming the authenticator code.

    The pending secret must not be treated as an enabled
    MFA credential until confirmation succeeds.
    """

    __tablename__ = "pending_totp_enrollments"


    # -------------------------------------------------
    # ACCOUNT RELATIONSHIP
    # -------------------------------------------------

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        unique=True,
        index=True,
        nullable=False,
    )


    # -------------------------------------------------
    # PROTECTED TOTP SECRET
    #
    # The secret is stored in protected form while the
    # enrolment is pending. It must never be written to
    # application or audit logs.
    # -------------------------------------------------

    secret_encrypted: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )


    # -------------------------------------------------
    # ENROLMENT LIFECYCLE
    # -------------------------------------------------

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )


# =====================================================
# MFA RECOVERY CODE
# =====================================================

class MfaRecoveryCode(
    IdMixin,
    Base,
):
    """
    Store one hashed, single-use MFA recovery code.

    Plaintext recovery codes are shown to the user only
    when MFA enrolment completes. Only their hashes are
    persisted.

    Once successfully used, consumed_at is populated so
    the same recovery code cannot be reused.
    """

    __tablename__ = "mfa_recovery_codes"


    # -------------------------------------------------
    # ACCOUNT RELATIONSHIP
    # -------------------------------------------------

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )


    # -------------------------------------------------
    # HASHED RECOVERY CODE
    # -------------------------------------------------

    code_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )


    # -------------------------------------------------
    # RECOVERY-CODE LIFECYCLE
    # -------------------------------------------------

    consumed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
