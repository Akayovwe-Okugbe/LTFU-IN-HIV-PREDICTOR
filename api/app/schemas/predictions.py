"""MEDISCOPE Phase 4 prediction request/response schemas."""
from __future__ import annotations
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field

class ManualPredictionRequest(BaseModel):
    """Synthetic values required for an ad-hoc LTFU prediction."""
    date_of_birth: date | None = None
    sex: str = Field(min_length=1, max_length=40)
    state: str = Field(min_length=1, max_length=100)
    lga: str = Field(min_length=1, max_length=150)
    patient_transferred_in: bool | None = None
    art_start_date: date | None = None
    age_at_art_initiation: float | None = Field(default=None, ge=0, le=150)
    last_regimen: str | None = Field(default=None, max_length=200)
    days_of_arv_refill: float | None = Field(default=None, ge=0)
    current_viral_load: float | None = Field(default=None, ge=0)
    pregnancy_status: str | None = Field(default=None, max_length=100)
    last_clinic_visit_date: date | None = None

class ModelPredictionResult(BaseModel):
    model_name: str
    model_version: str
    probability: float = Field(ge=0, le=1)
    classification: str
    threshold: float = Field(ge=0, le=1)

class PredictionResponse(BaseModel):
    prediction_id: UUID
    patient_id: UUID | None
    generated_at: datetime
    logistic_regression: ModelPredictionResult
    xgboost: ModelPredictionResult
    agreement_status: str
    overall_summary: str
    explanation_notes: list[str]
    clinical_disclaimer: str
    input_schema_version: str

class PredictionHistoryItem(BaseModel):
    id: UUID
    patient_id: UUID | None
    requested_by: UUID
    logistic_probability: float
    logistic_classification: str
    xgboost_probability: float
    xgboost_classification: str
    agreement_status: str
    threshold_used: float
    input_schema_version: str
    generated_at: datetime
    model_config = {'from_attributes': True}

class ModelRegistryResponse(BaseModel):
    id: UUID
    model_name: str
    model_version: str
    algorithm: str
    trained_at: datetime
    threshold: float
    feature_schema_version: str
    evaluation_metrics: dict
    is_active: bool
    model_config = {'from_attributes': True}
