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
import numpy as np

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

    logger.info("Reading dataset...")
    df = pd.read_excel(filepath)

    logger.info("\nRAW COLUMN NAMES:")
    for i, col in enumerate(df.columns):
        logger.info(f"{i}: {repr(col)}")

    # -----------------------------------------------------
    # Clean column names
    # -----------------------------------------------------
    logger.info("Cleaning data columns...")
    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.replace("\n", " ", regex=False)
        .str.replace("\r", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    logger.info("Dataset columns after cleaning:")
    for col in df.columns:
        logger.info(repr(col))

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
# CLEAN AGE AT ART INITIATION
# =====================================================

def clean_age_at_art_initiation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the Age at ART Initiation column.

    The source dataset contains a small number of
    inconsistent values, including:

        - Negative ages
        - Dates stored in the age column
        - Other non-numeric values

    These values cannot be treated as valid ages.
    They are therefore converted to missing values
    rather than being replaced with an assumed value.

    This preserves the integrity of the original data
    while preventing invalid values from entering the
    modelling pipeline.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset to clean.

    Returns
    -------
    pandas.DataFrame
        Dataset with a validated numeric age column.
    """

    column = "Age at ART Initiation"

    if column not in df.columns:
        logger.warning(
            f"Column '{column}' not found. "
            "Age cleaning skipped."
        )
        return df

    logger.info(
        "Cleaning Age at ART Initiation..."
    )

    # -------------------------------------------------
    # Convert valid numeric values to numbers.
    #
    # Dates and other non-numeric values become NaN.
    # -------------------------------------------------

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    # -------------------------------------------------
    # Identify negative ages.
    #
    # Negative ages are impossible and therefore
    # treated as invalid observations.
    # -------------------------------------------------

    negative_mask = df[column] < 0

    negative_count = negative_mask.sum()

    if negative_count > 0:

        logger.warning(
            f"Converting {negative_count:,} "
            "negative Age at ART Initiation values "
            "to missing."
        )

        df.loc[negative_mask, column] = np.nan

    # -------------------------------------------------
    # Identify implausibly high ages.
    #
    # Ages above 100 are treated as invalid for
    # this project.
    # -------------------------------------------------

    extreme_mask = df[column] > 100

    extreme_count = extreme_mask.sum()

    if extreme_count > 0:

        logger.warning(
            f"Converting {extreme_count:,} "
            "Age at ART Initiation values above "
            "100 to missing."
        )

        df.loc[extreme_mask, column] = np.nan

    # -------------------------------------------------
    # Ensure a numeric dtype for Parquet compatibility.
    # -------------------------------------------------

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    logger.info(
        "Age at ART Initiation cleaning completed."
    )

    logger.info(
        f"Valid numeric ages remaining: "
        f"{df[column].notna().sum():,}"
    )

    logger.info(
        f"Missing / invalid ages: "
        f"{df[column].isna().sum():,}"
    )

    return df


# =====================================================
# SAVE CLEAN DATASET
# =====================================================

def save_processed_dataset(df: pd.DataFrame):
    """
    Saves processed dataset into the processed
    data folder.
    """

    output_file = PROCESSED_DATA / "01_dates_converted.parquet"

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
    # Convert Dates Columns
    # -------------------------------------------------

    df = convert_dates(df)

    # =====================================================
    # CLEAN AGE AT ART INITIATION
    # =====================================================

    df = clean_age_at_art_initiation(df)

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
