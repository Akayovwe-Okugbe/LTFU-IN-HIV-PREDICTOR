from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.inference.predict import InputSchemaError, load_model, predict_batch, predict_patient


@pytest.fixture()
def fitted_pipeline(tmp_path: Path) -> Path:
    X = pd.DataFrame({
        "Current Age": [20, 25, 31, 38, 45, 52, 60, 67],
        "Age at ART Initiation": [18, 20, 25, 32, 39, 45, 51, 58],
        "Days Of ARV Refill": [90, 90, 60, 60, 30, 30, 30, 30],
        "Sex": ["Female", "Female", "Male", "Female", "Male", "Female", "Male", "Male"],
        "Last Regimen": ["TDF+3TC+DTG", "TDF+3TC+DTG", "TDF+3TC+DTG", "ABC+3TC+DTG", "AZT-3TC-NVP", "AZT-3TC-NVP", "AZT-3TC-NVP", "AZT-3TC-NVP"],
    })
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    numeric = ["Current Age", "Age at ART Initiation", "Days Of ARV Refill"]
    categorical = ["Sex", "Last Regimen"]
    preprocessor = ColumnTransformer([
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric),
        ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore"))]), categorical),
    ])
    pipeline = Pipeline([("preprocessor", preprocessor), ("classifier", LogisticRegression(random_state=42))])
    pipeline.fit(X, y)
    path = tmp_path / "logistic_regression_pipeline.joblib"
    joblib.dump(pipeline, path)
    load_model.cache_clear()
    return path


def valid_patient() -> dict:
    return {
        "Current Age": 48,
        "Age at ART Initiation": 40,
        "Days Of ARV Refill": 30,
        "Sex": "Female",
        "Last Regimen": "TDF+3TC+DTG",
    }


def test_single_patient_prediction(fitted_pipeline: Path) -> None:
    result = predict_patient(valid_patient(), model_path=fitted_pipeline)
    assert result.predicted_class in {0, 1}
    assert result.predicted_label in {"Retained", "LTFU"}
    assert 0.0 <= result.ltfu_probability <= 1.0
    assert result.ltfu_probability + result.retained_probability == pytest.approx(1.0)
    assert result.risk_category in {"Low", "Moderate", "High"}


def test_batch_prediction_preserves_rows(fitted_pipeline: Path) -> None:
    output = predict_batch(pd.DataFrame([valid_patient(), valid_patient()]), model_path=fitted_pipeline)
    assert len(output) == 2


def test_column_order_is_corrected(fitted_pipeline: Path) -> None:
    records = pd.DataFrame([valid_patient()])[list(reversed(valid_patient().keys()))]
    assert len(predict_batch(records, model_path=fitted_pipeline)) == 1


def test_missing_feature_is_rejected(fitted_pipeline: Path) -> None:
    patient = valid_patient(); patient.pop("Current Age")
    with pytest.raises(InputSchemaError, match="Missing required"):
        predict_patient(patient, model_path=fitted_pipeline)


def test_extra_feature_is_rejected(fitted_pipeline: Path) -> None:
    patient = valid_patient(); patient["Patient Number"] = "PRIVATE-ID"
    with pytest.raises(InputSchemaError, match="Unexpected input"):
        predict_patient(patient, model_path=fitted_pipeline)


def test_unknown_category_is_handled(fitted_pipeline: Path) -> None:
    patient = valid_patient(); patient["Last Regimen"] = "NEW-UNSEEN-REGIMEN"
    assert 0.0 <= predict_patient(patient, model_path=fitted_pipeline).ltfu_probability <= 1.0


def test_invalid_threshold_is_rejected(fitted_pipeline: Path) -> None:
    with pytest.raises(ValueError, match="threshold"):
        predict_patient(valid_patient(), model_path=fitted_pipeline, threshold=1.0)
