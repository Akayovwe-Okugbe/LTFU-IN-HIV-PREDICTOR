"""
=========================================================
Administrator Audit-Log Schemas

MEDISCOPE

Purpose:
    Defines read-only response schemas for the
    administrator audit-log interface.

Security:
    Audit records are intentionally exposed as read-only
    resources. The administration API does not provide
    create, update or delete endpoints for audit events.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# =====================================================
# SINGLE AUDIT EVENT
# =====================================================

class AuditLogResponse(BaseModel):
    """
    Administrator-safe representation of one immutable
    MEDISCOPE audit event.
    """

    id: UUID

    actor_user_id: UUID | None = None

    # Human-readable actor information is supplied by
    # the audit-log query rather than requiring the
    # frontend to resolve user UUIDs separately.
    actor_name: str | None = None

    actor_email: str | None = None

    action: str

    outcome: str

    resource_type: str | None = None

    resource_id: UUID | None = None

    ip_address: str | None = None

    user_agent: str | None = None

    details: dict[str, Any] | None = None

    created_at: datetime


# =====================================================
# PAGINATED AUDIT RESPONSE
# =====================================================

class AuditLogListResponse(BaseModel):
    """
    Paginated collection returned by the audit directory.
    """

    items: list[AuditLogResponse]

    total: int

    limit: int

    offset: int


# =====================================================
# AUDIT FILTER METADATA
# =====================================================

class AuditLogMetadataResponse(BaseModel):
    """
    Distinct backend values used by frontend filters.

    This prevents React from guessing available actions,
    outcomes or resource types.
    """

    actions: list[str] = Field(
        default_factory=list
    )

    outcomes: list[str] = Field(
        default_factory=list
    )

    resource_types: list[str] = Field(
        default_factory=list
    )
