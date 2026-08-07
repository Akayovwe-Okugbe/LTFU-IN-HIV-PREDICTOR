"""Pydantic schemas for MEDISCOPE clinical APIs."""
from __future__ import annotations
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field


class PatientSummaryResponse(BaseModel):
    """Clinical-facing patient summary."""
    id: UUID
    synthetic_patient_number: str
    first_name: str
    last_name: str
    date_of_birth: date | None
    sex: str
    state: str
    lga: str
    status: str
    is_synthetic: bool
    updated_at: datetime
    model_config = {"from_attributes": True}


class ClinicalRecordCreateRequest(BaseModel):
    """Create a clinical record."""
    art_start_date: date | None = None
    age_at_art_initiation: float | None = Field(default=None, ge=0, le=150)
    last_regimen: str | None = Field(default=None, max_length=200)
    days_of_arv_refill: float | None = Field(default=None, ge=0)
    current_viral_load: float | None = Field(default=None, ge=0)
    pregnancy_status: str | None = Field(default=None, max_length=100)
    last_clinic_visit_date: date | None = None
    notes: str | None = Field(default=None, max_length=5000)


class ClinicalRecordUpdateRequest(BaseModel):
    """Update a clinical record."""
    art_start_date: date | None = None
    age_at_art_initiation: float | None = Field(default=None, ge=0, le=150)
    last_regimen: str | None = Field(default=None, max_length=200)
    days_of_arv_refill: float | None = Field(default=None, ge=0)
    current_viral_load: float | None = Field(default=None, ge=0)
    pregnancy_status: str | None = Field(default=None, max_length=100)
    last_clinic_visit_date: date | None = None
    notes: str | None = Field(default=None, max_length=5000)


class ClinicalRecordResponse(BaseModel):
    """Clinical record returned to an authorised clinician."""
    id: UUID
    patient_id: UUID
    recorded_by: UUID
    art_start_date: date | None
    age_at_art_initiation: float | None
    last_regimen: str | None
    days_of_arv_refill: float | None
    current_viral_load: float | None
    pregnancy_status: str | None
    last_clinic_visit_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
