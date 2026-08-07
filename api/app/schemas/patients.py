"""
=========================================================
MEDISCOPE Patient Schemas

Purpose:
    Define request and response models used by synthetic
    patient-management endpoints.

Responsibilities:
    - Validate synthetic patient creation input.
    - Represent patient records returned by the API.
    - Keep database models separate from HTTP schemas.

Design:
    Clinician-patient assignment schemas are intentionally
    not defined here.

    Assignment requests belong to the administration
    domain and are defined in:

        api/app/schemas/administration.py

Data Governance:
    MEDISCOPE currently supports synthetic patient data
    only.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

from datetime import (
    date,
    datetime,
)

from uuid import UUID


# =====================================================
# PYDANTIC IMPORTS
# =====================================================

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# =====================================================
# PATIENT CREATION REQUEST
# =====================================================

class PatientCreate(BaseModel):
    """
    Data required to create a synthetic patient.

    linked_user_id is optional because a patient may be
    created before a corresponding standard USER account
    exists.

    is_synthetic is deliberately excluded because that
    value is enforced server-side.
    """

    linked_user_id: UUID | None = None

    synthetic_patient_number: str = Field(
        min_length=3,
        max_length=50,
    )

    first_name: str = Field(
        min_length=1,
        max_length=100,
    )

    last_name: str = Field(
        min_length=1,
        max_length=100,
    )

    date_of_birth: date | None = None

    sex: str = Field(
        min_length=1,
        max_length=40,
    )

    state: str = Field(
        min_length=1,
        max_length=100,
    )

    lga: str = Field(
        min_length=1,
        max_length=150,
    )


# =====================================================
# PATIENT RESPONSE
# =====================================================

class PatientRead(PatientCreate):
    """
    Synthetic patient representation returned by the API.

    Includes database-generated identifiers, status and
    timestamps.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID

    status: str

    is_synthetic: bool

    created_at: datetime

    updated_at: datetime
