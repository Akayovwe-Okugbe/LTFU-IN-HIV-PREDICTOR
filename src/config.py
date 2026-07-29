"""
=========================================================
Configuration File

LTFU Prediction in HIV Treatment Programmes
Rome Business School Capstone Project

Purpose:
    Central location for all project configuration.

    Any settings that may change during development
    should be defined here rather than hard-coded
    throughout the project.

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

EXTERNAL_DATA = DATA_DIR / "external"

MODELS = PROJECT_ROOT / "models"

REPORTS = PROJECT_ROOT / "reports"

NOTEBOOKS = PROJECT_ROOT / "notebooks"

API = PROJECT_ROOT / "api"

DASHBOARD = PROJECT_ROOT / "dashboard"

# =========================================================
# DATASET
# =========================================================

DATASET_NAME = "LTFU in HIV DataSet NDR.xlsx"

PROCESSED_DATASET = "01_dates_converted.parquet"

FEATURE_DATASET = "02_feature_engineered.parquet"

# =========================================================
# TARGET VARIABLES
# =========================================================

TARGET = "Current Status (90 Days)"

SECONDARY_TARGET = "Current Status (28 Days)"

TARGET_MAPPING = {
    "Active": 0,
    "Inactive": 1
}

# =========================================================
# TRAIN / TEST SETTINGS
# =========================================================

TEST_SIZE = 0.20

RANDOM_STATE = 42

N_SPLITS = 10

STRATIFY = True

# =========================================================
# DATA QUALITY SETTINGS
# =========================================================

MISSING_THRESHOLD = 0.30

MINIMUM_AGE = 0

MAXIMUM_AGE = 120

MINIMUM_ART_AGE = 0

MAXIMUM_ART_AGE = 100

# =========================================================
# FEATURE ENGINEERING
# =========================================================

AGE_GROUP_BINS = [0, 15, 25, 35, 45, 55, 65, 120]

AGE_GROUP_LABELS = [
    "0-14",
    "15-24",
    "25-34",
    "35-44",
    "45-54",
    "55-64",
    "65+"
]

# =========================================================
# MODEL SETTINGS
# =========================================================

MODELS_TO_TRAIN = [

    "Logistic Regression",

    "Random Forest",

    "AdaBoost",

    "XGBoost"

]

# =========================================================
# DATE COLUMNS
# =========================================================

DATE_COLUMNS = [

    "Date Of Birth",

    "ART Start Date",

    "Last Drug Pickup date",

    "Last Drug Pickup date Q1",

    "Last Drug Pickup date Q2",

    "Last Drug Pickup date Q3",

    "Last Drug Pickup date Q4",

    "Last Clinic Visit Date",

    "Date Of Current Viral Load",

    "Date Of Current Viral Load Q1",

    "Date Of Current Viral Load Q2",

    "Date Of Current Viral Load Q3",

    "Date Of Current Viral Load Q4",

    "Patient Deceased Date",

    "Transferred Out Date",

    "Transferred In Date"

]

# =========================================================
# CATEGORICAL VARIABLES
# =========================================================

CATEGORICAL_COLUMNS = [

    "State",

    "LGA",

    "Sex",

    "Pregnancy Status",

    "Last Regimen"

]

# =========================================================
# NUMERICAL VARIABLES
# =========================================================

NUMERICAL_COLUMNS = [

    "Age at ART Initiation",

    "Current Age",

    "Days Of ARV Refill",

    "Current Viral Load",

    "Current Viral Load Q1",

    "Current Viral Load Q2",

    "Current Viral Load Q4"

]

# =========================================================
# LOGGING
# =========================================================

LOG_FILE = REPORTS / "logs" / "project.log"
