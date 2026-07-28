"""
=========================================================
Demographic Feature Engineering

Creates demographic-related machine learning
features.

Author:
    Akayovwe Okugbe

=========================================================
"""

import pandas as pd


# =====================================================
# AGE GROUPS
# =====================================================

def create_age_groups(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates categorical age groups.
    """

    bins = [0, 15, 25, 35, 45, 55, 65, 150]

    labels = [
        "0-14",
        "15-24",
        "25-34",
        "35-44",
        "45-54",
        "55-64",
        "65+"
    ]

    df["Age Group"] = pd.cut(
        df["Current Age"],
        bins=bins,
        labels=labels,
        right=False
    )

    return df


# =====================================================
# AGE CATEGORY FLAGS
# =====================================================

def create_age_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates binary age indicators.
    """

    df["Is Child"] = (df["Current Age"] < 15).astype(int)

    df["Is Adult"] = (df["Current Age"] >= 18).astype(int)

    df["Is Elderly"] = (df["Current Age"] >= 65).astype(int)

    return df


# =====================================================
# PREGNANCY FEATURE
# =====================================================

def clean_pregnancy_status(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardises pregnancy status.
    """

    df["Pregnancy Status"] = (
        df["Pregnancy Status"]
        .fillna("Unknown")
        .replace("", "Unknown")
    )

    return df