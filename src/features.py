"""
=========================================================
Feature Engineering Pipeline

LTFU Prediction in HIV Treatment Programmes
Rome Business School Capstone Project

File:
    features.py

Purpose:
    Executes the complete feature engineering
    pipeline by orchestrating all feature
    builder modules.

    This script transforms the cleaned dataset
    into a machine-learning-ready dataset.

Author:
    Akayovwe Okugbe

=========================================================
"""

# =====================================================
# IMPORT LIBRARIES
# =====================================================

import pandas as pd

from src.config import (
    PROCESSED_DATA
)

from src.logger import logger

from src.utils import (
    print_header,
    print_subheader,
    dataset_shape,
    save_dataframe
)

# Feature Builders
from src.feature_builders import *

# Encoding
from src.encoder import one_hot_encode

# Dataset Splitter
from src.splitter import save_split_data, split_data


# =====================================================
# LOAD PREPROCESSED DATASET
# =====================================================

def load_dataset():
    """
    Loads the preprocessed dataset.

    Returns
    -------
    pandas.DataFrame
    """

    filepath = PROCESSED_DATA / "01_dates_converted.parquet"

    logger.info("Loading preprocessed dataset...")
    logger.info(f"Source: {filepath}")

    df = pd.read_parquet(filepath)

    logger.info(
        f"Dataset loaded successfully "
        f"({df.shape[0]:,} rows × {df.shape[1]} columns)."
    )

    return df


# =====================================================
# FEATURE ENGINEERING PIPELINE
# =====================================================

def engineer_features(df):

    """
    Executes all feature engineering steps.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
    """

    print_header("Feature Engineering")

    logger.info("Beginning feature engineering...")

    # -------------------------------------------------
    # DEMOGRAPHIC FEATURES
    # -------------------------------------------------

    print_subheader("Demographic Features")

    df = create_age_groups(df)

    df = create_age_flags(df)

    df = create_art_initiation_age_group(df)

    df = clean_pregnancy_status(df)

    logger.info("Demographic features created.")

    # -------------------------------------------------
    # TEMPORAL FEATURES
    # -------------------------------------------------

    print_subheader("Temporal Features")

    df = create_art_duration(df)

    df = create_visit_gap(df)

    df = create_visit_year(df)

    df = create_visit_month(df)

    logger.info("Temporal features created.")

    # -------------------------------------------------
    # CLINICAL FEATURES
    # -------------------------------------------------

    print_subheader("Clinical Features")

    df = create_viral_load_category(df)

    df = create_missing_viral_load(df)

    logger.info("Clinical features created.")

    # -------------------------------------------------
    # TREATMENT FEATURES
    # -------------------------------------------------

    print_subheader("Treatment Features")

    df = create_transfer_status(df)

    df = create_mortality_flag(df)

    df = create_arv_refill_category(df)

    logger.info("Treatment features created.")

    # -------------------------------------------------
    # TARGET VARIABLE
    # -------------------------------------------------

    print_subheader("Target Variable")

    df = create_target(df)

    df = remove_leakage(df)

    logger.info("Target variable created.")

    # -------------------------------------------------
    # FINALISE MODEL FEATURES
    # -------------------------------------------------

    print_subheader("Finalising Model Features")

    df = finalise_model_features(df)

    logger.info(
        "Model features finalised."
    )

    return df


# =====================================================
# ENCODE CATEGORICAL VARIABLES
# =====================================================

def encode_dataset(df):

    """
    One-hot encodes categorical variables.
    """

    print_subheader("Encoding Variables")

    categorical_columns = [

        "State",

        "LGA",

        "Sex",

        "Age Group",

        "ART Initiation Age Group",

        "Pregnancy Status",

        "ARV Refill Category",

        "Last Regimen",

        "Patient Transferred In",

        "Viral Load Category"

    ]

    existing_columns = [

        column

        for column in categorical_columns

        if column in df.columns

    ]

    df = one_hot_encode(

        df,

        existing_columns

    )

    logger.info("Categorical encoding completed.")

    return df


# =====================================================
# SAVE FEATURE DATASET
# =====================================================

def save_features(df):

    """
    Saves the engineered dataset.
    """

    output = PROCESSED_DATA / "02_feature_engineered.parquet"

    save_dataframe(

        df,

        output

    )

    logger.info("Feature engineered dataset saved.")


# =====================================================
# CREATE TRAIN / TEST SPLIT
# =====================================================

def create_train_test(df):

    """
    Splits dataset into training
    and testing datasets.
    """

    print_subheader("Train-Test Split")

    if "Target" not in df.columns:
        raise KeyError(
            "The Target column was not found."
        )

    missing_target = df["Target"].isna().sum()

    if missing_target > 0:
        raise ValueError(
            f"The Target column contains "
            f"{missing_target:,} missing values."
        )

    invalid_target_values = set(
        df["Target"].dropna().unique()
    ) - {0, 1}

    if invalid_target_values:
        raise ValueError(
            "Unexpected target values found: "
            f"{invalid_target_values}"
        )

    logger.info(
        "Target validation completed successfully."
    )

    X_train, X_test, y_train, y_test = split_data(df)

    save_split_data(
        X_train,
        X_test,
        y_train,
        y_test
    )

    logger.info("Dataset successfully split.")

    print(f"\nTraining Records : {len(X_train):,}")

    print(f"Testing Records  : {len(X_test):,}")

    logger.info("Auditing training feature data types...")

    datetime_columns = X_train.select_dtypes(
        include=[
            "datetime",
            "datetimetz"
        ]
    ).columns.tolist()

    object_columns = X_train.select_dtypes(
        include=[
            "object",
            "string",
            "category"
        ]
    ).columns.tolist()

    boolean_columns = X_train.select_dtypes(
        include=["bool"]
    ).columns.tolist()

    numeric_columns = X_train.select_dtypes(
        include=["number"]
    ).columns.tolist()

    logger.info(
        "Numeric feature columns: %s",
        len(numeric_columns)
    )

    logger.info(
        "Boolean feature columns: %s",
        len(boolean_columns)
    )

    logger.info(
        "Remaining datetime columns: %s",
        datetime_columns
    )

    logger.info(
        "Remaining unencoded categorical columns: %s",
        object_columns
    )

    if datetime_columns:
        raise TypeError(
            "Datetime columns remain in the model dataset: "
            f"{datetime_columns}"
        )

    if object_columns:
        raise TypeError(
            "Unencoded categorical columns remain in the "
            f"model dataset: {object_columns}"
        )

    return (

        X_train,

        X_test,

        y_train,

        y_test

    )


# =====================================================
# MAIN PROGRAM
# =====================================================

def main():

    logger.info("=" * 60)

    logger.info("STARTING FEATURE ENGINEERING")

    logger.info("=" * 60)

    df = load_dataset()

    dataset_shape(df)

    df = engineer_features(df)

    df = encode_dataset(df)

    save_features(df)

    create_train_test(df)

    logger.info("=" * 60)

    logger.info("FEATURE ENGINEERING COMPLETED")

    logger.info("=" * 60)


if __name__ == "__main__":

    main()
