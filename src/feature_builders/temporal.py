"""
=========================================================
Temporal Feature Engineering

Creates date-based predictive features.

Author:
    Akayovwe Okugbe

=========================================================
"""

import pandas as pd


# =====================================================
# MONTHS ON ART
# =====================================================

def create_art_duration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates duration on ART.
    """

    df["Months on ART"] = (

        (
            df["Last Clinic Visit Date"]

            -

            df["ART Start Date"]

        ).dt.days

        / 30.44

    ).round(1)

    return df


# =====================================================
# VISIT GAP
# =====================================================

def create_visit_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates days between
    drug pickup and clinic visit.
    """

    df["Visit Gap"] = (

        df["Last Clinic Visit Date"]

        -

        df["Last Drug Pickup date"]

    ).dt.days

    return df


# =====================================================
# LAST VISIT YEAR
# =====================================================

def create_visit_year(df: pd.DataFrame):

    df["Visit Year"] = (

        df["Last Clinic Visit Date"]

        .dt.year

    )

    return df


# =====================================================
# LAST VISIT MONTH
# =====================================================

def create_visit_month(df: pd.DataFrame):

    df["Visit Month"] = (

        df["Last Clinic Visit Date"]

        .dt.month

    )

    return df