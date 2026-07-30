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
# EVALUATION PATHS
# =========================================================

EVALUATION_DIR = REPORTS / "evaluation"

EVALUATION_METRICS_DIR = EVALUATION_DIR / "metrics"

EVALUATION_PREDICTIONS_DIR = (
    EVALUATION_DIR / "predictions"
)

EVALUATION_PLOTS_DIR = EVALUATION_DIR / "plots"

FEATURE_IMPORTANCE_DIR = (
    EVALUATION_DIR / "feature_importance"
)

MODEL_COMPARISON_CSV_PATH = (
    EVALUATION_METRICS_DIR / "model_comparison.csv"
)

MODEL_COMPARISON_JSON_PATH = (
    EVALUATION_METRICS_DIR / "model_comparison.json"
)

TEST_PREDICTIONS_PATH = (
    EVALUATION_PREDICTIONS_DIR
    / "test_predictions.parquet"
)

EVALUATION_METADATA_PATH = (
    EVALUATION_DIR / "evaluation_metadata.json"
)


# =========================================================
# EVALUATION SETTINGS
# =========================================================

CLASSIFICATION_THRESHOLD = 0.50

TOP_FEATURES_TO_PLOT = 20

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


# =====================================================
# MODEL-TRAINING CONFIGURATION
# =====================================================

# Name of the binary target variable.
TARGET_COLUMN = "Target"

# Random seed used across all models.
RANDOM_STATE = 42

# Number of CPU cores used by compatible estimators.
# -1 instructs the estimator to use all available cores.
N_JOBS = -1

# Folder used to store trained model pipelines.
TRAINED_MODELS_DIR = PROJECT_ROOT / "models" / "trained"

# Feature-engineered training and testing datasets.
TRAIN_DATA_PATH = PROCESSED_DATA / "03_train.parquet"
TEST_DATA_PATH = PROCESSED_DATA / "03_test.parquet"

# Individual model output paths.
LOGISTIC_REGRESSION_MODEL_PATH = (
    TRAINED_MODELS_DIR / "logistic_regression_pipeline.joblib"
)

RANDOM_FOREST_MODEL_PATH = (
    TRAINED_MODELS_DIR / "random_forest_pipeline.joblib"
)

ADABOOST_MODEL_PATH = (
    TRAINED_MODELS_DIR / "adaboost_pipeline.joblib"
)

XGBOOST_MODEL_PATH = (
    TRAINED_MODELS_DIR / "xgboost_pipeline.joblib"
)

# Stores information about the training run, feature names,
# class balance and package versions.
TRAINING_METADATA_PATH = (
    TRAINED_MODELS_DIR / "training_metadata.json"
)
