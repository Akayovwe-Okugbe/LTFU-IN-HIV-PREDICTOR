from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from app.api.dependencies import DbSession, require_roles
from app.core.enums import UserRole
from app.models.entities import ClinicianPatientAssignment, Patient, User
from app.schemas.patients import AssignmentCreate, PatientCreate, PatientRead
from app.services.audit import write_audit_log

router = APIRouter(prefix='/patients', tags=['Patients'])
SYNTHETIC_NOTICE = ('All patient records shown in this prototype are synthetic and were created '
                    'solely for demonstration and testing. They do not represent real individuals.')

@router.post('', response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient_shell(payload: PatientCreate, request: Request, db: DbSession,
                         administrator: User = Depends(require_roles(UserRole.ADMINISTRATOR.value))):
    if db.scalar(select(Patient).where(Patient.synthetic_patient_number == payload.synthetic_patient_number)):
        raise HTTPException(status_code=409, detail='Synthetic patient number already exists.')
    patient = Patient(**payload.model_dump(), is_synthetic=True)
    db.add(patient); db.flush()
    write_audit_log(db, actor_user_id=administrator.id, action='PATIENT_SHELL_CREATED',
                    outcome='SUCCESS', resource_type='PATIENT', resource_id=patient.id,
                    ip_address=request.client.host if request.client else None)
    db.commit(); db.refresh(patient)
    return PatientRead.model_validate(patient)

@router.post('/assignments', status_code=status.HTTP_201_CREATED)
def assign_clinician(payload: AssignmentCreate, request: Request, db: DbSession,
                     administrator: User = Depends(require_roles(UserRole.ADMINISTRATOR.value))):
    clinician = db.get(User, payload.clinician_user_id)
    patient = db.get(Patient, payload.patient_id)
    if clinician is None or clinician.role != UserRole.CLINICIAN.value:
        raise HTTPException(status_code=400, detail='Valid clinician required.')
    if patient is None:
        raise HTTPException(status_code=404, detail='Patient not found.')
    existing = db.scalar(select(ClinicianPatientAssignment).where(
        ClinicianPatientAssignment.clinician_user_id == clinician.id,
        ClinicianPatientAssignment.patient_id == patient.id,
        ClinicianPatientAssignment.is_active.is_(True)))
    if existing:
        raise HTTPException(status_code=409, detail='This clinician is already assigned to the patient.')
    assignment = ClinicianPatientAssignment(clinician_user_id=clinician.id,
                                            patient_id=patient.id,
                                            assigned_by=administrator.id)
    db.add(assignment); db.flush()
    write_audit_log(db, actor_user_id=administrator.id,
                    action='CLINICIAN_ASSIGNED_TO_PATIENT', outcome='SUCCESS',
                    resource_type='PATIENT', resource_id=patient.id,
                    details={'clinician_user_id': str(clinician.id)})
    db.commit()
    return {'message': 'Clinician assigned successfully.'}
