"""
=========================================================
Dataset Validation

LTFU Prediction in HIV Treatment Programmes
Rome Business School Capstone Project

Purpose:
    Performs integrity checks on the raw dataset before
    preprocessing and feature engineering.

    These checks help identify inconsistencies,
    impossible values and data quality issues that may
    negatively affect model performance.

Author:
    Akayovwe Okugbe

=========================================================
"""

# =====================================================
# IMPORT REQUIRED LIBRARIES
# =====================================================

import pandas as pd

from src.logger import logger


# =====================================================
# REQUIRED COLUMNS
# =====================================================

REQUIRED_COLUMNS = [

    "Patient Number",
    "State",
    "LGA",
    "Sex",
    "Age at ART Initiation",
    "Current Age",
    "ART Start Date",
    "Last Drug Pickup date",
    "Current Status (90 Days)"

]


# =====================================================
# VALIDATE REQUIRED COLUMNS
# =====================================================

def validate_required_columns(df):

    """
    Checks that all required columns exist.
    """

    logger.info("Checking required columns...")

    missing = [

        col

        for col in REQUIRED_COLUMNS

        if col not in df.columns

    ]

    if missing:

        raise ValueError(

            f"Missing required columns:\n{missing}"

        )

    logger.info("Required columns verified.")


# =====================================================
# DUPLICATE PATIENTS
# =====================================================

def check_duplicate_patients(df):

    """
    Checks duplicate patient numbers.
    """

    duplicates = df["Patient Number"].duplicated().sum()

    logger.info(

        f"Duplicate Patient Numbers: {duplicates:,}"

    )

    return duplicates


# =====================================================
# CHECK NEGATIVE AGE AT ART INITIATION
# =====================================================

def check_negative_age(df):
    """
    Identifies negative values in Age at ART Initiation.

    The source dataset contains mixed data types in this
    column, including numeric ages and date-formatted
    values. Values are therefore converted to numeric
    temporarily using errors="coerce".

    Non-numeric values are not treated as negative ages;
    they are handled separately by the mixed-type validation
    check.
    """

    age_numeric = pd.to_numeric(
        df["Age at ART Initiation"],
        errors="coerce"
    )

    negative_count = (age_numeric < 0).sum()

    logger.info(
        f"Negative Age at ART Initiation values: "
        f"{negative_count:,}"
    )

    return negative_count


# =====================================================
# CHECK NON-NUMERIC AGE VALUES
# =====================================================

def check_non_numeric_age(df):
    """
    Identifies Age at ART Initiation values that cannot
    be interpreted as numeric ages.

    These may include incorrectly formatted dates or
    other malformed values originating from the source
    dataset.
    """

    age_numeric = pd.to_numeric(
        df["Age at ART Initiation"],
        errors="coerce"
    )

    non_numeric_mask = (
        df["Age at ART Initiation"].notna()
        & age_numeric.isna()
    )

    non_numeric_count = non_numeric_mask.sum()

    logger.info(
        f"Non-numeric Age at ART Initiation values: "
        f"{non_numeric_count:,}"
    )

    return non_numeric_count


# =====================================================
# EXTREME AGES
# =====================================================

def check_extreme_age(df):

    """
    Identifies patients older than 100 years.
    """

    extreme = (

        df["Current Age"] > 100

    ).sum()

    logger.info(

        f"Patients older than 100 years: {extreme:,}"

    )

    return extreme


# =====================================================
# INVALID PREGNANCY RECORDS
# =====================================================

def check_invalid_pregnancy(df):

    """
    Detects pregnancy values recorded for males.
    """

    invalid = df[

        (df["Sex"] == "Male")

        &

        (

            df["Pregnancy Status"]

            .isin(["Pregnant", "Breastfeeding"])

        )

    ]

    logger.info(

        f"Invalid pregnancy records: {len(invalid):,}"

    )

    return invalid


# =====================================================
# TRANSFER VALIDATION
# =====================================================

def check_transfer_dates(df):

    """
    Checks transferred-out patients with
    missing transfer dates.
    """

    invalid = df[

        (df["Patient Transferred Out"] == "Yes")

        &

        (df["Transferred Out Date"].isna())

    ]

    logger.info(

        f"Transferred Out without date: {len(invalid):,}"

    )

    return invalid


# =====================================================
# DEATH VALIDATION
# =====================================================

def check_deceased_dates(df):

    """
    Checks deceased patients with
    missing death dates.
    """

    invalid = df[

        (df["Patient Has Died"] == "Yes")

        &

        (df["Patient Deceased Date"].isna())

    ]

    logger.info(

        f"Missing deceased dates: {len(invalid):,}"

    )

    return invalid


# =====================================================
# NEGATIVE REFILL DAYS
# =====================================================

def check_refill_days(df):

    if "Days Of ARV Refill" not in df.columns:

        return pd.DataFrame()

    invalid = df[
        df["Days Of ARV Refill"] < 0
    ]

    logger.info(

        f"Negative refill records: {len(invalid):,}"

    )

    return invalid


# =====================================================
# ART START DATE VALIDATION
# =====================================================

def check_art_dates(df):

    """
    Detects missing ART start dates.
    """

    missing = df["ART Start Date"].isna().sum()

    logger.info(

        f"Missing ART Start Dates: {missing:,}"

    )

    return missing


# =====================================================
# TARGET VARIABLE
# =====================================================

def check_target_variable(df):

    """
    Displays class balance.
    """

    counts = (

        df["Current Status (90 Days)"]

        .value_counts(dropna=False)

    )

    logger.info(

        "\nCurrent Status (90 Days):\n"

        + str(counts)

    )

    return counts


# =====================================================
# MASTER VALIDATION FUNCTION
# =====================================================

def validate_dataset(df):

    """
    Runs every validation routine.
    """

    logger.info("=" * 60)

    logger.info("RUNNING DATASET VALIDATION")

    logger.info("=" * 60)

    validate_required_columns(df)

    check_duplicate_patients(df)

    check_negative_age(df)

    check_extreme_age(df)

    check_invalid_pregnancy(df)

    check_transfer_dates(df)

    check_deceased_dates(df)

    check_refill_days(df)

    check_art_dates(df)

    check_target_variable(df)

    logger.info("Validation completed successfully.")
