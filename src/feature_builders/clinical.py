"""
=========================================================
Clinical Feature Engineering

Creates HIV clinical variables.

Author:
    Akayovwe Okugbe

=========================================================
"""

import numpy as np
import pandas as pd


# =====================================================
# VIRAL LOAD CATEGORY
# =====================================================

def create_viral_load_category(df: pd.DataFrame):

    conditions = [

        df["Current Viral Load"].isna(),

        df["Current Viral Load"] < 1000,

        df["Current Viral Load"] >= 1000

    ]

    choices = [

        "Unknown",

        "Suppressed",

        "Unsuppressed"

    ]

    df["Viral Load Category"] = np.select(

        conditions,

        choices,

        default="Unknown"

    )

    return df


# =====================================================
# MISSING VIRAL LOAD FLAG
# =====================================================

def create_missing_viral_load(df):

    df["Missing Viral Load"] = (

        df["Current Viral Load"]

        .isna()

        .astype(int)

    )

    return df