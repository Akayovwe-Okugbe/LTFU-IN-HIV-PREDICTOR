"""
=========================================================
Target Variable Engineering

Creates the machine learning target
and removes leakage variables.

Author:
    Akayovwe Okugbe

=========================================================
"""

import pandas as pd


# =====================================================
# TARGET
# =====================================================

def create_target(df: pd.DataFrame):

    df["Target"] = (

        df["Current Status (90 Days)"]

        .map({

            "Active": 0,

            "Inactive": 1

        })

    )

    return df


# =====================================================
# REMOVE LEAKAGE
# =====================================================

def remove_leakage(df: pd.DataFrame):

    leakage_columns = [

        "Current Status (28 Days)",

        "Current Status (90 Days)",

        "Current Status Q1 (28 Days)",

        "Current Status Q1 (90 Days)",

        "Current Status Q2 (28 Days)",

        "Current Status Q2 (90 Days)",

        "Current Status Q4 (28 Days)",

        "Current Status Q4 (90 Days)"

    ]

    existing = [

        col

        for col in leakage_columns

        if col in df.columns

    ]

    return df.drop(

        columns=existing

    )