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