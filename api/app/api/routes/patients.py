"""
=========================================================
MEDISCOPE Patient API Routes

Purpose:
    Provide administrator-controlled synthetic patient
    creation endpoints.

Current responsibilities:
    - Create synthetic patient profiles.
    - Prevent duplicate synthetic patient numbers.
    - Optionally link a standard USER account to a patient.
    - Enforce synthetic-only data usage.
    - Audit patient creation.

Design:
    Clinician-patient assignment is intentionally NOT
    handled in this module.

    The canonical assignment API is located in:

        api/app/api/routes/administration.py

    under:

        POST /api/v1/admin/assignments

Data Governance:
    Every patient created through this API is explicitly
    marked as synthetic.

    Real patient information must not be entered into this
    prototype environment.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# FASTAPI IMPORTS
# =====================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)


# =====================================================
# SQLALCHEMY IMPORTS
# =====================================================

from sqlalchemy import select


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.api.dependencies import (
    DbSession,
    require_roles,
)

from app.core.enums import (
    UserRole,
)

from app.models.entities import (
    Patient,
    User,
)

from app.schemas.patients import (
    PatientCreate,
    PatientRead,
)

from app.services.audit import (
    write_audit_log,
)


# =====================================================
# ROUTER CONFIGURATION
# =====================================================

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)


# =====================================================
# SYNTHETIC-DATA NOTICE
# =====================================================

SYNTHETIC_NOTICE = (
    "All patient records shown in this prototype are "
    "synthetic and were created solely for demonstration "
    "and testing. They do not represent real individuals."
)


# =====================================================
# CREATE SYNTHETIC PATIENT
# =====================================================

@router.post(
    "",
    response_model=PatientRead,
    status_code=status.HTTP_201_CREATED,
)
def create_patient_shell(
    payload: PatientCreate,
    request: Request,
    db: DbSession,
    administrator: User = Depends(
        require_roles(
            UserRole.ADMINISTRATOR.value
        )
    ),
) -> PatientRead:
    """
    Create a synthetic MEDISCOPE patient profile.

    Only administrators may create patient records.

    linked_user_id is optional because a patient may be
    created before a corresponding standard USER account
    exists.
    """

    # -------------------------------------------------
    # NORMALISE SYNTHETIC PATIENT NUMBER
    # -------------------------------------------------

    synthetic_patient_number = (
        payload.synthetic_patient_number
        .strip()
    )

    # -------------------------------------------------
    # PREVENT DUPLICATE SYNTHETIC PATIENT NUMBERS
    # -------------------------------------------------

    existing_patient = db.scalar(
        select(Patient).where(
            Patient.synthetic_patient_number
            == synthetic_patient_number
        )
    )

    if existing_patient is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Synthetic patient number already exists."
            ),
        )

    # -------------------------------------------------
    # VALIDATE OPTIONAL LINKED USER
    # -------------------------------------------------

    if payload.linked_user_id is not None:

        linked_user = db.get(
            User,
            payload.linked_user_id,
        )

        if linked_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Linked user account not found.",
            )

        if (
            linked_user.role
            != UserRole.USER.value
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A patient profile may only be linked "
                    "to a standard USER account."
                ),
            )

        if linked_user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A deleted user account cannot be "
                    "linked to a patient."
                ),
            )

        # ---------------------------------------------
        # PREVENT ONE USER FROM BEING LINKED TO
        # MULTIPLE PATIENT PROFILES
        # ---------------------------------------------

        existing_link = db.scalar(
            select(Patient).where(
                Patient.linked_user_id
                == linked_user.id
            )
        )

        if existing_link is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This user account is already linked "
                    "to a patient profile."
                ),
            )

    # -------------------------------------------------
    # CREATE PATIENT
    #
    # is_synthetic is always set server-side.
    # The client is never allowed to choose whether a
    # patient is synthetic.
    # -------------------------------------------------

    patient = Patient(
        linked_user_id=payload.linked_user_id,
        synthetic_patient_number=(
            synthetic_patient_number
        ),
        first_name=(
            payload.first_name.strip()
        ),
        last_name=(
            payload.last_name.strip()
        ),
        date_of_birth=payload.date_of_birth,
        sex=payload.sex.strip(),
        state=payload.state.strip(),
        lga=payload.lga.strip(),
        is_synthetic=True,
    )

    db.add(
        patient
    )

    # Flush so the database-generated UUID is available
    # before the audit record is created.
    db.flush()

    # -------------------------------------------------
    # AUDIT PATIENT CREATION
    # -------------------------------------------------

    write_audit_log(
        db,
        actor_user_id=administrator.id,
        action="PATIENT_SHELL_CREATED",
        outcome="SUCCESS",
        resource_type="PATIENT",
        resource_id=patient.id,
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
        user_agent=request.headers.get(
            "user-agent"
        ),
        details={
            "synthetic_patient_number": (
                patient.synthetic_patient_number
            ),
            "linked_user_id": (
                str(patient.linked_user_id)
                if patient.linked_user_id
                else None
            ),
            "synthetic_data": True,
        },
    )

    db.commit()

    db.refresh(
        patient
    )

    return PatientRead.model_validate(
        patient
    )
