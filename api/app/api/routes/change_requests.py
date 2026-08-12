"""Patient change-request and clinician review endpoints."""
from __future__ import annotations
from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.api.dependencies import CurrentUser, DbSession, require_roles
from app.core.enums import ChangeRequestStatus, UserRole
from app.models.entities import HealthRecordChangeRequest, Patient, User
from app.schemas.change_requests import (
    HealthRecordChangeCreateRequest,
    HealthRecordChangeResponse,
    HealthRecordChangeReviewRequest,
)
from app.services.access_control import clinician_has_patient_access
from app.services.audit import write_audit_log

router = APIRouter(prefix="/change-requests", tags=["Clinical Records"])

ClinicianUser = Annotated[
    User,
    Depends(require_roles(UserRole.CLINICIAN.value)),
]

PATIENT_EDITABLE_FIELDS = {
    "first_name",
    "last_name",
    "date_of_birth",
    "sex",
    "state",
    "lga",
}


@router.post("", response_model=HealthRecordChangeResponse, status_code=201)
def submit_change_request(
    payload: HealthRecordChangeCreateRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> HealthRecordChangeRequest:
    """Submit a proposed change for the current user's linked patient."""
    if current_user.role != UserRole.USER.value:
        raise HTTPException(status_code=403, detail="Only standard users may submit this request.")

    patient = db.scalar(select(Patient).where(Patient.linked_user_id == current_user.id))
    if patient is None:
        raise HTTPException(status_code=404, detail="No linked patient profile exists.")
    if not patient.is_synthetic:
        raise HTTPException(status_code=403, detail="Only synthetic patient records are permitted.")
    if payload.field_name not in PATIENT_EDITABLE_FIELDS:
        raise HTTPException(
            status_code=400,
            detail="This field cannot be changed through the patient request workflow.",
        )

    previous_value = getattr(patient, payload.field_name, None)

    change_request = HealthRecordChangeRequest(
        patient_id=patient.id,
        requested_by=current_user.id,
        field_name=payload.field_name,
        previous_value=None if previous_value is None else str(previous_value),
        proposed_value=payload.proposed_value,
        reason=payload.reason,
        status=ChangeRequestStatus.PENDING.value,
    )
    db.add(change_request)
    db.flush()

    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="HEALTH_RECORD_CHANGE_REQUESTED",
        outcome="SUCCESS",
        resource_type="HEALTH_RECORD_CHANGE_REQUEST",
        resource_id=change_request.id,
        details={"field_name": payload.field_name},
    )

    db.commit()
    db.refresh(change_request)
    return change_request


@router.get("/pending", response_model=list[HealthRecordChangeResponse])
def list_pending_change_requests(
    db: DbSession,
    current_clinician: ClinicianUser,
) -> list[HealthRecordChangeRequest]:
    """List pending requests for patients assigned to the clinician."""
    pending = list(
        db.scalars(
            select(HealthRecordChangeRequest)
            .where(HealthRecordChangeRequest.status == ChangeRequestStatus.PENDING.value)
            .order_by(HealthRecordChangeRequest.created_at.asc())
        ).all()
    )

    return [
        item
        for item in pending
        if clinician_has_patient_access(
            db,
            clinician_user_id=current_clinician.id,
            patient_id=item.patient_id,
        )
    ]


@router.post("/{request_id}/review", response_model=HealthRecordChangeResponse)
def review_change_request(
    request_id: UUID,
    payload: HealthRecordChangeReviewRequest,
    db: DbSession,
    current_clinician: ClinicianUser,
) -> HealthRecordChangeRequest:
    """Approve or reject an assigned patient's pending request."""
    item = db.get(HealthRecordChangeRequest, request_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Change request not found.")
    if item.status != ChangeRequestStatus.PENDING.value:
        raise HTTPException(status_code=409, detail="Change request has already been reviewed.")
    if not clinician_has_patient_access(
        db,
        clinician_user_id=current_clinician.id,
        patient_id=item.patient_id,
    ):
        raise HTTPException(status_code=403, detail="You are not assigned to this patient.")

    patient = db.get(Patient, item.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")

    if payload.approve:
        if item.field_name == "date_of_birth":
            try:
                value = date.fromisoformat(item.proposed_value)
            except ValueError:
                raise HTTPException(status_code=400, detail="Date of birth must use YYYY-MM-DD format.")
        else:
            value = item.proposed_value

        setattr(patient, item.field_name, value)
        item.status = ChangeRequestStatus.APPROVED.value
        action = "HEALTH_RECORD_CHANGE_APPROVED"
    else:
        item.status = ChangeRequestStatus.REJECTED.value
        action = "HEALTH_RECORD_CHANGE_REJECTED"

    item.reviewed_by = current_clinician.id
    item.reviewed_at = datetime.now(UTC)
    item.review_comment = payload.review_comment

    write_audit_log(
        db,
        actor_user_id=current_clinician.id,
        action=action,
        outcome="SUCCESS",
        resource_type="HEALTH_RECORD_CHANGE_REQUEST",
        resource_id=item.id,
        details={"patient_id": str(item.patient_id), "field_name": item.field_name},
    )

    db.commit()
    db.refresh(item)
    return item


@router.get('/mine', response_model=list[HealthRecordChangeResponse])
def list_my_change_requests(db: DbSession, current_user: CurrentUser) -> list[HealthRecordChangeRequest]:
    """Return the current standard user's own change requests, newest first."""
    if current_user.role != UserRole.USER.value:
        raise HTTPException(status_code=403, detail='Only standard users have personal health-record change requests.')
    return list(db.scalars(select(HealthRecordChangeRequest).where(HealthRecordChangeRequest.requested_by == current_user.id).order_by(HealthRecordChangeRequest.created_at.desc())).all())
