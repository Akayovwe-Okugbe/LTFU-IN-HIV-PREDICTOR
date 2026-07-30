"""
=========================================================
Model Persistence

Saves trained model pipelines and training metadata.

=========================================================
"""

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import joblib
import pandas as pd
import sklearn
import xgboost

from src.config import (
    TRAINED_MODELS_DIR,
    TRAINING_METADATA_PATH,
)

from src.logger import logger


# =====================================================
# CREATE OUTPUT DIRECTORY
# =====================================================

def _create_model_directory() -> None:
    """
    Creates the trained-model directory if it does not
    already exist.
    """

    TRAINED_MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


# =====================================================
# SAVE TRAINED MODEL
# =====================================================

def save_model(
    model: Any,
    file_path: Path,
    model_name: str,
) -> None:
    """
    Saves a fitted model pipeline using joblib.

    Parameters
    ----------
    model : Any
        Fitted model or pipeline.

    file_path : pathlib.Path
        Destination for the serialised model.

    model_name : str
        Human-readable model name used in logs.
    """

    _create_model_directory()

    file_path = Path(file_path)

    try:
        joblib.dump(
            model,
            file_path,
            compress=3,
        )

    except Exception as error:
        raise RuntimeError(
            f"Unable to save the {model_name} model "
            f"to {file_path}."
        ) from error

    file_size_mb = (
        file_path.stat().st_size
        / (1024 ** 2)
    )

    logger.info(
        "%s model saved successfully.",
        model_name,
    )

    logger.info(
        "Location: %s",
        file_path,
    )

    logger.info(
        "File size: %.2f MB",
        file_size_mb,
    )


# =====================================================
# SAVE TRAINING METADATA
# =====================================================

def save_training_metadata(
    metadata: Dict[str, Any],
) -> None:
    """
    Saves information needed to reproduce or audit the
    model-training run.
    """

    _create_model_directory()

    complete_metadata = {
        "training_timestamp_utc": (
            datetime.now(timezone.utc).isoformat()
        ),
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "scikit_learn_version": sklearn.__version__,
        "xgboost_version": xgboost.__version__,
        **metadata,
    }

    try:
        with open(
            TRAINING_METADATA_PATH,
            "w",
            encoding="utf-8",
        ) as metadata_file:
            json.dump(
                complete_metadata,
                metadata_file,
                indent=4,
                ensure_ascii=False,
            )

    except Exception as error:
        raise RuntimeError(
            "Unable to save the model-training metadata."
        ) from error

    logger.info(
        "Training metadata saved successfully."
    )

    logger.info(
        "Location: %s",
        TRAINING_METADATA_PATH,
    )
