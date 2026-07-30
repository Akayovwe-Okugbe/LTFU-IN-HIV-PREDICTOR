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
# AGE AT ART INITIATION GROUP
# =====================================================

def create_art_initiation_age_group(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Categorises patient age at ART initiation.

    Categories
    ----------
    Child:
        Younger than 15 years.

    Adolescent/Young Adult:
        15 to 24 years.

    Adult:
        25 to 44 years.

    Older Adult:
        45 years and above.

    Unknown:
        Missing or invalid age at ART initiation.
    """

    age_column = "Age at ART Initiation"

    if age_column not in df.columns:
        raise KeyError(
            f"Required column '{age_column}' was not found."
        )

    df[age_column] = pd.to_numeric(
        df[age_column],
        errors="coerce"
    )

    # Values outside the accepted age range are invalid.
    df.loc[
        (df[age_column] < 0)
        |
        (df[age_column] > 100),
        age_column
    ] = pd.NA

    bins = [
        0,
        15,
        25,
        45,
        101
    ]

    labels = [
        "Child",
        "Adolescent/Young Adult",
        "Adult",
        "Older Adult"
    ]

    df["ART Initiation Age Group"] = pd.cut(
        df[age_column],
        bins=bins,
        labels=labels,
        right=False
    )

    df["ART Initiation Age Group"] = (
        df["ART Initiation Age Group"]
        .astype("object")
        .fillna("Unknown")
    )

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
