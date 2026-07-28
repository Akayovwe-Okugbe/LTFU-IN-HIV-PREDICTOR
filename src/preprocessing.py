"""
=========================================================
LTFU Prediction in HIV Treatment Programmes
Rome Business School Capstone Project

File:
    preprocessing.py

Purpose:
    Loads the raw National Data Repository (NDR) dataset,
    performs initial preprocessing, validates the dataset,
    converts date variables into datetime format,
    generates summary statistics, and saves the cleaned
    dataset for feature engineering.

Author:
    Akayovwe Okugbe

=========================================================
"""

# =====================================================
# IMPORT REQUIRED LIBRARIES
# =====================================================

import pandas as pd

from src.config import (
    RAW_DATA,
    PROCESSED_DATA,
    DATASET_NAME,
    DATE_COLUMNS,
)

from src.logger import logger

from src.utils import (
    print_header,
    print_subheader,
    dataset_shape,
    missing_summary,
    duplicate_summary,
    column_summary,
    invalid_dates,
    save_dataframe,
)

from src.validation import (
    validate_dataset,
)


# =====================================================
# LOAD DATASET
# =====================================================

def load_dataset(filename: str) -> pd.DataFrame:
    """
    Loads the raw HIV dataset from the configured
    raw data directory.

    Parameters
    ----------
    filename : str
        Dataset filename.

    Returns
    -------
    pandas.DataFrame
        Loaded dataset.
    """

    filepath = RAW_DATA / filename

    logger.info("Loading dataset...")
    logger.info(f"Source: {filepath}")

    df = pd.read_excel(filepath)

    logger.info(
        f"Dataset loaded successfully "
        f"({df.shape[0]:,} rows × {df.shape[1]} columns)."
    )

    return df


# =====================================================
# DATASET OVERVIEW
# =====================================================

def dataset_summary(df: pd.DataFrame):
    """
    Prints a high-level overview of the dataset.
    """

    print_header("Dataset Summary")

    dataset_shape(df)

    print_subheader("Column Information")

    print(column_summary(df))

    print_subheader("Duplicate Records")

    duplicate_summary(df)

    print_subheader("Missing Value Summary")

    print(missing_summary(df))


# =====================================================
# CONVERT DATE VARIABLES
# =====================================================

def convert_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts configured date columns into datetime.

    Invalid dates are automatically converted
    into NaT.
    """

    logger.info("Converting date columns...")

    for column in DATE_COLUMNS:

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

    logger.info("Date conversion completed.")

    return df


# =====================================================
# DATE VALIDATION SUMMARY
# =====================================================

def date_validation_summary(df: pd.DataFrame):
    """
    Displays invalid or missing dates after
    conversion.
    """

    print_subheader("Date Validation")

    print(
        invalid_dates(
            df,
            DATE_COLUMNS
        )
    )


# =====================================================
# SAVE CLEAN DATASET
# =====================================================

def save_processed_dataset(df: pd.DataFrame):
    """
    Saves processed dataset into the processed
    data folder.
    """

    output_file = PROCESSED_DATA / "01_dates_converted.csv"

    save_dataframe(df, output_file)

    logger.info(
        f"Processed dataset saved to {output_file}"
    )


# =====================================================
# MAIN PROGRAM
# =====================================================

def main():

    logger.info("=" * 60)
    logger.info("STARTING DATA PREPROCESSING")
    logger.info("=" * 60)

    # -------------------------------------------------
    # Load Dataset
    # -------------------------------------------------

    df = load_dataset(DATASET_NAME)

    # -------------------------------------------------
    # Validate Dataset Structure
    # -------------------------------------------------

    validate_dataset(df)

    # -------------------------------------------------
    # Dataset Summary
    # -------------------------------------------------

    dataset_summary(df)

    # -------------------------------------------------
    # Convert Dates
    # -------------------------------------------------

    df = convert_dates(df)

    # -------------------------------------------------
    # Date Validation
    # -------------------------------------------------

    date_validation_summary(df)

    # -------------------------------------------------
    # Save Dataset
    # -------------------------------------------------

    save_processed_dataset(df)

    logger.info("=" * 60)
    logger.info("PREPROCESSING COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)


# =====================================================
# ENTRY POINT
# =====================================================

if __name__ == "__main__":

    main()