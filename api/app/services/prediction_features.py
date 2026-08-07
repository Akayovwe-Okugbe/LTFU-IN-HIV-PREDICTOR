"""
=========================================================
MEDISCOPE Prediction Feature Builder

Purpose:
    Reproduce the feature-engineering rules used during
    model training and construct model-ready feature rows.

Design:
    This module is deliberately independent of SQLAlchemy.

    Database entities are converted into small typed data
    objects before entering the prediction layer.

Training / Serving Consistency:
    The transformations implemented here mirror the
    original feature builders under:

        src/feature_builders/

    including:
        - demographic age groups;
        - age indicator flags;
        - ART initiation age categories;
        - months on ART;
        - viral-load categories;
        - missing viral-load indicators;
        - ARV refill categories;
        - transfer-in status.

Important:
    The fitted model artifact remains the source of truth
    for feature names and feature order.

    Features that were completely unavailable in the
    source dataset, such as the Q3 status variables, remain
    NaN and are handled by the fitted preprocessing
    pipeline.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Sequence


# =====================================================
# THIRD-PARTY IMPORTS
# =====================================================

import numpy as np
import pandas as pd


# =====================================================
# TYPED PREDICTION INPUT OBJECTS
# =====================================================

@dataclass(frozen=True)
class PatientFeatureInput:
    """
    Patient-level values required by feature engineering.

    patient_transferred_in is optional because the current
    MEDISCOPE patient table may not yet persist this field.
    """

    date_of_birth: date | None
    sex: str | None
    state: str | None
    lga: str | None
    patient_transferred_in: bool | None = None


@dataclass(frozen=True)
class ClinicalRecordFeatureInput:
    """
    Clinical values required by feature engineering.
    """

    art_start_date: date | None
    age_at_art_initiation: float | None
    last_regimen: str | None
    days_of_arv_refill: float | None
    current_viral_load: float | None
    pregnancy_status: str | None
    last_clinic_visit_date: date | None


# =====================================================
# CUSTOM EXCEPTION
# =====================================================

class PredictionFeatureError(ValueError):
    """Raised when prediction features cannot be built."""


# =====================================================
# AGE CALCULATION
# =====================================================

def _age_in_years(
    birth_date: date | None,
    *,
    as_of: date,
) -> float | None:
    """
    Calculate age in completed years.
    """

    if birth_date is None:
        return None

    years = (
        as_of.year
        - birth_date.year
    )

    if (
        as_of.month,
        as_of.day,
    ) < (
        birth_date.month,
        birth_date.day,
    ):
        years -= 1

    # Negative ages are invalid.
    if years < 0:
        return None

    return float(years)


# =====================================================
# AGE GROUP
#
# Mirrors:
# src/feature_builders/demographics.py
# create_age_groups()
# =====================================================

def _age_group(
    age: float | None,
) -> str | None:
    """
    Reproduce the training age-group categories.
    """

    if age is None:
        return None

    if age < 0 or age >= 150:
        return None

    if age < 15:
        return "0-14"

    if age < 25:
        return "15-24"

    if age < 35:
        return "25-34"

    if age < 45:
        return "35-44"

    if age < 55:
        return "45-54"

    if age < 65:
        return "55-64"

    return "65+"


# =====================================================
# ART INITIATION AGE GROUP
#
# Mirrors:
# create_art_initiation_age_group()
# =====================================================

def _art_initiation_age_group(
    age: float | None,
) -> str:
    """
    Reproduce the exact training categories.

    Training boundaries:
        <15     -> Child
        15-24   -> Adolescent/Young Adult
        25-44   -> Adult
        45-100  -> Older Adult
        missing/invalid -> Unknown
    """

    if (
        age is None
        or age < 0
        or age > 100
    ):
        return "Unknown"

    if age < 15:
        return "Child"

    if age < 25:
        return "Adolescent/Young Adult"

    if age < 45:
        return "Adult"

    return "Older Adult"


# =====================================================
# ARV REFILL CATEGORY
#
# Mirrors:
# create_arv_refill_category()
# =====================================================

def _arv_refill_category(
    days: float | None,
) -> str:
    """
    Reproduce the exact training refill categories.

    Training boundaries:
        <=30   -> Short Refill
        31-60  -> Medium Refill
        >60    -> Long Refill
        missing/invalid -> Unknown
    """

    if (
        days is None
        or days < 0
    ):
        return "Unknown"

    if days <= 30:
        return "Short Refill"

    if days <= 60:
        return "Medium Refill"

    return "Long Refill"


# =====================================================
# VIRAL LOAD CATEGORY
#
# Mirrors:
# create_viral_load_category()
# =====================================================

def _viral_load_category(
    viral_load: float | None,
) -> str:
    """
    Reproduce the training viral-load classification.

        missing -> Unknown
        <1000   -> Suppressed
        >=1000  -> Unsuppressed
    """

    if viral_load is None:
        return "Unknown"

    if viral_load < 1000:
        return "Suppressed"

    return "Unsuppressed"


# =====================================================
# MONTHS ON ART
#
# Mirrors:
# create_art_duration()
#
# Training used:
#
# (Last Clinic Visit Date - ART Start Date).days / 30.44
#
# rounded to one decimal place.
# =====================================================

def _months_on_art(
    *,
    art_start_date: date | None,
    last_clinic_visit_date: date | None,
) -> float | None:
    """
    Calculate ART duration exactly as training did.
    """

    if (
        art_start_date is None
        or last_clinic_visit_date is None
    ):
        return None

    day_difference = (
        last_clinic_visit_date
        - art_start_date
    ).days

    if day_difference < 0:
        return None

    return round(
        day_difference / 30.44,
        1,
    )


# =====================================================
# NUMERIC FEATURE HELPER
# =====================================================

def _set_if_expected(
    values: dict[str, float],
    expected: set[str],
    name: str,
    value: float | int | None,
) -> None:
    """
    Populate a numeric feature only when the model expects
    that feature.
    """

    if (
        name in expected
        and value is not None
    ):
        values[name] = float(value)


# =====================================================
# ONE-HOT FEATURE HELPER
# =====================================================

def _activate_category(
    values: dict[str, float],
    expected: set[str],
    prefix: str,
    category: str | None,
) -> None:
    """
    Activate a fitted one-hot encoded category.

    Categories not represented in the artifact remain all
    zero, which corresponds to the encoder's reference
    category.
    """

    if not category:
        return

    feature_name = (
        f"{prefix}_{category}"
    )

    if feature_name in expected:
        values[feature_name] = 1.0


# =====================================================
# BOOLEAN NORMALISATION
# =====================================================

def _normalise_transfer_in(
    value: Any,
) -> bool | None:
    """
    Convert common transfer-in representations to bool.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()

    if text in {
        "yes",
        "true",
        "1",
        "y",
    }:
        return True

    if text in {
        "no",
        "false",
        "0",
        "n",
    }:
        return False

    return None


# =====================================================
# FEATURE FRAME BUILDER
# =====================================================

def build_feature_frame(
    *,
    expected_columns: Sequence[str],
    patient: PatientFeatureInput | None = None,
    clinical_record: ClinicalRecordFeatureInput | None = None,
    manual_values: dict[str, Any] | None = None,
    prediction_date: date | None = None,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    """
    Build one feature row in the exact order expected by
    the deployed model.
    """

    if not expected_columns:
        raise PredictionFeatureError(
            "The deployed model does not expose "
            "feature_names_in_."
        )

    today = (
        prediction_date
        or datetime.now(UTC).date()
    )

    expected = {
        str(column)
        for column
        in expected_columns
    }

    # -------------------------------------------------
    # INITIALISE FEATURES
    #
    # Numeric and genuinely missing features start as NaN
    # so the fitted preprocessing pipeline can apply the
    # same imputation behaviour learned during training.
    # -------------------------------------------------

    values: dict[str, float] = {
        str(column): np.nan
        for column
        in expected_columns
    }

    # -------------------------------------------------
    # INITIALISE ONE-HOT FEATURES TO ZERO
    # -------------------------------------------------

    one_hot_prefixes = (
        "State_",
        "LGA_",
        "Sex_",
        "Age Group_",
        "ART Initiation Age Group_",
        "Pregnancy Status_",
        "ARV Refill Category_",
        "Last Regimen_",
        "Patient Transferred In_",
        "Viral Load Category_",
    )

    for column in expected_columns:

        column_name = str(column)

        if column_name.startswith(
            one_hot_prefixes
        ):
            values[column_name] = 0.0

    # -------------------------------------------------
    # COMBINE INPUT SOURCES
    # -------------------------------------------------

    source: dict[str, Any] = {}

    if patient is not None:

        source.update(
            {
                "date_of_birth": (
                    patient.date_of_birth
                ),
                "sex": patient.sex,
                "state": patient.state,
                "lga": patient.lga,
                "patient_transferred_in": (
                    patient.patient_transferred_in
                ),
            }
        )

    if clinical_record is not None:

        source.update(
            {
                "art_start_date": (
                    clinical_record.art_start_date
                ),
                "age_at_art_initiation": (
                    clinical_record
                    .age_at_art_initiation
                ),
                "last_regimen": (
                    clinical_record.last_regimen
                ),
                "days_of_arv_refill": (
                    clinical_record
                    .days_of_arv_refill
                ),
                "current_viral_load": (
                    clinical_record
                    .current_viral_load
                ),
                "pregnancy_status": (
                    clinical_record
                    .pregnancy_status
                ),
                "last_clinic_visit_date": (
                    clinical_record
                    .last_clinic_visit_date
                ),
            }
        )

    # Manual prediction values deliberately override any
    # existing values.
    if manual_values:
        source.update(
            manual_values
        )

    # =================================================
    # BASIC SOURCE VALUE NORMALISATION
    # =================================================

    birth_date_raw = source.get(
        "date_of_birth"
    )

    birth_date = (
        birth_date_raw
        if isinstance(
            birth_date_raw,
            date,
        )
        else None
    )

    art_start_raw = source.get(
        "art_start_date"
    )

    art_start_date = (
        art_start_raw
        if isinstance(
            art_start_raw,
            date,
        )
        else None
    )

    last_visit_raw = source.get(
        "last_clinic_visit_date"
    )

    last_clinic_visit_date = (
        last_visit_raw
        if isinstance(
            last_visit_raw,
            date,
        )
        else None
    )

    refill_raw = source.get(
        "days_of_arv_refill"
    )

    days_of_arv_refill = (
        float(refill_raw)
        if isinstance(
            refill_raw,
            (int, float),
        )
        else None
    )

    if (
        days_of_arv_refill
        is not None
        and days_of_arv_refill < 0
    ):
        days_of_arv_refill = None

    viral_load_raw = source.get(
        "current_viral_load"
    )

    current_viral_load = (
        float(viral_load_raw)
        if isinstance(
            viral_load_raw,
            (int, float),
        )
        else None
    )

    age_at_art_raw = source.get(
        "age_at_art_initiation"
    )

    age_at_art = (
        float(age_at_art_raw)
        if isinstance(
            age_at_art_raw,
            (int, float),
        )
        else None
    )

    if (
        age_at_art is not None
        and (
            age_at_art < 0
            or age_at_art > 100
        )
    ):
        age_at_art = None

    # =================================================
    # CURRENT AGE
    # =================================================

    current_age = _age_in_years(
        birth_date,
        as_of=today,
    )

    # If age at ART was not explicitly stored, derive it
    # from DOB and ART-start date.
    if (
        age_at_art is None
        and art_start_date is not None
    ):
        age_at_art = _age_in_years(
            birth_date,
            as_of=art_start_date,
        )

    # =================================================
    # MONTHS ON ART
    #
    # IMPORTANT:
    # Uses last clinic visit, not today's date.
    # =================================================

    months_on_art = _months_on_art(
        art_start_date=(
            art_start_date
        ),
        last_clinic_visit_date=(
            last_clinic_visit_date
        ),
    )

    # =================================================
    # RAW NUMERIC MODEL FEATURES
    # =================================================

    _set_if_expected(
        values,
        expected,
        "Age at ART Initiation",
        age_at_art,
    )

    _set_if_expected(
        values,
        expected,
        "Current Age",
        current_age,
    )

    _set_if_expected(
        values,
        expected,
        "Days Of ARV Refill",
        days_of_arv_refill,
    )

    _set_if_expected(
        values,
        expected,
        "Current Viral Load",
        current_viral_load,
    )

    _set_if_expected(
        values,
        expected,
        "Months on ART",
        months_on_art,
    )

    # =================================================
    # Q3 STATUS VARIABLES
    #
    # Both source fields are blank in the training
    # dataset. They are therefore intentionally left NaN
    # and handled by the already-fitted model pipeline.
    # =================================================

    # Current Status Q3 (28 Days)
    # Current Status Q3 (90 Days)

    # =================================================
    # AGE FLAGS
    #
    # Exact training logic:
    #
    # Is Child   = Current Age < 15
    # Is Adult   = Current Age >= 18
    # Is Elderly = Current Age >= 65
    # =================================================

    if current_age is not None:

        _set_if_expected(
            values,
            expected,
            "Is Child",
            int(
                current_age < 15
            ),
        )

        _set_if_expected(
            values,
            expected,
            "Is Adult",
            int(
                current_age >= 18
            ),
        )

        _set_if_expected(
            values,
            expected,
            "Is Elderly",
            int(
                current_age >= 65
            ),
        )

    # =================================================
    # MISSING VIRAL LOAD FLAG
    # =================================================

    _set_if_expected(
        values,
        expected,
        "Missing Viral Load",
        int(
            current_viral_load
            is None
        ),
    )

    # =================================================
    # AGE GROUP ENCODING
    # =================================================

    _activate_category(
        values,
        expected,
        "Age Group",
        _age_group(
            current_age
        ),
    )

    # =================================================
    # ART INITIATION AGE GROUP
    # =================================================

    _activate_category(
        values,
        expected,
        "ART Initiation Age Group",
        _art_initiation_age_group(
            age_at_art
        ),
    )

    # =================================================
    # PREGNANCY STATUS
    #
    # Training converted missing/blank values to Unknown.
    # =================================================

    pregnancy_raw = source.get(
        "pregnancy_status"
    )

    pregnancy_status = (
        str(pregnancy_raw).strip()
        if pregnancy_raw is not None
        else ""
    )

    if not pregnancy_status:
        pregnancy_status = "Unknown"

    _activate_category(
        values,
        expected,
        "Pregnancy Status",
        pregnancy_status,
    )

    # =================================================
    # ARV REFILL CATEGORY
    # =================================================

    refill_category = (
        _arv_refill_category(
            days_of_arv_refill
        )
    )

    _activate_category(
        values,
        expected,
        "ARV Refill Category",
        refill_category,
    )

    # =================================================
    # VIRAL LOAD CATEGORY
    # =================================================

    viral_load_category = (
        _viral_load_category(
            current_viral_load
        )
    )

    _activate_category(
        values,
        expected,
        "Viral Load Category",
        viral_load_category,
    )

    # =================================================
    # STATE / LGA
    # =================================================

    state_raw = source.get(
        "state"
    )

    state = (
        str(state_raw).strip()
        if state_raw is not None
        else None
    )

    lga_raw = source.get(
        "lga"
    )

    lga = (
        str(lga_raw).strip()
        if lga_raw is not None
        else None
    )

    _activate_category(
        values,
        expected,
        "State",
        state,
    )

    _activate_category(
        values,
        expected,
        "LGA",
        lga,
    )

    # =================================================
    # SEX
    #
    # The trained artifact contains Sex_M only.
    # Female is therefore the fitted reference category.
    # =================================================

    sex_raw = source.get(
        "sex"
    )

    sex_text = (
        str(sex_raw)
        .strip()
        .lower()
        if sex_raw is not None
        else ""
    )

    if sex_text in {
        "m",
        "male",
    }:
        _activate_category(
            values,
            expected,
            "Sex",
            "M",
        )

    # Female/F remains reference category (all zero).

    # =================================================
    # LAST REGIMEN
    # =================================================

    regimen_raw = source.get(
        "last_regimen"
    )

    regimen = (
        str(regimen_raw).strip()
        if regimen_raw is not None
        else None
    )

    _activate_category(
        values,
        expected,
        "Last Regimen",
        regimen,
    )

    # =================================================
    # PATIENT TRANSFERRED IN
    # =================================================

    transferred_in = (
        _normalise_transfer_in(
            source.get(
                "patient_transferred_in"
            )
        )
    )

    # The fitted artifact only contains the True dummy.
    # False is the reference category.
    if transferred_in is True:
        _activate_category(
            values,
            expected,
            "Patient Transferred In",
            "True",
        )

    # =================================================
    # CREATE FINAL MODEL FRAME
    # =================================================

    frame = pd.DataFrame(
        [
            [
                values[
                    str(column)
                ]
                for column
                in expected_columns
            ]
        ],
        columns=[
            str(column)
            for column
            in expected_columns
        ],
    )

    # =================================================
    # SERIALISABLE INPUT SNAPSHOT
    # =================================================

    snapshot: dict[str, Any] = {
        "prediction_date": (
            today.isoformat()
        ),
        "current_age": (
            current_age
        ),
        "age_group": (
            _age_group(
                current_age
            )
        ),
        "is_child": (
            int(
                current_age < 15
            )
            if current_age
            is not None
            else None
        ),
        "is_adult": (
            int(
                current_age >= 18
            )
            if current_age
            is not None
            else None
        ),
        "is_elderly": (
            int(
                current_age >= 65
            )
            if current_age
            is not None
            else None
        ),
        "age_at_art_initiation": (
            age_at_art
        ),
        "art_initiation_age_group": (
            _art_initiation_age_group(
                age_at_art
            )
        ),
        "months_on_art": (
            months_on_art
        ),
        "days_of_arv_refill": (
            days_of_arv_refill
        ),
        "arv_refill_category": (
            refill_category
        ),
        "current_viral_load": (
            current_viral_load
        ),
        "missing_viral_load": (
            int(
                current_viral_load
                is None
            )
        ),
        "viral_load_category": (
            viral_load_category
        ),
        "last_regimen": (
            regimen
        ),
        "pregnancy_status": (
            pregnancy_status
        ),
        "sex": (
            sex_raw
        ),
        "state": state,
        "lga": lga,
        "patient_transferred_in": (
            transferred_in
        ),
        "last_clinic_visit_date": (
            last_clinic_visit_date.isoformat()
            if last_clinic_visit_date
            is not None
            else None
        ),
        "art_start_date": (
            art_start_date.isoformat()
            if art_start_date
            is not None
            else None
        ),
        "feature_count": len(
            expected_columns
        ),
    }

    return (
        frame,
        snapshot,
    )
