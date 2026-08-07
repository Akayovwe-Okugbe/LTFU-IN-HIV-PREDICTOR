"""MEDISCOPE Phase 4 prediction API routes."""
from __future__ import annotations
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from app.api.dependencies import DbSession, require_roles
from app.core.enums import UserRole
from app.models.entities import ModelRegistry, Patient, Prediction, User
from app.schemas.predictions import ManualPredictionRequest, ModelPredictionResult, ModelRegistryResponse, PredictionHistoryItem, PredictionResponse
from app.services.access_control import clinician_has_patient_access
from app.services.audit import write_audit_log
from app.services.model_registry import ModelRegistryError, ensure_active_model_registry
from app.services.prediction_engine import PredictionEngineError, run_two_model_prediction
router=APIRouter(prefix='/predictions',tags=['Predictions'])
ClinicianUser=Annotated[User,Depends(require_roles(UserRole.CLINICIAN.value))]

def _response(prediction: Prediction, result: dict)->PredictionResponse:
    lr=result['logistic_registry']; xgb=result['xgboost_registry']
    return PredictionResponse(prediction_id=prediction.id,patient_id=prediction.patient_id,generated_at=prediction.generated_at,logistic_regression=ModelPredictionResult(model_name=lr.model_name,model_version=lr.model_version,probability=prediction.logistic_probability,classification=prediction.logistic_classification,threshold=lr.threshold),xgboost=ModelPredictionResult(model_name=xgb.model_name,model_version=xgb.model_version,probability=prediction.xgboost_probability,classification=prediction.xgboost_classification,threshold=xgb.threshold),agreement_status=prediction.agreement_status,overall_summary=result['overall_summary'],explanation_notes=result['explanation_notes'],clinical_disclaimer=result['clinical_disclaimer'],input_schema_version=prediction.input_schema_version)

@router.post('/patients/{patient_id}',response_model=PredictionResponse,status_code=status.HTTP_201_CREATED)
def predict_patient_ltfu_risk(patient_id: UUID,request: Request,db: DbSession,current_clinician: ClinicianUser)->PredictionResponse:
    patient=db.get(Patient,patient_id)
    if patient is None: raise HTTPException(404,'Patient not found.')
    if not patient.is_synthetic: raise HTTPException(403,'Only synthetic patient records may be scored in this prototype.')
    if not clinician_has_patient_access(db,clinician_user_id=current_clinician.id,patient_id=patient.id): raise HTTPException(403,'You are not assigned to this patient.')
    try: pred,result=run_two_model_prediction(db,requested_by=current_clinician,patient=patient)
    except (PredictionEngineError,ModelRegistryError) as exc:
        db.rollback(); raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,str(exc))
    write_audit_log(db,actor_user_id=current_clinician.id,action='LTFU_PREDICTION_GENERATED',outcome='SUCCESS',resource_type='PREDICTION',resource_id=pred.id,ip_address=request.client.host if request.client else None,user_agent=request.headers.get('user-agent'),details={'patient_id':str(patient.id),'agreement_status':pred.agreement_status})
    db.commit(); db.refresh(pred); return _response(pred,result)

@router.post('/manual',response_model=PredictionResponse,status_code=status.HTTP_201_CREATED)
def predict_manual_ltfu_risk(payload: ManualPredictionRequest,request: Request,db: DbSession,current_clinician: ClinicianUser)->PredictionResponse:
    try: pred,result=run_two_model_prediction(db,requested_by=current_clinician,manual_values=payload.model_dump())
    except (PredictionEngineError,ModelRegistryError) as exc:
        db.rollback(); raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,str(exc))
    write_audit_log(db,actor_user_id=current_clinician.id,action='MANUAL_LTFU_PREDICTION_GENERATED',outcome='SUCCESS',resource_type='PREDICTION',resource_id=pred.id,ip_address=request.client.host if request.client else None,user_agent=request.headers.get('user-agent'),details={'patient_id':None,'agreement_status':pred.agreement_status})
    db.commit(); db.refresh(pred); return _response(pred,result)

@router.get('/patients/{patient_id}/history',response_model=list[PredictionHistoryItem])
def prediction_history(patient_id: UUID,db: DbSession,current_clinician: ClinicianUser)->list[Prediction]:
    patient=db.get(Patient,patient_id)
    if patient is None: raise HTTPException(404,'Patient not found.')
    if not clinician_has_patient_access(db,clinician_user_id=current_clinician.id,patient_id=patient.id): raise HTTPException(403,'You are not assigned to this patient.')
    return list(db.scalars(select(Prediction).where(Prediction.patient_id==patient.id).order_by(Prediction.generated_at.desc())).all())

@router.get('/models',response_model=list[ModelRegistryResponse])
def active_models(db: DbSession,current_clinician: ClinicianUser)->list[ModelRegistry]:
    try: ensure_active_model_registry(db)
    except ModelRegistryError as exc:
        db.rollback(); raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,str(exc))
    db.commit(); return list(db.scalars(select(ModelRegistry).where(ModelRegistry.is_active.is_(True)).order_by(ModelRegistry.model_name.asc())).all())
