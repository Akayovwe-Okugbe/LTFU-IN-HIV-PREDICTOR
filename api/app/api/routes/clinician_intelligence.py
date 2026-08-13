"""
=========================================================
MEDISCOPE Clinician Intelligence Routes

Purpose:
    Provides read-only analytical views for clinicians.

Design rule:
    Dashboard requests NEVER generate predictions.

    They analyse predictions that have already been stored
    in the immutable predictions table.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select

from app.api.dependencies import (
    DbSession,
    require_roles,
)

from app.core.enums import UserRole

from app.models.entities import (
    ClinicalRecord,
    ClinicianPatientAssignment,
    Patient,
    Prediction,
    User,
)

from app.schemas.clinician_intelligence import (
    ClinicianClinicalRecordResponse,
    ClinicianDashboardResponse,
    ClinicianDashboardSummary,
    ClinicianPatientIntelligenceResponse,
    ClinicianPatientSummary,
    ClinicianPredictionHistoryItem,
    ClinicianPredictionTrendPoint,
    ClinicianPriorityPatient,
    MissingFeatureSummary,
)


router = APIRouter(
    prefix="/clinical/intelligence",
    tags=[
        "Clinician Intelligence",
    ],
)


ClinicianUser = Annotated[
    User,
    Depends(
        require_roles(
            UserRole.CLINICIAN.value
        )
    ),
]


# =====================================================
# HELPERS
# =====================================================

def _risk_state(
    prediction: Prediction,
) -> str:
    """
    Derive a presentation state using the actual threshold
    stored with the prediction.

    No arbitrary Low/Moderate/High probability bands are
    invented here.
    """

    logistic_above = (
        prediction.logistic_probability
        >= prediction.threshold_used
    )

    xgboost_above = (
        prediction.xgboost_probability
        >= prediction.threshold_used
    )

    if (
        logistic_above
        and xgboost_above
    ):
        return "BOTH_ABOVE_THRESHOLD"

    if (
        logistic_above
        != xgboost_above
    ):
        return "MODEL_DISAGREEMENT"

    return "BOTH_BELOW_THRESHOLD"


def _missing_snapshot_features(
    prediction: Prediction,
) -> list[str]:
    """
    Identify missing model-input values from the immutable
    prediction snapshot.
    """

    missing: list[str] = []

    for (
        name,
        value,
    ) in prediction.input_snapshot.items():

        if (
            value is None
            or value == ""
        ):
            missing.append(
                name
            )

    return sorted(
        missing
    )


def _clinical_response(
    record: ClinicalRecord,
) -> ClinicianClinicalRecordResponse:
    return ClinicianClinicalRecordResponse(
        id=record.id,

        art_start_date=(
            record.art_start_date
        ),

        age_at_art_initiation=(
            record.age_at_art_initiation
        ),

        last_regimen=(
            record.last_regimen
        ),

        days_of_arv_refill=(
            record.days_of_arv_refill
        ),

        current_viral_load=(
            record.current_viral_load
        ),

        pregnancy_status=(
            record.pregnancy_status
        ),

        last_clinic_visit_date=(
            record.last_clinic_visit_date
        ),

        notes=record.notes,

        created_at=record.created_at,

        updated_at=record.updated_at,
    )


def _prediction_response(
    prediction: Prediction,
) -> ClinicianPredictionHistoryItem:
    return ClinicianPredictionHistoryItem(
        id=prediction.id,

        logistic_probability=(
            prediction.logistic_probability
        ),

        logistic_classification=(
            prediction.logistic_classification
        ),

        xgboost_probability=(
            prediction.xgboost_probability
        ),

        xgboost_classification=(
            prediction.xgboost_classification
        ),

        agreement_status=(
            prediction.agreement_status
        ),

        threshold_used=(
            prediction.threshold_used
        ),

        input_schema_version=(
            prediction.input_schema_version
        ),

        input_snapshot=(
            prediction.input_snapshot
        ),

        generated_at=(
            prediction.generated_at
        ),

        clinical_review_status=(
            prediction.clinical_review_status
        ),
    )


# =====================================================
# CLINICIAN DASHBOARD
# =====================================================

@router.get(
    "/dashboard",
    response_model=ClinicianDashboardResponse,
)
def clinician_dashboard(
    db: DbSession,
    current_clinician: ClinicianUser,
) -> ClinicianDashboardResponse:
    """
    Build a read-only analytical summary for the current
    clinician's active patient portfolio.
    """

    # -------------------------------------------------
    # ACTIVE ASSIGNED PATIENTS
    # -------------------------------------------------

    patients = list(
        db.scalars(
            select(
                Patient
            )
            .join(
                ClinicianPatientAssignment,
                (
                    ClinicianPatientAssignment.patient_id
                    == Patient.id
                ),
            )
            .where(
                (
                    ClinicianPatientAssignment
                    .clinician_user_id
                    == current_clinician.id
                ),
                (
                    ClinicianPatientAssignment
                    .is_active
                    .is_(True)
                ),
                Patient.is_synthetic.is_(
                    True
                ),
            )
            .order_by(
                Patient.last_name,
                Patient.first_name,
            )
        ).all()
    )

    patient_ids = [
        patient.id
        for patient in patients
    ]

    if not patient_ids:
        return ClinicianDashboardResponse(
            summary=ClinicianDashboardSummary(
                assigned_patients=0,
                patients_with_predictions=0,
                patients_without_predictions=0,
                prediction_coverage_percentage=0.0,
                both_above_threshold=0,
                model_disagreement=0,
                both_below_threshold=0,
                pending_prediction_reviews=0,
                complete_prediction_inputs=0,
                incomplete_prediction_inputs=0,
            ),
            priority_patients=[],
            trend=[],
            missing_features=[],
        )

    # -------------------------------------------------
    # STORED PREDICTIONS
    # -------------------------------------------------

    all_predictions = list(
        db.scalars(
            select(
                Prediction
            )
            .where(
                Prediction.patient_id.in_(
                    patient_ids
                )
            )
            .order_by(
                Prediction.generated_at.desc()
            )
        ).all()
    )

    # Newest prediction for each patient.
    latest_predictions: dict[
        UUID,
        Prediction,
    ] = {}

    for prediction in all_predictions:
        if prediction.patient_id is None:
            continue

        latest_predictions.setdefault(
            prediction.patient_id,
            prediction,
        )

    patient_lookup = {
        patient.id: patient
        for patient in patients
    }

    # -------------------------------------------------
    # ANALYTICAL COUNTS
    # -------------------------------------------------

    both_above = 0
    disagreements = 0
    both_below = 0
    pending_reviews = 0

    complete_inputs = 0
    incomplete_inputs = 0

    missing_counter: Counter[str] = (
        Counter()
    )

    priority_rows: list[
        ClinicianPriorityPatient
    ] = []

    for patient in patients:
        prediction = (
            latest_predictions.get(
                patient.id
            )
        )

        if prediction is None:
            priority_rows.append(
                ClinicianPriorityPatient(
                    patient_id=patient.id,

                    synthetic_patient_number=(
                        patient
                        .synthetic_patient_number
                    ),

                    first_name=(
                        patient.first_name
                    ),

                    last_name=(
                        patient.last_name
                    ),

                    sex=patient.sex,

                    state=patient.state,

                    lga=patient.lga,

                    patient_status=(
                        patient.status
                    ),

                    risk_state=(
                        "NO_STORED_ASSESSMENT"
                    ),
                )
            )

            continue

        risk_state = (
            _risk_state(
                prediction
            )
        )

        if (
            risk_state
            == "BOTH_ABOVE_THRESHOLD"
        ):
            both_above += 1

        elif (
            risk_state
            == "MODEL_DISAGREEMENT"
        ):
            disagreements += 1

        else:
            both_below += 1

        if (
            prediction.clinical_review_status
            == "PENDING"
        ):
            pending_reviews += 1

        missing = (
            _missing_snapshot_features(
                prediction
            )
        )

        if missing:
            incomplete_inputs += 1

            missing_counter.update(
                missing
            )
        else:
            complete_inputs += 1

        priority_rows.append(
            ClinicianPriorityPatient(
                patient_id=patient.id,

                synthetic_patient_number=(
                    patient
                    .synthetic_patient_number
                ),

                first_name=(
                    patient.first_name
                ),

                last_name=(
                    patient.last_name
                ),

                sex=patient.sex,

                state=patient.state,

                lga=patient.lga,

                patient_status=(
                    patient.status
                ),

                logistic_probability=(
                    prediction
                    .logistic_probability
                ),

                xgboost_probability=(
                    prediction
                    .xgboost_probability
                ),

                logistic_classification=(
                    prediction
                    .logistic_classification
                ),

                xgboost_classification=(
                    prediction
                    .xgboost_classification
                ),

                threshold=(
                    prediction
                    .threshold_used
                ),

                agreement_status=(
                    prediction
                    .agreement_status
                ),

                risk_state=(
                    risk_state
                ),

                prediction_generated_at=(
                    prediction.generated_at
                ),

                clinical_review_status=(
                    prediction
                    .clinical_review_status
                ),

                missing_feature_count=(
                    len(
                        missing
                    )
                ),

                missing_features=(
                    missing
                ),
            )
        )

    # -------------------------------------------------
    # PRIORITY ORDER
    # -------------------------------------------------

    priority_rank = {
        "BOTH_ABOVE_THRESHOLD": 3,
        "MODEL_DISAGREEMENT": 2,
        "NO_STORED_ASSESSMENT": 1,
        "BOTH_BELOW_THRESHOLD": 0,
    }

    priority_rows.sort(
        key=lambda row: (
            priority_rank.get(
                row.risk_state,
                0,
            ),

            max(
                row.logistic_probability
                or 0.0,

                row.xgboost_probability
                or 0.0,
            ),
        ),
        reverse=True,
    )

    # -------------------------------------------------
    # HISTORICAL TREND
    #
    # Each point summarises STORED prediction events,
    # not unique patients.
    # -------------------------------------------------

    monthly: dict[
        str,
        list[Prediction],
    ] = defaultdict(
        list
    )

    for prediction in all_predictions:
        key = (
            prediction
            .generated_at
            .strftime(
                "%Y-%m"
            )
        )

        monthly[key].append(
            prediction
        )

    trend: list[
        ClinicianPredictionTrendPoint
    ] = []

    for period in sorted(
        monthly
    )[-6:]:
        values = monthly[
            period
        ]

        count = len(
            values
        )

        logistic_mean = (
            sum(
                item.logistic_probability
                for item in values
            )
            /
            count
        )

        xgboost_mean = (
            sum(
                item.xgboost_probability
                for item in values
            )
            /
            count
        )

        agreements = sum(
            1
            for item in values
            if (
                item.agreement_status
                .upper()
                == "AGREE"
            )
        )

        trend.append(
            ClinicianPredictionTrendPoint(
                period=period,

                prediction_count=count,

                mean_logistic_probability=round(
                    logistic_mean,
                    4,
                ),

                mean_xgboost_probability=round(
                    xgboost_mean,
                    4,
                ),

                agreement_percentage=round(
                    (
                        agreements
                        /
                        count
                    )
                    * 100,
                    1,
                ),
            )
        )

    prediction_count = len(
        latest_predictions
    )

    assigned_count = len(
        patients
    )

    coverage = (
        (
            prediction_count
            /
            assigned_count
        )
        * 100
        if assigned_count
        else 0.0
    )

    return ClinicianDashboardResponse(
        summary=ClinicianDashboardSummary(
            assigned_patients=(
                assigned_count
            ),

            patients_with_predictions=(
                prediction_count
            ),

            patients_without_predictions=(
                assigned_count
                -
                prediction_count
            ),

            prediction_coverage_percentage=round(
                coverage,
                1,
            ),

            both_above_threshold=(
                both_above
            ),

            model_disagreement=(
                disagreements
            ),

            both_below_threshold=(
                both_below
            ),

            pending_prediction_reviews=(
                pending_reviews
            ),

            complete_prediction_inputs=(
                complete_inputs
            ),

            incomplete_prediction_inputs=(
                incomplete_inputs
            ),
        ),

        priority_patients=(
            priority_rows
        ),

        trend=trend,

        missing_features=[
            MissingFeatureSummary(
                feature_name=name,

                missing_count=count,
            )
            for (
                name,
                count,
            ) in (
                missing_counter
                .most_common(
                    8
                )
            )
        ],
    )


# =====================================================
# PATIENT INTELLIGENCE
# =====================================================

@router.get(
    "/patients/{patient_id}",
    response_model=ClinicianPatientIntelligenceResponse,
)
def patient_intelligence(
    patient_id: UUID,
    db: DbSession,
    current_clinician: ClinicianUser,
) -> ClinicianPatientIntelligenceResponse:
    """
    Return comprehensive information for one patient
    actively assigned to the requesting clinician.
    """

    assignment = db.scalar(
        select(
            ClinicianPatientAssignment
        ).where(
            (
                ClinicianPatientAssignment
                .clinician_user_id
                == current_clinician.id
            ),
            (
                ClinicianPatientAssignment
                .patient_id
                == patient_id
            ),
            (
                ClinicianPatientAssignment
                .is_active
                .is_(True)
            ),
        )
    )

    if assignment is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Patient is not assigned to this clinician."
            ),
        )

    patient = db.get(
        Patient,
        patient_id,
    )

    if (
        patient is None
        or not patient.is_synthetic
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Patient not found.",
        )

    records = list(
        db.scalars(
            select(
                ClinicalRecord
            )
            .where(
                ClinicalRecord.patient_id
                == patient.id
            )
            .order_by(
                ClinicalRecord.created_at.desc()
            )
        ).all()
    )

    predictions = list(
        db.scalars(
            select(
                Prediction
            )
            .where(
                Prediction.patient_id
                == patient.id
            )
            .order_by(
                Prediction.generated_at.desc()
            )
        ).all()
    )

    latest_prediction = (
        predictions[0]
        if predictions
        else None
    )

    missing_features = (
        _missing_snapshot_features(
            latest_prediction
        )
        if latest_prediction
        else []
    )

    return ClinicianPatientIntelligenceResponse(
        patient=(
            ClinicianPatientSummary(
                id=patient.id,

                synthetic_patient_number=(
                    patient
                    .synthetic_patient_number
                ),

                first_name=(
                    patient.first_name
                ),

                last_name=(
                    patient.last_name
                ),

                date_of_birth=(
                    patient.date_of_birth
                ),

                sex=patient.sex,

                state=patient.state,

                lga=patient.lga,

                status=patient.status,

                is_synthetic=(
                    patient.is_synthetic
                ),
            )
        ),

        latest_clinical_record=(
            _clinical_response(
                records[0]
            )
            if records
            else None
        ),

        clinical_history=[
            _clinical_response(
                record
            )
            for record in records
        ],

        latest_prediction=(
            _prediction_response(
                latest_prediction
            )
            if latest_prediction
            else None
        ),

        prediction_history=[
            _prediction_response(
                prediction
            )
            for prediction in predictions
        ],

        missing_features=(
            missing_features
        ),

        prediction_coverage_status=(
            "ASSESSED"
            if latest_prediction
            else "NO_STORED_ASSESSMENT"
        ),
    )
