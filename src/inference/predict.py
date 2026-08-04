"""Leakage-safe inference utilities for the HIV LTFU predictor."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd

DEFAULT_MODEL_PATH = Path(os.getenv("LTFU_MODEL_PATH", "models/trained/logistic_regression_pipeline.joblib"))
DEFAULT_THRESHOLD = float(os.getenv("LTFU_DECISION_THRESHOLD", "0.50"))
POSITIVE_CLASS = 1


class InferenceError(RuntimeError):
    """Raised when a safe prediction cannot be produced."""


class InputSchemaError(ValueError):
    """Raised when inference data does not match the trained schema."""


@dataclass(frozen=True)
class PredictionResult:
    predicted_class: int
    predicted_label: str
    ltfu_probability: float
    retained_probability: float
    decision_threshold: float
    risk_category: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_threshold(threshold: float) -> float:
    value = float(threshold)
    if not 0.0 < value < 1.0:
        raise ValueError("threshold must be greater than 0 and less than 1.")
    return value


@lru_cache(maxsize=4)
def load_model(model_path: str | Path = DEFAULT_MODEL_PATH) -> Any:
    """Load and cache a fitted classification pipeline."""
    path = Path(model_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(
            f"Trained model not found: {path}. Set LTFU_MODEL_PATH or pass model_path explicitly."
        )
    try:
        model = joblib.load(path)
    except Exception as exc:
        raise InferenceError(f"Unable to load trained model from {path}.") from exc
    if not hasattr(model, "predict_proba"):
        raise InferenceError("Loaded object does not implement predict_proba().")
    return model


def expected_feature_names(model: Any) -> list[str] | None:
    names = getattr(model, "feature_names_in_", None)
    if names is not None:
        return [str(name) for name in names]
    named_steps = getattr(model, "named_steps", None)
    if named_steps:
        for step in named_steps.values():
            names = getattr(step, "feature_names_in_", None)
            if names is not None:
                return [str(name) for name in names]
    return None


def validate_input_schema(records: pd.DataFrame, model: Any, *, reject_extra_columns: bool = True) -> pd.DataFrame:
    if not isinstance(records, pd.DataFrame):
        raise TypeError("records must be a pandas DataFrame.")
    if records.empty:
        raise InputSchemaError("At least one patient record is required.")
    if records.columns.duplicated().any():
        duplicated = records.columns[records.columns.duplicated()].tolist()
        raise InputSchemaError(f"Duplicate input columns detected: {duplicated}")

    expected = expected_feature_names(model)
    if expected is None:
        return records.copy()

    supplied = [str(column) for column in records.columns]
    missing = sorted(set(expected) - set(supplied))
    extra = sorted(set(supplied) - set(expected))
    if missing:
        raise InputSchemaError("Missing required model feature(s): " + ", ".join(missing))
    if reject_extra_columns and extra:
        raise InputSchemaError("Unexpected input feature(s): " + ", ".join(extra))
    return records.loc[:, expected].copy()


def _positive_class_index(model: Any) -> int:
    classes = getattr(model, "classes_", None)
    if classes is None and getattr(model, "named_steps", None):
        classes = getattr(list(model.named_steps.values())[-1], "classes_", None)
    if classes is None:
        return 1
    classes_array = np.asarray(classes)
    matches = np.flatnonzero(classes_array == POSITIVE_CLASS)
    if matches.size != 1:
        raise InferenceError(f"Expected positive class 1; found {classes_array.tolist()}.")
    return int(matches[0])


def probability_to_risk_category(probability: float) -> str:
    if probability < 0.30:
        return "Low"
    if probability < 0.70:
        return "Moderate"
    return "High"


def predict_batch(
    records: pd.DataFrame,
    *,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    threshold: float = DEFAULT_THRESHOLD,
    reject_extra_columns: bool = True,
) -> pd.DataFrame:
    """Predict LTFU risk without fitting or refitting any component."""
    threshold = _validate_threshold(threshold)
    model = load_model(model_path)
    X = validate_input_schema(records, model, reject_extra_columns=reject_extra_columns)
    try:
        probabilities = np.asarray(model.predict_proba(X), dtype=float)
    except Exception as exc:
        raise InferenceError(
            "Prediction failed. Check input values, dtypes, missing-value handling, and categorical values."
        ) from exc
    if probabilities.ndim != 2 or probabilities.shape[0] != len(X):
        raise InferenceError(f"Unexpected predict_proba output shape: {probabilities.shape}.")
    positive_index = _positive_class_index(model)
    ltfu_probability = probabilities[:, positive_index]
    if not np.isfinite(ltfu_probability).all() or ((ltfu_probability < 0) | (ltfu_probability > 1)).any():
        raise InferenceError("Model returned invalid probability values.")

    predicted_class = (ltfu_probability >= threshold).astype(int)
    return pd.DataFrame(
        {
            "predicted_class": predicted_class,
            "predicted_label": np.where(predicted_class == 1, "LTFU", "Retained"),
            "ltfu_probability": ltfu_probability,
            "retained_probability": 1.0 - ltfu_probability,
            "decision_threshold": threshold,
            "risk_category": [probability_to_risk_category(float(v)) for v in ltfu_probability],
        },
        index=records.index,
    )


def predict_patient(
    patient: Mapping[str, Any],
    *,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    threshold: float = DEFAULT_THRESHOLD,
    reject_extra_columns: bool = True,
) -> PredictionResult:
    if not isinstance(patient, Mapping):
        raise TypeError("patient must be a mapping of feature names to values.")
    row = predict_batch(
        pd.DataFrame([dict(patient)]),
        model_path=model_path,
        threshold=threshold,
        reject_extra_columns=reject_extra_columns,
    ).iloc[0]
    return PredictionResult(
        predicted_class=int(row["predicted_class"]),
        predicted_label=str(row["predicted_label"]),
        ltfu_probability=float(row["ltfu_probability"]),
        retained_probability=float(row["retained_probability"]),
        decision_threshold=float(row["decision_threshold"]),
        risk_category=str(row["risk_category"]),
    )


def _read_input(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, Mapping):
            payload = [payload]
        if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes)):
            raise InputSchemaError("JSON input must be one object or a list of objects.")
        return pd.DataFrame(payload)
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError("Input format must be .json, .csv, .parquet, or .pq.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run leakage-safe LTFU model inference.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-extra-columns", action="store_true")
    args = parser.parse_args()

    records = _read_input(args.input)
    predictions = predict_batch(
        records,
        model_path=args.model,
        threshold=args.threshold,
        reject_extra_columns=not args.allow_extra_columns,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        predictions.to_csv(args.output, index=False)
        print(f"Predictions saved to: {args.output.resolve()}")
    else:
        print(predictions.to_json(orient="records", indent=2))


if __name__ == "__main__":
    main()
