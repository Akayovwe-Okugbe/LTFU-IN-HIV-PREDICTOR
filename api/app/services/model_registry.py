"""Synchronise selected MEDISCOPE model artifacts with model_registry."""
from __future__ import annotations
from datetime import UTC, datetime
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.entities import ModelRegistry

FEATURE_SCHEMA_VERSION = 'ltfu-feature-schema-v1'
MODEL_VERSION = '2026-07-30-v1'
TRAINED_AT = datetime(2026, 7, 30, tzinfo=UTC)
LOGISTIC_METRICS = {'balanced_accuracy':0.9849,'precision':0.9864,'recall_sensitivity':0.9824,'specificity':0.9873,'f1_score':0.9844,'roc_auc':0.9983,'pr_auc_average_precision':0.9985}
XGBOOST_METRICS = {'balanced_accuracy':0.9714,'precision':0.9712,'recall_sensitivity':0.9696,'specificity':0.9732,'f1_score':0.9704,'roc_auc':0.9965,'pr_auc_average_precision':0.9965}

class ModelRegistryError(RuntimeError):
    """Raised when deployed model metadata cannot be prepared safely."""

def _normalise_artifact_path(path_value: str) -> str:
    path = Path(path_value)
    if not path.is_absolute(): path = Path.cwd() / path
    path = path.resolve()
    if not path.exists(): raise ModelRegistryError(f'Model artifact does not exist: {path}')
    return str(path)

def _upsert_model(db: Session, *, model_name: str, algorithm: str, artifact_path: str, evaluation_metrics: dict[str,float]) -> ModelRegistry:
    settings = get_settings()
    record = db.scalar(select(ModelRegistry).where(ModelRegistry.model_name==model_name, ModelRegistry.model_version==MODEL_VERSION))
    if record is None:
        record = ModelRegistry(model_name=model_name, model_version=MODEL_VERSION, algorithm=algorithm, artifact_path=artifact_path, trained_at=TRAINED_AT, threshold=settings.decision_threshold, feature_schema_version=FEATURE_SCHEMA_VERSION, evaluation_metrics=evaluation_metrics, is_active=True)
        db.add(record)
    else:
        record.algorithm=algorithm; record.artifact_path=artifact_path; record.threshold=settings.decision_threshold; record.feature_schema_version=FEATURE_SCHEMA_VERSION; record.evaluation_metrics=evaluation_metrics; record.is_active=True
    return record

def ensure_active_model_registry(db: Session) -> tuple[ModelRegistry, ModelRegistry]:
    settings = get_settings()
    logistic = _upsert_model(db, model_name='Logistic Regression', algorithm='LogisticRegression', artifact_path=_normalise_artifact_path(settings.logistic_model_path), evaluation_metrics=LOGISTIC_METRICS)
    xgboost = _upsert_model(db, model_name='XGBoost', algorithm='XGBClassifier', artifact_path=_normalise_artifact_path(settings.xgboost_model_path), evaluation_metrics=XGBOOST_METRICS)
    db.flush()
    return logistic, xgboost
