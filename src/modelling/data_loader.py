"""
=========================================================
Modelling Data Loader

Loads the prepared train and test datasets and performs
the final structural checks required before model fitting.

=========================================================
"""

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from src.config import (
    TARGET_COLUMN,
    TRAIN_DATA_PATH,
    TEST_DATA_PATH,
)

from src.logger import logger


# =====================================================
# LOAD PARQUET DATASET
# =====================================================

def _load_parquet_dataset(
    file_path: Path,
    dataset_name: str,
) -> pd.DataFrame:
    """
    Loads a parquet dataset and confirms that it exists.

    Parameters
    ----------
    file_path : pathlib.Path
        Location of the parquet file.

    dataset_name : str
        Human-readable dataset name used in log messages.

    Returns
    -------
    pandas.DataFrame
        Loaded dataset.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"{dataset_name} dataset was not found: "
            f"{file_path}"
        )

    logger.info(
        "Loading %s dataset...",
        dataset_name,
    )

    logger.info(
        "Source: %s",
        file_path,
    )

    try:
        dataframe = pd.read_parquet(file_path)

    except Exception as error:
        raise RuntimeError(
            f"Unable to load the {dataset_name} dataset "
            f"from {file_path}."
        ) from error

    if dataframe.empty:
        raise ValueError(
            f"The {dataset_name} dataset is empty."
        )

    logger.info(
        "%s dataset loaded successfully "
        "(%s rows × %s columns).",
        dataset_name.capitalize(),
        f"{dataframe.shape[0]:,}",
        f"{dataframe.shape[1]:,}",
    )

    return dataframe


# =====================================================
# LOAD TRAINING DATA
# =====================================================

def load_training_dataset() -> pd.DataFrame:
    """
    Loads the feature-engineered training dataset.
    """

    return _load_parquet_dataset(
        TRAIN_DATA_PATH,
        "training",
    )


# =====================================================
# LOAD TESTING DATA
# =====================================================

def load_testing_dataset() -> pd.DataFrame:
    """
    Loads the held-out testing dataset.

    The testing dataset is loaded during training only
    to verify that it has the same schema as the training
    dataset. It is not used to fit the models.
    """

    return _load_parquet_dataset(
        TEST_DATA_PATH,
        "testing",
    )


# =====================================================
# VALIDATE MODELLING DATA
# =====================================================

def validate_modelling_dataset(
    dataframe: pd.DataFrame,
    dataset_name: str,
) -> None:
    """
    Validates a prepared modelling dataset.

    The function confirms that:

    - the target exists;
    - the target has no missing values;
    - the target contains only 0 and 1;
    - no datetime columns remain;
    - no unencoded categorical columns remain;
    - no infinite numeric values remain.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Dataset to validate.

    dataset_name : str
        Name used in error and log messages.
    """

    if TARGET_COLUMN not in dataframe.columns:
        raise KeyError(
            f"The target column '{TARGET_COLUMN}' is "
            f"missing from the {dataset_name} dataset."
        )

    missing_target_count = int(
        dataframe[TARGET_COLUMN].isna().sum()
    )

    if missing_target_count > 0:
        raise ValueError(
            f"The {dataset_name} target contains "
            f"{missing_target_count:,} missing values."
        )

    target_values = set(
        dataframe[TARGET_COLUMN]
        .dropna()
        .unique()
        .tolist()
    )

    invalid_target_values = target_values - {0, 1}

    if invalid_target_values:
        raise ValueError(
            f"The {dataset_name} target contains "
            f"unexpected values: {invalid_target_values}"
        )

    feature_data = dataframe.drop(
        columns=[TARGET_COLUMN]
    )

    datetime_columns = feature_data.select_dtypes(
        include=[
            "datetime",
            "datetimetz",
        ]
    ).columns.tolist()

    categorical_columns = feature_data.select_dtypes(
        include=[
            "object",
            "string",
            "category",
        ]
    ).columns.tolist()

    if datetime_columns:
        raise TypeError(
            f"Datetime columns remain in the "
            f"{dataset_name} dataset: "
            f"{datetime_columns}"
        )

    if categorical_columns:
        raise TypeError(
            f"Unencoded categorical columns remain in "
            f"the {dataset_name} dataset: "
            f"{categorical_columns}"
        )

    numeric_columns = feature_data.select_dtypes(
        include=["number"]
    ).columns

    infinite_count = int(
        np.isinf(
            feature_data[numeric_columns]
            .to_numpy(dtype=float)
        ).sum()
    )

    if infinite_count > 0:
        raise ValueError(
            f"The {dataset_name} dataset contains "
            f"{infinite_count:,} infinite numeric values."
        )

    duplicate_feature_names = (
        feature_data.columns[
            feature_data.columns.duplicated()
        ].tolist()
    )

    if duplicate_feature_names:
        raise ValueError(
            f"The {dataset_name} dataset contains "
            f"duplicate feature names: "
            f"{duplicate_feature_names}"
        )

    logger.info(
        "%s dataset validation completed successfully.",
        dataset_name.capitalize(),
    )


# =====================================================
# SPLIT FEATURES AND TARGET
# =====================================================

def split_features_target(
    dataframe: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Separates predictor variables from the target.

    Returns
    -------
    tuple
        X containing predictors and y containing the
        binary target.
    """

    X = dataframe.drop(
        columns=[TARGET_COLUMN]
    ).copy()

    y = (
        dataframe[TARGET_COLUMN]
        .astype("int8")
        .copy()
    )

    return X, y
