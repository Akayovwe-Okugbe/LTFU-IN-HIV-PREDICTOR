"""MEDISCOPE opaque refresh-token service.

Creates, rotates, revokes, and detects reuse of database-backed refresh tokens.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.auth_security import generate_url_safe_token, hash_secret
from app.models.authentication import RefreshTokenSession


class RefreshTokenError(ValueError):
    """Raised when a refresh token is invalid, expired, or reused."""


def create_refresh_token_session(
    db: Session,
    *,
    user_id: UUID,
    ip_address: str | None,
    user_agent: str | None,
    family_id: UUID | None = None,
    parent_session_id: UUID | None = None,
) -> tuple[str, RefreshTokenSession]:
    """Create an opaque refresh token and persist only its hash."""
    settings = get_settings()
    plaintext = generate_url_safe_token()
    session = RefreshTokenSession(
        user_id=user_id,
        token_hash=hash_secret(plaintext),
        family_id=family_id or uuid4(),
        parent_session_id=parent_session_id,
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.flush()
    return plaintext, session


def rotate_refresh_token(
    db: Session,
    *,
    plaintext_token: str,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[UUID, str]:
    """Rotate a valid refresh token and reject reuse of revoked tokens."""
    now = datetime.now(UTC)
    session = db.scalar(
        select(RefreshTokenSession).where(
            RefreshTokenSession.token_hash == hash_secret(plaintext_token)
        )
    )
    if session is None:
        raise RefreshTokenError("Invalid refresh token.")
    if session.revoked_at is not None:
        db.execute(
            update(RefreshTokenSession)
            .where(RefreshTokenSession.family_id == session.family_id)
            .values(revoked_at=now)
        )
        raise RefreshTokenError("Refresh token reuse detected.")
    if session.expires_at <= now:
        session.revoked_at = now
        raise RefreshTokenError("Refresh token has expired.")

    session.last_used_at = now
    session.revoked_at = now
    replacement, replacement_session = create_refresh_token_session(
        db,
        user_id=session.user_id,
        family_id=session.family_id,
        parent_session_id=session.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.replaced_by_session_id = replacement_session.id
    return session.user_id, replacement


def revoke_refresh_token(db: Session, *, plaintext_token: str) -> bool:
    """Revoke one refresh-token session."""
    session = db.scalar(
        select(RefreshTokenSession).where(
            RefreshTokenSession.token_hash == hash_secret(plaintext_token)
        )
    )
    if session is None:
        return False
    if session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
    return True


def revoke_all_user_refresh_tokens(db: Session, *, user_id: UUID) -> None:
    """Revoke every active refresh token for one account."""
    db.execute(
        update(RefreshTokenSession)
        .where(
            RefreshTokenSession.user_id == user_id,
            RefreshTokenSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
