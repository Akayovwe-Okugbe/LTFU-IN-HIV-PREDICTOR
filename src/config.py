"""
=========================================================
Configuration File

LTFU Prediction in HIV Treatment Programmes
Rome Business School Capstone Project

Purpose:
Central location for project configuration.

Any settings that may change during development
should be defined here.

Author:
Akayovwe Okugbe
=========================================================
"""

from pathlib import Path

# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA = DATA_DIR / "raw"

PROCESSED_DATA = DATA_DIR / "processed"

MODELS = PROJECT_ROOT / "models"

REPORTS = PROJECT_ROOT / "reports"

# =========================================================
# DATASET
# =========================================================

DATASET_NAME = "LTFU in HIV DataSet NDR.xlsx"

# =========================================================
# TARGET VARIABLES
# =========================================================

TARGET = "Current Status (90 Days)"

SECONDARY_TARGET = "Current Status (28 Days)"

# =========================================================
# TRAIN / TEST SETTINGS
# =========================================================

TEST_SIZE = 0.20

RANDOM_STATE = 42

# =========================================================
# DATE COLUMNS
# =========================================================

DATE_COLUMNS = [

    "Date Of Birth",

    "ART Start Date",

    "Last Drug Pickup date",

    "Last Drug Pickup date Q1",

    "Last Drug Pickup date Q2",

    "Last Drug Pickup date Q4",

    "Last Clinic Visit Date",

    "Date Of Current Viral Load",

    "Date Of Current Viral Load Q1",

    "Date Of Current Viral Load Q2",

    "Date Of Current Viral Load Q4",

    "Patient Deceased Date",

    "Transferred Out Date",

    "Transferred In Date"

]