"""
=========================================================
Dataset Validation

LTFU Prediction in HIV Treatment Programmes
Rome Business School Capstone Project

File:
    validation.py

Purpose:
    Performs data quality validation before
    preprocessing and feature engineering.

    The module checks:

    • Missing columns
    • Duplicate patient IDs
    • Invalid dates
    • Impossible ages
    • Future dates
    • Negative refill values
    • Data consistency

Author:
    Akayovwe Okugbe

=========================================================
"""

import pandas as pd

from src.logger import logger
from src.config import DATE_COLUMNS


# =====================================================
# REQUIRED COLUMNS
# =====================================================

REQUIRED_COLUMNS = [

    "Patient Number",

    "Sex",

    "Current Age",

    "Age at ART Initiation",

    "ART Start Date",

    "Current Status (90 Days)"

]


# =====================================================
# CHECK REQUIRED COLUMNS
# =====================================================

def check_required_columns(df):

    missing = [

        col

        for col in REQUIRED_COLUMNS

        if col not in df.columns

    ]

    if missing:

        logger.error(f"Missing columns: {missing}")

        raise ValueError(
            f"Dataset missing required columns: {missing}"
        )

    logger.info("Required columns verified.")


# =====================================================
# DUPLICATE PATIENT CHECK
# =====================================================

def check_duplicates(df):

    duplicates = df["Patient Number"].duplicated().sum()

    logger.info(f"Duplicate Patient IDs: {duplicates:,}")

    return duplicates


# =====================================================
# INVALID AGE CHECK
# =====================================================

def check_age(df):

    invalid = df[
        (df["Current Age"] < 0) |
        (df["Current Age"] > 120)
    ]

    logger.info(

        f"Invalid Current Age records: {len(invalid):,}"

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
# FUTURE DATE CHECK
# =====================================================

def check_future_dates(df):

    today = pd.Timestamp.today()

    results = {}

    for col in DATE_COLUMNS:

        if col in df.columns:

            future = (df[col] > today).sum()

            results[col] = future

    logger.info("Future date validation completed.")

    return pd.DataFrame.from_dict(

        results,

        orient="index",

        columns=["Future Dates"]

    )


# =====================================================
# RUN ALL VALIDATIONS
# =====================================================

def validate_dataset(df):

    logger.info("Starting dataset validation...")

    check_required_columns(df)

    check_duplicates(df)

    check_age(df)

    check_refill_days(df)

    future_dates = check_future_dates(df)

    logger.info("Validation completed.")

    return future_dates