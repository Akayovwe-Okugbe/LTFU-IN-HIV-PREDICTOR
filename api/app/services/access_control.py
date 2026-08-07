"""Patient-level access helpers for MEDISCOPE Phase 3."""
from __future__ import annotations
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.enums import UserRole
from app.models.entities import ClinicianPatientAssignment, Patient, User


def clinician_has_patient_access(
    db: Session,
    *,
    clinician_user_id: UUID,
    patient_id: UUID,
) -> bool:
    """Return True when an active clinician-patient assignment exists."""
    assignment_id = db.scalar(
        select(ClinicianPatientAssignment.id).where(
            ClinicianPatientAssignment.clinician_user_id == clinician_user_id,
            ClinicianPatientAssignment.patient_id == patient_id,
            ClinicianPatientAssignment.is_active.is_(True),
        )
    )
    return assignment_id is not None


def user_can_access_patient(
    db: Session,
    *,
    user: User,
    patient: Patient,
) -> bool:
    """Evaluate patient access using role and explicit relationship."""
    if user.role == UserRole.ADMINISTRATOR.value:
        return True
    if user.role == UserRole.USER.value and patient.linked_user_id == user.id:
        return True
    if user.role == UserRole.CLINICIAN.value:
        return clinician_has_patient_access(
            db,
            clinician_user_id=user.id,
            patient_id=patient.id,
        )
    return False
