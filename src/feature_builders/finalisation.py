"""
=========================================================
Feature Dataset Finalisation

Removes identifiers, redundant raw variables,
quarterly data, unsupported datetime columns
and leakage-prone outcome variables before
model training.

Author:
    Akayovwe Okugbe

=========================================================
"""

import pandas as pd

from src.logger import logger


# =====================================================
# FINALISE MODEL FEATURES
# =====================================================

def finalise_model_features(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Removes variables that should not be supplied
    directly to the machine-learning models.

    Parameters
    ----------
    df : pandas.DataFrame
        Feature-engineered dataset.

    Returns
    -------
    pandas.DataFrame
        Final modelling dataset.
    """

    logger.info(
        "Removing identifiers, raw dates, quarterly variables "
        "and leakage-prone columns..."
    )

    columns_to_drop = [

        # -------------------------------------------------
        # Unique identifier
        # -------------------------------------------------
        "Patient Number",

        # -------------------------------------------------
        # Raw demographic date
        # -------------------------------------------------
        "Date Of Birth",

        # -------------------------------------------------
        # Raw current dates already represented by
        # engineered or retained clinical variables
        # -------------------------------------------------
        "ART Start Date",
        "Last Drug Pickup date",
        "Last Clinic Visit Date",
        "Date Of Current Viral Load",

        # -------------------------------------------------
        # Baseline-excluded temporal features
        # -------------------------------------------------
        "Visit Gap",
        "Visit Year",
        "Visit Month",

        # -------------------------------------------------
        # Quarterly drug-pickup dates
        # -------------------------------------------------
        "Last Drug Pickup date Q1",
        "Last Drug Pickup date Q2",
        "Last Drug Pickup date Q3",
        "Last Drug Pickup date Q4",

        # -------------------------------------------------
        # Quarterly viral-load measurements
        # -------------------------------------------------
        "Current Viral Load Q1",
        "Current Viral Load Q2",
        "Current Viral Load Q3",
        "Current Viral Load Q4",

        # -------------------------------------------------
        # Quarterly viral-load dates
        # -------------------------------------------------
        "Date Of Current Viral Load Q1",
        "Date Of Current Viral Load Q2",
        "Date Of Current Viral Load Q3",
        "Date Of Current Viral Load Q4",

        # -------------------------------------------------
        # Death-related outcome variables
        # -------------------------------------------------
        "Patient Has Died",
        "Patient Deceased Date",
        "Mortality",

        # -------------------------------------------------
        # Transfer-out variables
        # -------------------------------------------------
        "Patient Transferred Out",
        "Transferred Out Date",
        "Transfer Status",

        # -------------------------------------------------
        # Transfer-in date remains a raw date.
        # The Yes/No transfer-in indicator is retained.
        # -------------------------------------------------
        "Transferred In Date",
    ]

    existing_columns = [

        column

        for column in columns_to_drop

        if column in df.columns

    ]

    df = df.drop(
        columns=existing_columns
    )

    logger.info(
        "%s identifier, raw, quarterly or "
        "leakage-prone columns removed.",
        len(existing_columns)
    )

    logger.info(
        "Removed columns: %s",
        existing_columns
    )

    return df
