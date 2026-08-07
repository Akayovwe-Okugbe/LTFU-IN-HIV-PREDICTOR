"""Clinician-assigned patient and clinical-record APIs."""
from __future__ import annotations
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from app.api.dependencies import DbSession, require_roles
from app.core.enums import UserRole
from app.models.entities import ClinicalRecord, ClinicianPatientAssignment, Patient, User
from app.schemas.clinical import (
    ClinicalRecordCreateRequest,
    ClinicalRecordResponse,
    ClinicalRecordUpdateRequest,
    PatientSummaryResponse,
)
from app.services.access_control import clinician_has_patient_access
from app.services.audit import write_audit_log

router = APIRouter(prefix="/clinical", tags=["Clinical Records"])

ClinicianUser = Annotated[
    User,
    Depends(require_roles(UserRole.CLINICIAN.value)),
]


def _get_assigned_patient(
    db: DbSession,
    *,
    clinician: User,
    patient_id: UUID,
) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    if not patient.is_synthetic:
        raise HTTPException(status_code=403, detail="Only synthetic patient records are permitted.")
    if not clinician_has_patient_access(
        db,
        clinician_user_id=clinician.id,
        patient_id=patient.id,
    ):
        raise HTTPException(status_code=403, detail="You are not assigned to this patient.")
    return patient


@router.get("/patients", response_model=list[PatientSummaryResponse])
def list_assigned_patients(
    db: DbSession,
    current_clinician: ClinicianUser,
) -> list[Patient]:
    """Return all active synthetic patients assigned to the clinician."""
    statement = (
        select(Patient)
        .join(
            ClinicianPatientAssignment,
            ClinicianPatientAssignment.patient_id == Patient.id,
        )
        .where(
            ClinicianPatientAssignment.clinician_user_id == current_clinician.id,
            ClinicianPatientAssignment.is_active.is_(True),
            Patient.is_synthetic.is_(True),
        )
        .order_by(Patient.updated_at.desc())
    )
    return list(db.scalars(statement).all())


@router.get("/patients/{patient_id}/records", response_model=list[ClinicalRecordResponse])
def list_clinical_records(
    patient_id: UUID,
    db: DbSession,
    current_clinician: ClinicianUser,
) -> list[ClinicalRecord]:
    """Return clinical history for an assigned patient."""
    _get_assigned_patient(db, clinician=current_clinician, patient_id=patient_id)
    return list(
        db.scalars(
            select(ClinicalRecord)
            .where(ClinicalRecord.patient_id == patient_id)
            .order_by(ClinicalRecord.created_at.desc())
        ).all()
    )


@router.post("/patients/{patient_id}/records", response_model=ClinicalRecordResponse, status_code=201)
def create_clinical_record(
    patient_id: UUID,
    payload: ClinicalRecordCreateRequest,
    request: Request,
    db: DbSession,
    current_clinician: ClinicianUser,
) -> ClinicalRecord:
    """Create a clinical record for an assigned patient."""
    patient = _get_assigned_patient(
        db,
        clinician=current_clinician,
        patient_id=patient_id,
    )

    record = ClinicalRecord(
        patient_id=patient.id,
        recorded_by=current_clinician.id,
        **payload.model_dump(),
    )
    db.add(record)
    db.flush()

    write_audit_log(
        db,
        actor_user_id=current_clinician.id,
        action="CLINICAL_RECORD_CREATED",
        outcome="SUCCESS",
        resource_type="CLINICAL_RECORD",
        resource_id=record.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={"patient_id": str(patient.id)},
    )

    db.commit()
    db.refresh(record)
    return record


@router.patch("/patients/{patient_id}/records/{record_id}", response_model=ClinicalRecordResponse)
def update_clinical_record(
    patient_id: UUID,
    record_id: UUID,
    payload: ClinicalRecordUpdateRequest,
    request: Request,
    db: DbSession,
    current_clinician: ClinicianUser,
) -> ClinicalRecord:
    """Update a clinical record for an assigned patient."""
    _get_assigned_patient(db, clinician=current_clinician, patient_id=patient_id)

    record = db.get(ClinicalRecord, record_id)
    if record is None or record.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Clinical record not found.")

    changes = payload.model_dump(exclude_unset=True)
    for name, value in changes.items():
        setattr(record, name, value)

    write_audit_log(
        db,
        actor_user_id=current_clinician.id,
        action="CLINICAL_RECORD_UPDATED",
        outcome="SUCCESS",
        resource_type="CLINICAL_RECORD",
        resource_id=record.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={"patient_id": str(patient_id), "fields": sorted(changes)},
    )

    db.commit()
    db.refresh(record)
    return record
