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
from src.splitter import split_data


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

    logger.info("Treatment features created.")

    # -------------------------------------------------
    # TARGET VARIABLE
    # -------------------------------------------------

    print_subheader("Target Variable")

    df = create_target(df)

    df = remove_leakage(df)

    logger.info("Target variable created.")

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

        "Pregnancy Status",

        "Transfer Status",

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

    X_train, X_test, y_train, y_test = split_data(df)

    logger.info("Dataset successfully split.")

    print(f"\nTraining Records : {len(X_train):,}")

    print(f"Testing Records  : {len(X_test):,}")

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
