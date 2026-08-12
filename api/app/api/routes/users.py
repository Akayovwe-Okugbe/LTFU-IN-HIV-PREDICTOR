from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.api.dependencies import CurrentUser, DbSession
from app.models.entities import Patient
from app.schemas.patients import PatientRead
from app.schemas.users import UserRead, UserSelfUpdateRequest
from app.services.audit import write_audit_log

router = APIRouter(prefix='/users', tags=['Users'])

@router.get('/me', response_model=UserRead)
def read_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)

@router.patch('/me', response_model=UserRead)
def update_me(payload: UserSelfUpdateRequest, db: DbSession, current_user: CurrentUser) -> UserRead:
    changes = payload.model_dump(exclude_unset=True)
    for name, value in changes.items():
        setattr(current_user, name, value)
    write_audit_log(db, actor_user_id=current_user.id, action='USER_PROFILE_UPDATED', outcome='SUCCESS', resource_type='USER', resource_id=current_user.id, details={'fields': sorted(changes)})
    db.commit(); db.refresh(current_user)
    return UserRead.model_validate(current_user)

@router.get('/me/patient', response_model=PatientRead | None)
def read_my_linked_patient(db: DbSession, current_user: CurrentUser) -> PatientRead | None:
    patient = db.scalar(select(Patient).where(Patient.linked_user_id == current_user.id))
    if patient is None:
        return None
    if not patient.is_synthetic:
        raise HTTPException(status_code=403, detail='Only synthetic patient records are permitted in this prototype.')
    return PatientRead.model_validate(patient)
