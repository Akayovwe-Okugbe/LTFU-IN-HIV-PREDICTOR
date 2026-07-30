"""
=========================================================
Treatment Feature Engineering

Creates treatment-related features.

Author:
    Akayovwe Okugbe

=========================================================
"""

import pandas as pd


# =====================================================
# TRANSFER STATUS
# =====================================================

def create_transfer_status(df: pd.DataFrame):

    df["Transfer Status"] = "None"

    df.loc[

        df["Patient Transferred In"] == "Yes",

        "Transfer Status"

    ] = "Transferred In"

    df.loc[

        df["Patient Transferred Out"] == "Yes",

        "Transfer Status"

    ] = "Transferred Out"

    return df


# =====================================================
# MORTALITY FLAG
# =====================================================

def create_mortality_flag(df: pd.DataFrame):

    df["Mortality"] = (

        df["Patient Has Died"]

        .map({

            "Yes": 1,

            "No": 0

        })

    )

    return df


# =====================================================
# ARV REFILL CATEGORY
# =====================================================

def create_arv_refill_category(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Categorises the number of ARV refill days.

    Categories
    ----------
    Missing:
        No valid refill duration was recorded.

    Short Refill:
        30 days or fewer.

    Medium Refill:
        Between 31 and 60 days.

    Long Refill:
        More than 60 days.
    """

    refill_column = "Days Of ARV Refill"

    if refill_column not in df.columns:
        raise KeyError(
            f"Required column '{refill_column}' was not found."
        )

    # Ensure the source column is numeric.
    df[refill_column] = pd.to_numeric(
        df[refill_column],
        errors="coerce"
    )

    # Negative refill durations are invalid.
    df.loc[
        df[refill_column] < 0,
        refill_column
    ] = pd.NA

    bins = [
        float("-inf"),
        30,
        60,
        float("inf")
    ]

    labels = [
        "Short Refill",
        "Medium Refill",
        "Long Refill"
    ]

    df["ARV Refill Category"] = pd.cut(
        df[refill_column],
        bins=bins,
        labels=labels,
        right=True
    )

    # Convert to object temporarily so that a missing
    # category can be inserted safely.
    df["ARV Refill Category"] = (
        df["ARV Refill Category"]
        .astype("object")
        .fillna("Unknown")
    )

    return df
