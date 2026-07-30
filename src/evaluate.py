"""
=========================================================
Final Model Evaluation Entry Point

Evaluates all fitted machine-learning pipelines using
the untouched held-out dataset:

    data/processed/03_test.parquet

Leakage safeguards
------------------
1. The test dataset is loaded only after training.
2. No model is fitted or refitted in this script.
3. Saved preprocessing pipelines are reused unchanged.
4. A fixed probability threshold of 0.50 is applied.
5. No threshold or hyperparameter optimisation is
   performed using test outcomes.
6. Evaluation outputs are saved for reproducibility.

Run
---
python -m src.evaluate

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations

import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import joblib
import matplotlib
import numpy as np
import pandas as pd
import sklearn

try:
    import xgboost
except ImportError:
    xgboost = None

from src.config import (
    ADABOOST_MODEL_PATH,
    CLASSIFICATION_THRESHOLD,
    EVALUATION_DIR,
    EVALUATION_METADATA_PATH,
    EVALUATION_METRICS_DIR,
    EVALUATION_PLOTS_DIR,
    EVALUATION_PREDICTIONS_DIR,
    FEATURE_IMPORTANCE_DIR,
    LOGISTIC_REGRESSION_MODEL_PATH,
    MODEL_COMPARISON_CSV_PATH,
    MODEL_COMPARISON_JSON_PATH,
    RANDOM_FOREST_MODEL_PATH,
    TARGET_COLUMN,
    TEST_DATA_PATH,
    TEST_PREDICTIONS_PATH,
    TOP_FEATURES_TO_PLOT,
    XGBOOST_MODEL_PATH,
)

from src.evaluation.feature_importance import (
    extract_feature_importance,
    save_feature_importance_plot,
    save_feature_importance_table,
)

from src.evaluation.metrics import (
    calculate_binary_classification_metrics,
)

from src.evaluation.persistence import (
    create_evaluation_directories,
    load_trained_model,
    save_json,
)

from src.evaluation.plots import (
    save_calibration_curves,
    save_combined_precision_recall_curve,
    save_combined_roc_curve,
    save_confusion_matrix_plot,
    save_model_comparison_plot,
)

from src.logger import logger


# =====================================================
# MODEL REGISTRY
# =====================================================

MODEL_REGISTRY = {
    "logistic_regression": {
        "display_name": "Logistic Regression",
        "path": LOGISTIC_REGRESSION_MODEL_PATH,
    },
    "random_forest": {
        "display_name": "Random Forest",
        "path": RANDOM_FOREST_MODEL_PATH,
    },
    "adaboost": {
        "display_name": "AdaBoost",
        "path": ADABOOST_MODEL_PATH,
    },
    "xgboost": {
        "display_name": "XGBoost",
        "path": XGBOOST_MODEL_PATH,
    },
}


# =====================================================
# CONSOLE FORMATTING
# =====================================================

def print_main_heading(
    heading: str,
) -> None:
    """
    Prints a major console heading.
    """

    print()
    print("=" * 70)
    print(heading)
    print("=" * 70)


def print_section(
    heading: str,
) -> None:
    """
    Prints a console section heading.
    """

    print()
    print("-" * 60)
    print(heading)
    print("-" * 60)


# =====================================================
# TEST DATA LOADING
# =====================================================

def load_locked_test_dataset():
    """
    Loads and validates the held-out test dataset.

    The target is separated from the predictors without
    making any modifications to model features.
    """

    logger.info(
        "Loading locked held-out test dataset..."
    )

    logger.info(
        "Source: %s",
        TEST_DATA_PATH,
    )

    test_path = Path(TEST_DATA_PATH)

    if not test_path.exists():
        raise FileNotFoundError(
            "Test dataset was not found: "
            f"{test_path}"
        )

    test_data = pd.read_parquet(
        test_path
    )

    logger.info(
        "Test dataset loaded successfully "
        "(%s rows × %s columns).",
        f"{test_data.shape[0]:,}",
        f"{test_data.shape[1]:,}",
    )

    if TARGET_COLUMN not in test_data.columns:
        raise KeyError(
            f"Target column '{TARGET_COLUMN}' was not "
            "found in the test dataset."
        )

    if test_data[TARGET_COLUMN].isna().any():
        raise ValueError(
            "The test target contains missing values."
        )

    target_values = set(
        test_data[TARGET_COLUMN]
        .astype(int)
        .unique()
        .tolist()
    )

    if not target_values.issubset({0, 1}):
        raise ValueError(
            "The test target contains values other than "
            "zero and one."
        )

    X_test = test_data.drop(
        columns=[TARGET_COLUMN]
    )

    y_test = (
        test_data[TARGET_COLUMN]
        .astype(int)
        .copy()
    )

    if X_test.empty:
        raise ValueError(
            "The held-out test predictor matrix is "
            "empty."
        )

    logger.info(
        "Held-out predictor matrix: "
        "%s rows × %s features.",
        f"{X_test.shape[0]:,}",
        f"{X_test.shape[1]:,}",
    )

    logger.info(
        "Held-out class 0 records: %s",
        f"{int((y_test == 0).sum()):,}",
    )

    logger.info(
        "Held-out class 1 records: %s",
        f"{int((y_test == 1).sum()):,}",
    )

    return X_test, y_test


# =====================================================
# MODEL EVALUATION
# =====================================================

def evaluate_single_model(
    model_key: str,
    display_name: str,
    model_path: Path,
    X_test: pd.DataFrame,
    y_test: pd.Series,
):
    """
    Loads and evaluates one trained pipeline.

    No fitting is performed.
    """

    logger.info(
        "Loading %s...",
        display_name,
    )

    model = load_trained_model(
        model_path
    )

    logger.info(
        "%s loaded successfully.",
        display_name,
    )

    start_time = time.perf_counter()

    probabilities = model.predict_proba(
        X_test
    )

    if probabilities.ndim != 2:
        raise ValueError(
            f"{display_name} returned an invalid "
            "probability array."
        )

    classifier = model.named_steps.get(
        "classifier"
    )

    if classifier is None:
        raise KeyError(
            f"{display_name} does not contain a "
            "'classifier' pipeline step."
        )

    classes = np.asarray(
        classifier.classes_
    )

    positive_class_positions = np.where(
        classes == 1
    )[0]

    if len(positive_class_positions) != 1:
        raise ValueError(
            f"{display_name} does not expose exactly one "
            "probability column for class 1."
        )

    positive_class_index = int(
        positive_class_positions[0]
    )

    y_probability = probabilities[
        :,
        positive_class_index,
    ]

    # A fixed threshold is used for every model.
    # It is not adjusted using the held-out test labels.
    y_pred = (
        y_probability
        >= CLASSIFICATION_THRESHOLD
    ).astype(int)

    prediction_seconds = (
        time.perf_counter() - start_time
    )

    metrics = (
        calculate_binary_classification_metrics(
            y_true=y_test,
            y_pred=y_pred,
            y_probability=y_probability,
        )
    )

    metrics.update(
        {
            "model": display_name,
            "model_key": model_key,
            "classification_threshold": float(
                CLASSIFICATION_THRESHOLD
            ),
            "prediction_seconds": float(
                prediction_seconds
            ),
            "predictions_per_second": float(
                len(X_test)
                / prediction_seconds
            )
            if prediction_seconds > 0
            else None,
            "model_path": str(model_path),
            "model_file_size_bytes": int(
                Path(model_path).stat().st_size
            ),
        }
    )

    logger.info(
        "%s evaluation completed in %.2f seconds.",
        display_name,
        prediction_seconds,
    )

    logger.info(
        "%s — Recall: %.4f | Precision: %.4f | "
        "F1: %.4f | ROC-AUC: %.4f | PR-AUC: %.4f",
        display_name,
        metrics["recall_sensitivity"],
        metrics["precision"],
        metrics["f1_score"],
        metrics["roc_auc"],
        metrics[
            "pr_auc_average_precision"
        ],
    )

    return (
        model,
        metrics,
        y_pred,
        y_probability,
    )


# =====================================================
# MAIN EVALUATION PIPELINE
# =====================================================

def evaluate_models() -> None:
    """
    Runs the complete held-out evaluation workflow.
    """

    logger.info("=" * 60)
    logger.info(
        "STARTING FINAL MODEL EVALUATION"
    )
    logger.info("=" * 60)

    print_main_heading(
        "FINAL MODEL EVALUATION"
    )

    pipeline_start = time.perf_counter()

    create_evaluation_directories(
        [
            EVALUATION_DIR,
            EVALUATION_METRICS_DIR,
            EVALUATION_PREDICTIONS_DIR,
            EVALUATION_PLOTS_DIR,
            FEATURE_IMPORTANCE_DIR,
        ]
    )

    print_section(
        "Loading Locked Held-Out Test Data"
    )

    X_test, y_test = (
        load_locked_test_dataset()
    )

    all_metrics: list[dict[str, Any]] = []

    all_probabilities: Dict[
        str,
        np.ndarray,
    ] = {}

    predictions_output = pd.DataFrame(
        {
            "actual_outcome": (
                y_test.to_numpy()
            )
        }
    )

    print_section(
        "Evaluating Saved Models"
    )

    for model_key, details in (
        MODEL_REGISTRY.items()
    ):
        display_name = details[
            "display_name"
        ]

        model_path = details["path"]

        logger.info("-" * 60)
        logger.info(
            "Evaluating %s",
            display_name,
        )

        (
            model,
            metrics,
            y_pred,
            y_probability,
        ) = evaluate_single_model(
            model_key=model_key,
            display_name=display_name,
            model_path=model_path,
            X_test=X_test,
            y_test=y_test,
        )

        all_metrics.append(metrics)

        all_probabilities[
            display_name
        ] = y_probability

        predictions_output[
            f"{model_key}_probability"
        ] = y_probability

        predictions_output[
            f"{model_key}_prediction"
        ] = y_pred

        model_metrics_path = (
            EVALUATION_METRICS_DIR
            / f"{model_key}_metrics.json"
        )

        save_json(
            metrics,
            model_metrics_path,
        )

        confusion_matrix_path = (
            EVALUATION_PLOTS_DIR
            / (
                f"{model_key}"
                "_confusion_matrix.png"
            )
        )

        save_confusion_matrix_plot(
            y_true=y_test,
            y_pred=y_pred,
            model_name=display_name,
            output_path=(
                confusion_matrix_path
            ),
        )

        importance = (
            extract_feature_importance(
                pipeline=model,
                model_name=display_name,
            )
        )

        if importance is not None:
            importance_csv_path = (
                FEATURE_IMPORTANCE_DIR
                / (
                    f"{model_key}"
                    "_feature_importance.csv"
                )
            )

            importance_plot_path = (
                FEATURE_IMPORTANCE_DIR
                / (
                    f"{model_key}"
                    "_feature_importance.png"
                )
            )

            save_feature_importance_table(
                importance=importance,
                output_path=(
                    importance_csv_path
                ),
            )

            save_feature_importance_plot(
                importance=importance,
                model_name=display_name,
                output_path=(
                    importance_plot_path
                ),
                top_n=TOP_FEATURES_TO_PLOT,
            )

            logger.info(
                "%s feature importance saved.",
                display_name,
            )

    print_section(
        "Saving Predictions and Comparison Results"
    )

    predictions_output.to_parquet(
        TEST_PREDICTIONS_PATH,
        index=False,
    )

    logger.info(
        "Test predictions saved successfully."
    )

    logger.info(
        "Location: %s",
        TEST_PREDICTIONS_PATH,
    )

    comparison = pd.DataFrame(
        all_metrics
    )

    preferred_column_order = [
        "model",
        "classification_threshold",
        "test_records",
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall_sensitivity",
        "specificity",
        "negative_predictive_value",
        "f1_score",
        "roc_auc",
        "pr_auc_average_precision",
        "matthews_correlation_coefficient",
        "brier_score",
        "log_loss",
        "true_negatives",
        "false_positives",
        "false_negatives",
        "true_positives",
        "prediction_seconds",
        "predictions_per_second",
        "model_file_size_bytes",
        "model_key",
        "model_path",
    ]

    available_ordered_columns = [
        column
        for column in preferred_column_order
        if column in comparison.columns
    ]

    remaining_columns = [
        column
        for column in comparison.columns
        if column
        not in available_ordered_columns
    ]

    comparison = comparison[
        available_ordered_columns
        + remaining_columns
    ]

    # This ordering is descriptive only. It must not be
    # used to tune and rerun models against this test set.
    comparison = comparison.sort_values(
        by=[
            "pr_auc_average_precision",
            "recall_sensitivity",
            "f1_score",
        ],
        ascending=False,
    ).reset_index(drop=True)

    comparison.insert(
        0,
        "descriptive_test_rank",
        np.arange(
            1,
            len(comparison) + 1,
        ),
    )

    comparison.to_csv(
        MODEL_COMPARISON_CSV_PATH,
        index=False,
    )

    save_json(
        {
            "warning": (
                "The descriptive test rank is for final "
                "reporting only. It must not be used for "
                "further test-driven tuning."
            ),
            "models": comparison.to_dict(
                orient="records"
            ),
        },
        MODEL_COMPARISON_JSON_PATH,
    )

    print_section(
        "Creating Evaluation Plots"
    )

    save_combined_roc_curve(
        y_true=y_test,
        probabilities=all_probabilities,
        output_path=(
            EVALUATION_PLOTS_DIR
            / "roc_curves.png"
        ),
    )

    save_combined_precision_recall_curve(
        y_true=y_test,
        probabilities=all_probabilities,
        output_path=(
            EVALUATION_PLOTS_DIR
            / "precision_recall_curves.png"
        ),
    )

    save_calibration_curves(
        y_true=y_test,
        probabilities=all_probabilities,
        output_path=(
            EVALUATION_PLOTS_DIR
            / "calibration_curves.png"
        ),
    )

    save_model_comparison_plot(
        comparison=comparison,
        output_path=(
            EVALUATION_PLOTS_DIR
            / "model_comparison.png"
        ),
    )

    total_seconds = (
        time.perf_counter()
        - pipeline_start
    )

    print_section(
        "Saving Evaluation Metadata"
    )

    metadata = {
        "evaluation_timestamp_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "evaluation_type": (
            "locked_held_out_test_evaluation"
        ),
        "test_dataset_path": str(
            TEST_DATA_PATH
        ),
        "test_records": int(
            len(X_test)
        ),
        "predictor_features": int(
            X_test.shape[1]
        ),
        "target_column": TARGET_COLUMN,
        "classification_threshold": float(
            CLASSIFICATION_THRESHOLD
        ),
        "positive_class": {
            "value": 1,
            "meaning": (
                "Inactive or loss to follow-up"
            ),
        },
        "negative_class": {
            "value": 0,
            "meaning": (
                "Active or retained in treatment"
            ),
        },
        "models_evaluated": list(
            MODEL_REGISTRY.keys()
        ),
        "model_count": int(
            len(MODEL_REGISTRY)
        ),
        "total_evaluation_seconds": float(
            total_seconds
        ),
        "leakage_safeguards": [
            (
                "No fitting or refitting was performed "
                "during evaluation."
            ),
            (
                "Saved preprocessing pipelines were "
                "used unchanged."
            ),
            (
                "A fixed 0.50 classification threshold "
                "was used."
            ),
            (
                "No hyperparameter optimisation was "
                "performed on test outcomes."
            ),
            (
                "Test rank is descriptive and must not "
                "be used for further tuning."
            ),
        ],
        "software_versions": {
            "python": sys.version,
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
            "matplotlib": matplotlib.__version__,
            "xgboost": (
                xgboost.__version__
                if xgboost is not None
                else None
            ),
        },
        "output_locations": {
            "comparison_csv": str(
                MODEL_COMPARISON_CSV_PATH
            ),
            "comparison_json": str(
                MODEL_COMPARISON_JSON_PATH
            ),
            "predictions": str(
                TEST_PREDICTIONS_PATH
            ),
            "plots": str(
                EVALUATION_PLOTS_DIR
            ),
            "feature_importance": str(
                FEATURE_IMPORTANCE_DIR
            ),
        },
    }

    save_json(
        metadata,
        EVALUATION_METADATA_PATH,
    )

    logger.info(
        "Evaluation metadata saved successfully."
    )

    print_main_heading(
        "FINAL MODEL EVALUATION COMPLETED"
    )

    print(
        comparison[
            [
                "descriptive_test_rank",
                "model",
                "balanced_accuracy",
                "precision",
                "recall_sensitivity",
                "specificity",
                "f1_score",
                "roc_auc",
                "pr_auc_average_precision",
            ]
        ].to_string(
            index=False,
            float_format=lambda value: (
                f"{value:.4f}"
            ),
        )
    )

    print()
    print(
        "Evaluation outputs saved to:"
    )
    print(EVALUATION_DIR)

    logger.info("=" * 60)
    logger.info(
        "FINAL MODEL EVALUATION COMPLETED"
    )
    logger.info("=" * 60)


# =====================================================
# SCRIPT ENTRY POINT
# =====================================================

if __name__ == "__main__":
    try:
        evaluate_models()

    except Exception:
        logger.exception(
            "Final model evaluation failed."
        )

        raise
