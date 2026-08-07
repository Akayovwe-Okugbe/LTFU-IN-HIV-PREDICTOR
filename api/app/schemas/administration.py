"""Pydantic schemas for MEDISCOPE administration APIs."""
from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class AdminUserCreateRequest(BaseModel):
    """Create a MEDISCOPE account administratively."""
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    gender: str | None = Field(default=None, max_length=40)
    role: str = Field(default="USER", max_length=40)


class AdminUserUpdateRequest(BaseModel):
    """Update non-clinical user fields."""
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=40)
    gender: str | None = Field(default=None, max_length=40)


class UserRoleUpdateRequest(BaseModel):
    """Change a user's application role."""
    role: str = Field(min_length=1, max_length=40)


class UserStatusUpdateRequest(BaseModel):
    """Change a user's account status."""
    account_status: str = Field(min_length=1, max_length=60)


class AdminUserResponse(BaseModel):
    """Administrator-safe user representation."""
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None
    gender: str | None
    role: str
    account_status: str
    email_verified_at: datetime | None
    mfa_enabled: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ClinicianAssignmentCreateRequest(BaseModel):
    """Assign a clinician to a patient."""
    clinician_user_id: UUID
    patient_id: UUID


class ClinicianAssignmentResponse(BaseModel):
    """Clinician-patient assignment response."""
    id: UUID
    clinician_user_id: UUID
    patient_id: UUID
    assigned_by: UUID
    assigned_at: datetime
    ended_at: datetime | None
    is_active: bool
    model_config = {"from_attributes": True}


# =====================================================
# PATIENT-USER LINK REQUEST
# =====================================================

class PatientUserLinkRequest(BaseModel):
    """
    Link a standard MEDISCOPE USER account to an existing
    synthetic patient profile.

    This relationship allows the user to:

    - view their linked patient profile;
    - submit permitted profile-change requests;
    - message their assigned clinicians.
    """

    user_id: UUID
