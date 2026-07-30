"""
=========================================================
Dataset Splitting

LTFU Prediction in HIV Treatment Programmes

Splits the feature engineered dataset into
training and testing sets and optionally saves them.

Author:
    Akayovwe Okugbe
=========================================================
"""

from pathlib import Path

import pandas as pd

from sklearn.model_selection import train_test_split

from src.config import (
    PROCESSED_DATA,
    TEST_SIZE,
    RANDOM_STATE
)

from src.logger import logger

from src.utils import save_dataframe


def split_data(
    df: pd.DataFrame,
    target: str = "Target",
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
):
    """
    Splits dataset into train and test sets.
    """

    X = df.drop(columns=[target])

    y = df[target]

    return train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )


def save_split_data(
    X_train,
    X_test,
    y_train,
    y_test,
):
    """
    Saves train/test datasets.
    """

    train_df = X_train.copy()
    train_df["Target"] = y_train

    test_df = X_test.copy()
    test_df["Target"] = y_test

    train_path = PROCESSED_DATA / "03_train.parquet"
    test_path = PROCESSED_DATA / "03_test.parquet"

    save_dataframe(train_df, train_path)
    save_dataframe(test_df, test_path)

    logger.info("Training dataset saved.")
    logger.info(train_path)

    logger.info("Testing dataset saved.")
    logger.info(test_path)
