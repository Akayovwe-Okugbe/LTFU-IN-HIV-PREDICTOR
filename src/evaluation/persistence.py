"""
=========================================================
Evaluation Persistence Utilities

Provides reusable functions for:

- creating evaluation directories;
- loading trained models;
- saving JSON safely;
- saving model metrics;
- saving prediction outputs.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd


def create_evaluation_directories(
    directories,
) -> None:
    """
    Creates all required evaluation directories.
    """

    for directory in directories:
        Path(directory).mkdir(
            parents=True,
            exist_ok=True,
        )


def load_trained_model(
    model_path: Path,
):
    """
    Loads a fitted joblib model pipeline.
    """

    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(
            "Trained model file was not found: "
            f"{model_path}"
        )

    model = joblib.load(model_path)

    if not hasattr(model, "predict"):
        raise TypeError(
            f"The object loaded from {model_path} "
            "does not implement predict()."
        )

    if not hasattr(model, "predict_proba"):
        raise TypeError(
            f"The object loaded from {model_path} "
            "does not implement predict_proba()."
        )

    return model


def _convert_to_json_compatible(
    value: Any,
) -> Any:
    """
    Recursively converts NumPy and pandas values to
    standard JSON-compatible Python values.
    """

    if isinstance(
        value,
        (np.integer,),
    ):
        return int(value)

    if isinstance(
        value,
        (np.floating,),
    ):
        return float(value)

    if isinstance(
        value,
        (np.bool_,),
    ):
        return bool(value)

    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): _convert_to_json_compatible(
                item
            )
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _convert_to_json_compatible(item)
            for item in value
        ]

    return value


def save_json(
    content: Dict[str, Any],
    output_path: Path,
) -> None:
    """
    Saves a dictionary as formatted UTF-8 JSON.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    serialisable_content = (
        _convert_to_json_compatible(
            content
        )
    )

    with output_path.open(
        mode="w",
        encoding="utf-8",
    ) as file:
        json.dump(
            serialisable_content,
            file,
            indent=4,
            ensure_ascii=False,
        )
