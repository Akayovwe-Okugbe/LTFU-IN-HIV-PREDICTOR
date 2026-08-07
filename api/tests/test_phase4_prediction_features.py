"""
=========================================================
MEDISCOPE Phase 4 Prediction Feature Tests

Purpose:
    Verify the feature-construction layer independently
    from PostgreSQL and the real trained model artifacts.

Tests:
    - preserves deployed model feature order;
    - correctly activates known categorical values;
    - handles unseen categories using Unknown columns;
    - preserves missing numeric values for fitted pipeline
      imputation.

Design:
    Tests use the typed prediction DTOs rather than
    SQLAlchemy models. This keeps the unit tests isolated
    from database persistence.

Author:
    Akayovwe Okugbe

=========================================================
"""

from datetime import date

import pandas as pd

from app.services.prediction_features import (
    ClinicalRecordFeatureInput,
    PatientFeatureInput,
    build_feature_frame,
)


# =====================================================
# FEATURE ORDER
# =====================================================

def test_feature_builder_preserves_artifact_column_order():
    """
    The generated feature frame must preserve the exact
    feature order supplied by the deployed model artifact.
    """

    patient = PatientFeatureInput(
        date_of_birth=date(
            1990,
            1,
            1,
        ),
        sex="Female",
        state="Abia",
        lga="Umuahia North",
    )

    clinical = ClinicalRecordFeatureInput(
        art_start_date=date(
            2020,
            1,
            1,
        ),
        age_at_art_initiation=30.0,
        last_regimen=(
            "TDF+3TC+DTG"
        ),
        days_of_arv_refill=90.0,
        current_viral_load=250.0,
        pregnancy_status="NP",
        last_clinic_visit_date=date(
            2026,
            7,
            1,
        ),
    )

    expected_columns = [
        "Current Age",
        "Months on ART",
        "Days Of ARV Refill",
        "Sex_M",
        "LGA_Umuahia North",
        "Last Regimen_TDF+3TC+DTG",
    ]

    (
        frame,
        snapshot,
    ) = build_feature_frame(
        expected_columns=(
            expected_columns
        ),
        patient=patient,
        clinical_record=clinical,
        prediction_date=date(
            2026,
            8,
            7,
        ),
    )

    # -------------------------------------------------
    # EXACT FEATURE ORDER
    # -------------------------------------------------

    assert (
        list(
            frame.columns
        )
        == expected_columns
    )

    # -------------------------------------------------
    # CATEGORICAL ACTIVATION
    # -------------------------------------------------

    # Female is the reference category in the fitted encoder.
    # The deployed artifact contains Sex_M only, therefore a
    # female record must leave Sex_M at zero.

    assert (
        frame.loc[
            0,
            "Sex_M",
        ]
        == 0.0
    )

    assert (
        frame.loc[
            0,
            "LGA_Umuahia North",
        ]
        == 1.0
    )

    assert (
        frame.loc[
            0,
            "Last Regimen_TDF+3TC+DTG",
        ]
        == 1.0
    )

    # -------------------------------------------------
    # NUMERIC FEATURE
    # -------------------------------------------------

    assert (
        frame.loc[
            0,
            "Days Of ARV Refill",
        ]
        == 90.0
    )

    # -------------------------------------------------
    # DERIVED TREATMENT DURATION
    # -------------------------------------------------

    assert (
        snapshot[
            "months_on_art"
        ]
        is not None
    )


# =====================================================
# UNKNOWN CATEGORY HANDLING
# =====================================================

# =====================================================
# UNKNOWN CATEGORY HANDLING
# =====================================================

def test_unseen_category_does_not_invent_model_features():
    """
    Categories that were not represented by an explicit
    Unknown column during training must not create new
    features at inference time.

    LGA and Last Regimen do not have Unknown columns in
    the deployed 141-feature schema. An unseen value must
    therefore leave the existing dummy variables at zero.
    """

    expected_columns = [
        "LGA_Umuahia North",
        "LGA_Umuahia South",
        "Last Regimen_TDF+3TC+DTG",
        "Last Regimen_AZT+3TC+DTG",
        "Current Age",
    ]

    (
        frame,
        _,
    ) = build_feature_frame(
        expected_columns=(
            expected_columns
        ),
        manual_values={
            "date_of_birth": date(
                2000,
                1,
                1,
            ),
            "lga": (
                "Never Seen LGA"
            ),
            "last_regimen": (
                "Never Seen Regimen"
            ),
            "sex": "Female",
            "state": "Abia",
        },
        prediction_date=date(
            2026,
            8,
            7,
        ),
    )

    # No known LGA feature should be activated.
    assert (
        frame.loc[
            0,
            "LGA_Umuahia North",
        ]
        == 0.0
    )

    assert (
        frame.loc[
            0,
            "LGA_Umuahia South",
        ]
        == 0.0
    )

    # No known regimen feature should be activated.
    assert (
        frame.loc[
            0,
            "Last Regimen_TDF+3TC+DTG",
        ]
        == 0.0
    )

    assert (
        frame.loc[
            0,
            "Last Regimen_AZT+3TC+DTG",
        ]
        == 0.0
    )


# =====================================================
# MISSING NUMERIC VALUES
# =====================================================

def test_missing_numeric_values_remain_nan_for_pipeline_imputation():
    """
    Missing numeric values must remain NaN.

    The already-fitted preprocessing pipeline is
    responsible for applying the imputation strategy
    learned during model training.
    """

    (
        frame,
        _,
    ) = build_feature_frame(
        expected_columns=[
            "Current Viral Load",
            "Days Of ARV Refill",
        ],
        manual_values={
            "sex": "Female",
            "state": "Abia",
            "lga": "Umuahia North",
        },
        prediction_date=date(
            2026,
            8,
            7,
        ),
    )

    assert pd.isna(
        frame.loc[
            0,
            "Current Viral Load",
        ]
    )

    assert pd.isna(
        frame.loc[
            0,
            "Days Of ARV Refill",
        ]
    )


# =====================================================
# TRAINING / SERVING CONSISTENCY
# =====================================================

def test_age_features_match_training_boundaries():
    """
    Verify age-group and binary-age features reproduce the
    original training rules.
    """

    columns = [
        "Current Age",
        "Is Child",
        "Is Adult",
        "Is Elderly",
        "Age Group_15-24",
        "Age Group_25-34",
        "Age Group_65+",
    ]

    frame, _ = build_feature_frame(
        expected_columns=columns,
        manual_values={
            "date_of_birth": date(
                2001,
                8,
                7,
            ),
            "sex": "Female",
            "state": "Abia",
            "lga": "Umuahia North",
        },
        prediction_date=date(
            2026,
            8,
            7,
        ),
    )

    # Exactly 25 years old.
    assert (
        frame.loc[
            0,
            "Current Age",
        ]
        == 25.0
    )

    assert (
        frame.loc[
            0,
            "Is Child",
        ]
        == 0.0
    )

    assert (
        frame.loc[
            0,
            "Is Adult",
        ]
        == 1.0
    )

    assert (
        frame.loc[
            0,
            "Is Elderly",
        ]
        == 0.0
    )

    assert (
        frame.loc[
            0,
            "Age Group_25-34",
        ]
        == 1.0
    )


def test_art_initiation_age_group_matches_training():
    """
    Verify the exact ART-initiation categories used during
    model training.
    """

    columns = [
        "ART Initiation Age Group_Child",
        "ART Initiation Age Group_Adult",
        "ART Initiation Age Group_Older Adult",
        "ART Initiation Age Group_Unknown",
    ]

    frame, snapshot = build_feature_frame(
        expected_columns=columns,
        manual_values={
            "sex": "Female",
            "state": "Abia",
            "lga": "Umuahia North",
            "age_at_art_initiation": 45,
        },
        prediction_date=date(
            2026,
            8,
            7,
        ),
    )

    assert (
        frame.loc[
            0,
            "ART Initiation Age Group_Older Adult",
        ]
        == 1.0
    )

    assert (
        snapshot[
            "art_initiation_age_group"
        ]
        == "Older Adult"
    )


def test_refill_category_matches_training_boundaries():
    """
    Verify the 30-day and 60-day refill boundaries from
    the training pipeline.
    """

    columns = [
        "Days Of ARV Refill",
        "ARV Refill Category_Short Refill",
        "ARV Refill Category_Medium Refill",
        "ARV Refill Category_Unknown",
    ]

    frame, snapshot = build_feature_frame(
        expected_columns=columns,
        manual_values={
            "sex": "Female",
            "state": "Abia",
            "lga": "Umuahia North",
            "days_of_arv_refill": 60,
        },
        prediction_date=date(
            2026,
            8,
            7,
        ),
    )

    assert (
        frame.loc[
            0,
            "ARV Refill Category_Medium Refill",
        ]
        == 1.0
    )

    assert (
        snapshot[
            "arv_refill_category"
        ]
        == "Medium Refill"
    )


def test_viral_load_features_match_training():
    """
    Verify missing and unsuppressed viral-load features
    reproduce the original clinical feature builder.
    """

    columns = [
        "Current Viral Load",
        "Missing Viral Load",
        "Viral Load Category_Unknown",
        "Viral Load Category_Unsuppressed",
    ]

    frame, snapshot = build_feature_frame(
        expected_columns=columns,
        manual_values={
            "sex": "Female",
            "state": "Abia",
            "lga": "Umuahia North",
            "current_viral_load": 1000,
        },
        prediction_date=date(
            2026,
            8,
            7,
        ),
    )

    assert (
        frame.loc[
            0,
            "Missing Viral Load",
        ]
        == 0.0
    )

    assert (
        frame.loc[
            0,
            "Viral Load Category_Unsuppressed",
        ]
        == 1.0
    )

    assert (
        snapshot[
            "viral_load_category"
        ]
        == "Unsuppressed"
    )


def test_months_on_art_uses_last_clinic_visit():
    """
    ART duration must use the latest clinic visit date,
    exactly as the training pipeline did, rather than the
    current system date.
    """

    columns = [
        "Months on ART",
    ]

    frame, _ = build_feature_frame(
        expected_columns=columns,
        manual_values={
            "sex": "Female",
            "state": "Abia",
            "lga": "Umuahia North",
            "art_start_date": date(
                2024,
                1,
                1,
            ),
            "last_clinic_visit_date": date(
                2025,
                1,
                1,
            ),
        },
        prediction_date=date(
            2026,
            8,
            7,
        ),
    )

    expected_months = round(
        366 / 30.44,
        1,
    )

    assert (
        frame.loc[
            0,
            "Months on ART",
        ]
        == expected_months
    )
