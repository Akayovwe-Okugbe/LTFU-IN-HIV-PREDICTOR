"""
=========================================================
MEDISCOPE Clinician Intelligence Schemas

Purpose:
    Defines read-only analytical responses used by the
    clinician dashboard and patient-intelligence views.

Important:
    These schemas expose stored analytical evidence.
    Merely opening a dashboard must never trigger new
    machine-learning predictions.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# =====================================================
# DASHBOARD SUMMARY
# =====================================================

class ClinicianDashboardSummary(BaseModel):
    assigned_patients: int

    patients_with_predictions: int

    patients_without_predictions: int

    prediction_coverage_percentage: float

    both_above_threshold: int

    model_disagreement: int

    both_below_threshold: int

    pending_prediction_reviews: int

    complete_prediction_inputs: int

    incomplete_prediction_inputs: int


# =====================================================
# PRIORITY PATIENT
# =====================================================

class ClinicianPriorityPatient(BaseModel):
    patient_id: UUID

    synthetic_patient_number: str

    first_name: str

    last_name: str

    sex: str | None = None

    state: str

    lga: str

    patient_status: str

    logistic_probability: float | None = None

    xgboost_probability: float | None = None

    logistic_classification: str | None = None

    xgboost_classification: str | None = None

    threshold: float | None = None

    agreement_status: str | None = None

    risk_state: str

    prediction_generated_at: datetime | None = None

    clinical_review_status: str | None = None

    missing_feature_count: int = 0

    missing_features: list[str] = Field(
        default_factory=list
    )


# =====================================================
# TREND POINT
# =====================================================

class ClinicianPredictionTrendPoint(BaseModel):
    period: str

    prediction_count: int

    mean_logistic_probability: float

    mean_xgboost_probability: float

    agreement_percentage: float


# =====================================================
# FEATURE COMPLETENESS
# =====================================================

class MissingFeatureSummary(BaseModel):
    feature_name: str

    missing_count: int


# =====================================================
# DASHBOARD RESPONSE
# =====================================================

class ClinicianDashboardResponse(BaseModel):
    summary: ClinicianDashboardSummary

    priority_patients: list[
        ClinicianPriorityPatient
    ]

    trend: list[
        ClinicianPredictionTrendPoint
    ]

    missing_features: list[
        MissingFeatureSummary
    ]


# =====================================================
# PATIENT / CLINICAL DETAIL
# =====================================================

class ClinicianPatientSummary(BaseModel):
    id: UUID

    synthetic_patient_number: str

    first_name: str

    last_name: str

    date_of_birth: date | None

    sex: str

    state: str

    lga: str

    status: str

    is_synthetic: bool


class ClinicianClinicalRecordResponse(BaseModel):
    id: UUID

    art_start_date: date | None

    age_at_art_initiation: float | None

    last_regimen: str | None

    days_of_arv_refill: float | None

    current_viral_load: float | None

    pregnancy_status: str | None

    last_clinic_visit_date: date | None

    notes: str | None

    created_at: datetime

    updated_at: datetime


class ClinicianPredictionHistoryItem(BaseModel):
    id: UUID

    logistic_probability: float

    logistic_classification: str

    xgboost_probability: float

    xgboost_classification: str

    agreement_status: str

    threshold_used: float

    input_schema_version: str

    input_snapshot: dict[str, Any]

    generated_at: datetime

    clinical_review_status: str


class ClinicianPatientIntelligenceResponse(BaseModel):
    patient: ClinicianPatientSummary

    latest_clinical_record: (
        ClinicianClinicalRecordResponse
        | None
    )

    clinical_history: list[
        ClinicianClinicalRecordResponse
    ]

    latest_prediction: (
        ClinicianPredictionHistoryItem
        | None
    )

    prediction_history: list[
        ClinicianPredictionHistoryItem
    ]

    missing_features: list[str]

    prediction_coverage_status: str
