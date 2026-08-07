"""
=========================================================
MEDISCOPE Two-Model Prediction Engine

Purpose:
    Run and persist MEDISCOPE's selected Logistic
    Regression and XGBoost LTFU prediction models.

Responsibilities:
    - Load and cache trained model artifacts.
    - Validate deployed feature schemas.
    - Convert SQLAlchemy models into prediction DTOs.
    - Construct model-ready feature frames.
    - Generate positive-class probabilities.
    - Apply deployment thresholds.
    - Compare model classifications.
    - Persist prediction history.
    - Return clinician-friendly interpretation metadata.

Clinical Safety:
    Predictions provide decision support only.

    They are not diagnoses and must not be used to make
    autonomous treatment, discharge, or retention
    decisions.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import UUID


# =====================================================
# THIRD-PARTY IMPORTS
# =====================================================

import joblib
import numpy as np

from sqlalchemy import select
from sqlalchemy.orm import Session


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.models.entities import (
    ClinicalRecord,
    Patient,
    Prediction,
    User,
)

from app.services.model_registry import (
    FEATURE_SCHEMA_VERSION,
    ensure_active_model_registry,
)

from app.services.prediction_features import (
    ClinicalRecordFeatureInput,
    PatientFeatureInput,
    PredictionFeatureError,
    build_feature_frame,
)


# =====================================================
# CLINICAL DISCLAIMER
# =====================================================

CLINICAL_DISCLAIMER = (
    "MEDISCOPE provides decision-support risk estimates "
    "only. The prediction is not a diagnosis and must not "
    "be used as an autonomous treatment or discharge "
    "decision."
)


# =====================================================
# CUSTOM EXCEPTION
# =====================================================

class PredictionEngineError(RuntimeError):
    """
    Raised when the deployed prediction workflow cannot
    execute safely.
    """


# =====================================================
# MODEL LOADING
# =====================================================

@lru_cache(
    maxsize=4
)
def _load_pipeline(
    path: str,
) -> Any:
    """
    Load and cache a trained prediction pipeline.
    """

    model_path = Path(
        path
    )

    if not model_path.exists():
        raise PredictionEngineError(
            "Model artifact could not be found: "
            f"{model_path}"
        )

    return joblib.load(
        model_path
    )


# =====================================================
# DEPLOYED FEATURE SCHEMA
# =====================================================

def _feature_names(
    model: Any,
) -> list[str]:
    """
    Retrieve the exact feature names and order expected by
    a fitted model artifact.
    """

    names = getattr(
        model,
        "feature_names_in_",
        None,
    )

    if names is None:
        raise PredictionEngineError(
            "Deployed model does not expose "
            "feature_names_in_."
        )

    return [
        str(name)
        for name
        in names
    ]


# =====================================================
# POSITIVE-CLASS PROBABILITY
# =====================================================

def _probability(
    model: Any,
    frame: Any,
) -> float:
    """
    Return probability of the positive LTFU class.
    """

    probabilities = model.predict_proba(
        frame
    )

    if (
        len(
            probabilities.shape
        )
        != 2
        or probabilities.shape[1]
        < 2
    ):
        raise PredictionEngineError(
            "Classifier does not expose a valid "
            "positive-class probability."
        )

    return float(
        probabilities[
            0,
            1,
        ]
    )


# =====================================================
# CLASSIFICATION
# =====================================================

def _classify(
    probability: float,
    threshold: float,
) -> str:
    """
    Convert a probability into the MEDISCOPE display
    classification.
    """

    if (
        probability
        >= threshold
    ):
        return "AT_RISK_OF_LTFU"

    return "LOWER_LTFU_RISK"


# =====================================================
# LATEST CLINICAL RECORD
# =====================================================

def _latest_record(
    db: Session,
    patient_id: UUID,
) -> ClinicalRecord:
    """
    Retrieve the patient's most recently updated clinical
    record.
    """

    record = db.scalar(
        select(
            ClinicalRecord
        )
        .where(
            ClinicalRecord.patient_id
            == patient_id
        )
        .order_by(
            ClinicalRecord.updated_at.desc(),
            ClinicalRecord.created_at.desc(),
        )
    )

    if record is None:
        raise PredictionEngineError(
            "This patient does not yet have a "
            "clinical record."
        )

    return record


# =====================================================
# BUILD PATIENT FEATURE INPUT
# =====================================================

def _patient_feature_input(
    patient: Patient | None,
) -> PatientFeatureInput | None:
    """
    Convert the SQLAlchemy Patient entity into the
    prediction-layer DTO.

    patient_transferred_in is read dynamically so Phase 4
    remains compatible with the current database schema.
    If the field is not yet persisted, None is supplied.
    """

    if patient is None:
        return None

    transferred_in = getattr(
        patient,
        "patient_transferred_in",
        None,
    )

    return PatientFeatureInput(
        date_of_birth=(
            patient.date_of_birth
        ),
        sex=patient.sex,
        state=patient.state,
        lga=patient.lga,
        patient_transferred_in=(
            transferred_in
            if isinstance(
                transferred_in,
                bool,
            )
            else None
        ),
    )


# =====================================================
# BUILD CLINICAL FEATURE INPUT
# =====================================================

def _clinical_feature_input(
    clinical_record: ClinicalRecord | None,
) -> ClinicalRecordFeatureInput | None:
    """
    Convert a SQLAlchemy ClinicalRecord model into the
    prediction-layer DTO.
    """

    if clinical_record is None:
        return None

    return ClinicalRecordFeatureInput(
        art_start_date=(
            clinical_record.art_start_date
        ),
        age_at_art_initiation=(
            clinical_record
            .age_at_art_initiation
        ),
        last_regimen=(
            clinical_record.last_regimen
        ),
        days_of_arv_refill=(
            clinical_record
            .days_of_arv_refill
        ),
        current_viral_load=(
            clinical_record
            .current_viral_load
        ),
        pregnancy_status=(
            clinical_record
            .pregnancy_status
        ),
        last_clinic_visit_date=(
            clinical_record
            .last_clinic_visit_date
        ),
    )


# =====================================================
# BUILD CLINICIAN SUMMARY
# =====================================================

def _build_summary(
    *,
    agreement: str,
    logistic_classification: str,
    logistic_probability: float,
    xgboost_probability: float,
) -> str:
    """
    Produce a concise clinician-facing prediction summary.
    """

    if (
        agreement == "AGREE"
        and logistic_classification
        == "AT_RISK_OF_LTFU"
    ):
        return (
            "Both deployed models flag increased LTFU "
            "risk. Consider clinical review and "
            "appropriate retention-support prioritisation."
        )

    if agreement == "AGREE":
        return (
            "Both deployed models place this record below "
            "the configured LTFU risk threshold. Continue "
            "routine clinical review and monitoring."
        )

    highest_probability = max(
        logistic_probability,
        xgboost_probability,
    )

    return (
        "The deployed models disagree at the "
        "classification threshold. The higher estimated "
        f"LTFU probability is {highest_probability:.1%}; "
        "review the patient context rather than relying "
        "on either classification alone."
    )


# =====================================================
# BUILD EXPLANATION NOTES
# =====================================================

def _build_explanation_notes(
    *,
    snapshot: dict[str, Any],
    logistic_probability: float,
    xgboost_probability: float,
) -> list[str]:
    """
    Generate transparent context notes for clinicians.

    These notes describe model inputs and outputs only.
    They must not be interpreted as causal explanations.
    """

    notes = [
        (
            "Logistic Regression positive-class "
            f"probability: {logistic_probability:.1%}."
        ),
        (
            "XGBoost positive-class probability: "
            f"{xgboost_probability:.1%}."
        ),
    ]

    current_age = snapshot.get(
        "current_age"
    )

    if isinstance(
        current_age,
        (int, float),
    ):
        notes.append(
            "Current age supplied to the model: "
            f"{float(current_age):.0f} years."
        )

    months_on_art = snapshot.get(
        "months_on_art"
    )

    if isinstance(
        months_on_art,
        (int, float),
    ):
        notes.append(
            "Calculated treatment duration: "
            f"{float(months_on_art):.0f} months on ART."
        )

    refill_days = snapshot.get(
        "days_of_arv_refill"
    )

    if isinstance(
        refill_days,
        (int, float),
    ):
        notes.append(
            "Recorded ARV refill duration: "
            f"{float(refill_days):.0f} days."
        )

    viral_load = snapshot.get(
        "current_viral_load"
    )

    if isinstance(
        viral_load,
        (int, float),
    ):
        notes.append(
            "Recorded current viral load supplied to "
            f"the model: {float(viral_load):.0f}."
        )

    last_regimen = snapshot.get(
        "last_regimen"
    )

    if last_regimen:
        notes.append(
            "Recorded regimen supplied to the model: "
            f"{last_regimen}."
        )

    notes.append(
        "These notes describe model inputs and outputs; "
        "they do not establish that any individual "
        "feature caused the predicted risk."
    )

    return notes


# =====================================================
# RUN TWO-MODEL PREDICTION
# =====================================================

def run_two_model_prediction(
    db: Session,
    *,
    requested_by: User,
    patient: Patient | None = None,
    manual_values: dict[str, Any] | None = None,
) -> tuple[
    Prediction,
    dict[str, Any],
]:
    """
    Run Logistic Regression and XGBoost against one
    prediction record and persist the result.
    """

    # -------------------------------------------------
    # ENSURE MODEL REGISTRY ENTRIES EXIST
    # -------------------------------------------------

    (
        logistic_registry,
        xgboost_registry,
    ) = ensure_active_model_registry(
        db
    )

    # -------------------------------------------------
    # LOAD MODEL ARTIFACTS
    # -------------------------------------------------

    logistic_model = _load_pipeline(
        logistic_registry.artifact_path
    )

    xgboost_model = _load_pipeline(
        xgboost_registry.artifact_path
    )

    # -------------------------------------------------
    # VALIDATE FEATURE SCHEMAS
    # -------------------------------------------------

    logistic_columns = _feature_names(
        logistic_model
    )

    xgboost_columns = _feature_names(
        xgboost_model
    )

    if (
        logistic_columns
        != xgboost_columns
    ):
        raise PredictionEngineError(
            "The active Logistic Regression and XGBoost "
            "models do not use the same deployed input "
            "schema."
        )

    # -------------------------------------------------
    # RETRIEVE LATEST CLINICAL RECORD WHEN USING A
    # STORED PATIENT
    # -------------------------------------------------

    clinical_record = (
        _latest_record(
            db,
            patient.id,
        )
        if patient is not None
        else None
    )

    # -------------------------------------------------
    # CONVERT ORM MODELS INTO PREDICTION DTOs
    # -------------------------------------------------

    patient_input = (
        _patient_feature_input(
            patient
        )
    )

    clinical_input = (
        _clinical_feature_input(
            clinical_record
        )
    )

    # -------------------------------------------------
    # BUILD MODEL-READY FEATURE FRAME
    # -------------------------------------------------

    try:

        (
            frame,
            snapshot,
        ) = build_feature_frame(
            expected_columns=(
                logistic_columns
            ),
            patient=patient_input,
            clinical_record=(
                clinical_input
            ),
            manual_values=manual_values,
        )

    except PredictionFeatureError as exc:
        raise PredictionEngineError(
            str(exc)
        ) from exc

    # -------------------------------------------------
    # GENERATE PROBABILITIES
    # -------------------------------------------------

    logistic_probability = (
        _probability(
            logistic_model,
            frame,
        )
    )

    xgboost_probability = (
        _probability(
            xgboost_model,
            frame,
        )
    )

    # -------------------------------------------------
    # VERIFY THRESHOLD COMPATIBILITY
    #
    # The current Prediction table stores one shared
    # threshold, so both active models must currently use
    # the same deployment threshold.
    # -------------------------------------------------

    if not np.isclose(
        logistic_registry.threshold,
        xgboost_registry.threshold,
    ):
        raise PredictionEngineError(
            "Active models use different thresholds but "
            "prediction history currently stores one "
            "shared threshold."
        )

    # -------------------------------------------------
    # CLASSIFY BOTH MODELS
    # -------------------------------------------------

    logistic_classification = (
        _classify(
            logistic_probability,
            logistic_registry.threshold,
        )
    )

    xgboost_classification = (
        _classify(
            xgboost_probability,
            xgboost_registry.threshold,
        )
    )

    agreement = (
        "AGREE"
        if logistic_classification
        == xgboost_classification
        else "DISAGREE"
    )

    # -------------------------------------------------
    # CLINICIAN-FACING INTERPRETATION
    # -------------------------------------------------

    summary = _build_summary(
        agreement=agreement,
        logistic_classification=(
            logistic_classification
        ),
        logistic_probability=(
            logistic_probability
        ),
        xgboost_probability=(
            xgboost_probability
        ),
    )

    explanation_notes = (
        _build_explanation_notes(
            snapshot=snapshot,
            logistic_probability=(
                logistic_probability
            ),
            xgboost_probability=(
                xgboost_probability
            ),
        )
    )

    # -------------------------------------------------
    # PERSIST PREDICTION HISTORY
    # -------------------------------------------------

    prediction = Prediction(
        patient_id=(
            patient.id
            if patient is not None
            else None
        ),
        requested_by=requested_by.id,
        logistic_model_id=(
            logistic_registry.id
        ),
        xgboost_model_id=(
            xgboost_registry.id
        ),
        logistic_probability=(
            logistic_probability
        ),
        logistic_classification=(
            logistic_classification
        ),
        xgboost_probability=(
            xgboost_probability
        ),
        xgboost_classification=(
            xgboost_classification
        ),
        agreement_status=agreement,
        threshold_used=(
            logistic_registry.threshold
        ),
        input_schema_version=(
            FEATURE_SCHEMA_VERSION
        ),
        input_snapshot=snapshot,
    )

    db.add(
        prediction
    )

    # Flush so the generated UUID is available to route
    # audit logging before the surrounding transaction is
    # committed.
    db.flush()

    # -------------------------------------------------
    # RETURN PERSISTED OBJECT + RESPONSE METADATA
    # -------------------------------------------------

    return (
        prediction,
        {
            "logistic_registry": (
                logistic_registry
            ),
            "xgboost_registry": (
                xgboost_registry
            ),
            "overall_summary": summary,
            "explanation_notes": (
                explanation_notes
            ),
            "clinical_disclaimer": (
                CLINICAL_DISCLAIMER
            ),
        },
    )
