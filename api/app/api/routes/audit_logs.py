"""
=========================================================
Administrator Audit-Log Routes

MEDISCOPE

Purpose:
    Provides administrator-only, read-only access to
    MEDISCOPE audit events.

Capabilities:
    - paginated audit directory;
    - action filtering;
    - outcome filtering;
    - resource-type filtering;
    - actor filtering;
    - date filtering;
    - text search;
    - single-event inspection;
    - audit-filter metadata.

Security:
    Every route requires the ADMINISTRATOR role.

    Audit events cannot be created, modified or deleted
    through this API.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy import (
    func,
    or_,
    select,
)

from app.api.dependencies import (
    DbSession,
    require_roles,
)

from app.core.enums import (
    UserRole,
)

from app.models.entities import (
    AuditLog,
    User,
)

from app.schemas.audit_logs import (
    AuditLogListResponse,
    AuditLogMetadataResponse,
    AuditLogResponse,
)


router = APIRouter(
    prefix="/admin/audit-logs",
    tags=[
        "Audit Logs",
    ],
)


AdminUser = Annotated[
    User,
    Depends(
        require_roles(
            UserRole.ADMINISTRATOR.value
        )
    ),
]


# =====================================================
# SERIALISE AUDIT EVENT
# =====================================================

def _audit_response(
    audit_log: AuditLog,
    actor: User | None,
) -> AuditLogResponse:
    """
    Convert an AuditLog entity and optional actor User
    into the enriched administrator response.
    """

    actor_name: str | None = None

    actor_email: str | None = None

    if actor is not None:
        actor_name = (
            f"{actor.first_name} "
            f"{actor.last_name}"
        ).strip()

        actor_email = actor.email

    return AuditLogResponse(
        id=audit_log.id,

        actor_user_id=(
            audit_log.actor_user_id
        ),

        actor_name=(
            actor_name
            or None
        ),

        actor_email=actor_email,

        action=audit_log.action,

        outcome=audit_log.outcome,

        resource_type=(
            audit_log.resource_type
        ),

        resource_id=(
            audit_log.resource_id
        ),

        ip_address=(
            audit_log.ip_address
        ),

        user_agent=(
            audit_log.user_agent
        ),

        details=(
            audit_log.details
        ),

        created_at=(
            audit_log.created_at
        ),
    )


# =====================================================
# LIST AUDIT EVENTS
# =====================================================

@router.get(
    "",
    response_model=AuditLogListResponse,
)
def list_audit_logs(
    db: DbSession,
    current_admin: AdminUser,

    search: str | None = None,

    action: str | None = None,

    outcome: str | None = None,

    resource_type: str | None = None,

    actor_user_id: UUID | None = None,

    date_from: datetime | None = None,

    date_to: datetime | None = None,

    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),

    offset: int = Query(
        default=0,
        ge=0,
    ),
) -> AuditLogListResponse:
    """
    Return a filtered and paginated audit-log directory.

    Ordering is newest-first so the administrator sees
    recent security and operational activity first.
    """

    conditions = []

    # -------------------------------------------------
    # TEXT SEARCH
    # -------------------------------------------------

    if search:
        pattern = (
            f"%{search.strip()}%"
        )

        conditions.append(
            or_(
                AuditLog.action.ilike(
                    pattern
                ),

                AuditLog.outcome.ilike(
                    pattern
                ),

                AuditLog.resource_type.ilike(
                    pattern
                ),

                User.email.ilike(
                    pattern
                ),

                User.first_name.ilike(
                    pattern
                ),

                User.last_name.ilike(
                    pattern
                ),
            )
        )

    # -------------------------------------------------
    # STRUCTURED FILTERS
    # -------------------------------------------------

    if action:
        conditions.append(
            AuditLog.action
            == action
        )

    if outcome:
        conditions.append(
            AuditLog.outcome
            == outcome
        )

    if resource_type:
        conditions.append(
            AuditLog.resource_type
            == resource_type
        )

    if actor_user_id:
        conditions.append(
            AuditLog.actor_user_id
            == actor_user_id
        )

    if date_from:
        conditions.append(
            AuditLog.created_at
            >= date_from
        )

    if date_to:
        conditions.append(
            AuditLog.created_at
            <= date_to
        )

    # -------------------------------------------------
    # TOTAL COUNT
    # -------------------------------------------------

    count_statement = (
        select(
            func.count(
                AuditLog.id
            )
        )
        .select_from(
            AuditLog
        )
        .outerjoin(
            User,
            AuditLog.actor_user_id
            == User.id,
        )
    )

    if conditions:
        count_statement = (
            count_statement.where(
                *conditions
            )
        )

    total = (
        db.scalar(
            count_statement
        )
        or 0
    )

    # -------------------------------------------------
    # PAGE QUERY
    # -------------------------------------------------

    statement = (
        select(
            AuditLog,
            User,
        )
        .outerjoin(
            User,
            AuditLog.actor_user_id
            == User.id,
        )
    )

    if conditions:
        statement = (
            statement.where(
                *conditions
            )
        )

    statement = (
        statement
        .order_by(
            AuditLog.created_at.desc()
        )
        .offset(
            offset
        )
        .limit(
            limit
        )
    )

    rows = db.execute(
        statement
    ).all()

    items = [
        _audit_response(
            audit_log,
            actor,
        )
        for (
            audit_log,
            actor,
        ) in rows
    ]

    return AuditLogListResponse(
        items=items,

        total=int(
            total
        ),

        limit=limit,

        offset=offset,
    )


# =====================================================
# FILTER METADATA
# =====================================================

@router.get(
    "/metadata",
    response_model=AuditLogMetadataResponse,
)
def audit_log_metadata(
    db: DbSession,
    current_admin: AdminUser,
) -> AuditLogMetadataResponse:
    """
    Return distinct values for audit-directory filters.
    """

    actions = list(
        db.scalars(
            select(
                AuditLog.action
            )
            .where(
                AuditLog.action.is_not(
                    None
                )
            )
            .distinct()
            .order_by(
                AuditLog.action
            )
        ).all()
    )

    outcomes = list(
        db.scalars(
            select(
                AuditLog.outcome
            )
            .where(
                AuditLog.outcome.is_not(
                    None
                )
            )
            .distinct()
            .order_by(
                AuditLog.outcome
            )
        ).all()
    )

    resource_types = list(
        db.scalars(
            select(
                AuditLog.resource_type
            )
            .where(
                AuditLog.resource_type.is_not(
                    None
                )
            )
            .distinct()
            .order_by(
                AuditLog.resource_type
            )
        ).all()
    )

    return AuditLogMetadataResponse(
        actions=[
            value
            for value in actions
            if value
        ],

        outcomes=[
            value
            for value in outcomes
            if value
        ],

        resource_types=[
            value
            for value in resource_types
            if value
        ],
    )


# =====================================================
# SINGLE AUDIT EVENT
# =====================================================

@router.get(
    "/{audit_log_id}",
    response_model=AuditLogResponse,
)
def get_audit_log(
    audit_log_id: UUID,
    db: DbSession,
    current_admin: AdminUser,
) -> AuditLogResponse:
    """
    Return one complete audit event for administrator
    review.
    """

    row = db.execute(
        select(
            AuditLog,
            User,
        )
        .outerjoin(
            User,
            AuditLog.actor_user_id
            == User.id,
        )
        .where(
            AuditLog.id
            == audit_log_id
        )
    ).first()

    if row is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Audit event not found."
            ),
        )

    audit_log, actor = row

    return _audit_response(
        audit_log,
        actor,
    )
