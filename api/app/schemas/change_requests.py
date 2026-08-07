"""Schemas for patient-submitted change requests."""
from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class HealthRecordChangeCreateRequest(BaseModel):
    field_name: str = Field(min_length=1, max_length=150)
    proposed_value: str = Field(min_length=1, max_length=5000)
    reason: str | None = Field(default=None, max_length=5000)


class HealthRecordChangeReviewRequest(BaseModel):
    approve: bool
    review_comment: str | None = Field(default=None, max_length=5000)


class HealthRecordChangeResponse(BaseModel):
    id: UUID
    patient_id: UUID
    requested_by: UUID
    field_name: str
    previous_value: str | None
    proposed_value: str
    reason: str | None
    status: str
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    review_comment: str | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
