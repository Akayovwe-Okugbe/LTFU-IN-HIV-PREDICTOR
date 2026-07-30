"""
=========================================================
Model Feature Importance

Extracts feature contributions from the fitted estimator
inside each saved scikit-learn pipeline.

Supported estimators
--------------------
- Logistic Regression: absolute coefficient magnitude
- Random Forest: impurity-based feature importance
- AdaBoost: weighted tree importance
- XGBoost: fitted estimator feature importance

The output describes the fitted model's behaviour. It
does not establish causality.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline


def _get_pipeline_components(
    pipeline: Pipeline,
):
    """
    Retrieves the fitted preprocessor and classifier from
    a model pipeline.
    """

    if not isinstance(pipeline, Pipeline):
        raise TypeError(
            "Feature importance extraction expects a "
            "fitted sklearn Pipeline."
        )

    if "preprocessor" not in pipeline.named_steps:
        raise KeyError(
            "The pipeline does not contain a step named "
            "'preprocessor'."
        )

    if "classifier" not in pipeline.named_steps:
        raise KeyError(
            "The pipeline does not contain a step named "
            "'classifier'."
        )

    preprocessor = pipeline.named_steps[
        "preprocessor"
    ]

    classifier = pipeline.named_steps[
        "classifier"
    ]

    return preprocessor, classifier


def extract_feature_importance(
    pipeline: Pipeline,
    model_name: str,
) -> Optional[pd.DataFrame]:
    """
    Extracts feature importance values from one fitted
    model pipeline.

    Returns None when the underlying classifier does not
    expose coefficients or feature_importances_.
    """

    preprocessor, classifier = (
        _get_pipeline_components(
            pipeline
        )
    )

    feature_names = np.asarray(
        preprocessor.get_feature_names_out(),
        dtype=str,
    )

    importance_type: str

    if hasattr(classifier, "coef_"):
        coefficients = np.asarray(
            classifier.coef_
        )

        if coefficients.ndim == 2:
            coefficients = coefficients[0]

        raw_values = coefficients
        importance_values = np.abs(
            coefficients
        )

        importance_type = (
            "absolute_logistic_coefficient"
        )

    elif hasattr(
        classifier,
        "feature_importances_",
    ):
        raw_values = np.asarray(
            classifier.feature_importances_,
            dtype=float,
        )

        importance_values = raw_values

        importance_type = (
            "estimator_feature_importance"
        )

    else:
        return None

    if len(feature_names) != len(
        importance_values
    ):
        raise ValueError(
            f"{model_name} returned "
            f"{len(importance_values)} importance values "
            f"for {len(feature_names)} transformed "
            "features."
        )

    result = pd.DataFrame(
        {
            "model": model_name,
            "feature": feature_names,
            "importance": importance_values,
            "raw_value": raw_values,
            "importance_type": importance_type,
        }
    )

    result = result.sort_values(
        by="importance",
        ascending=False,
    ).reset_index(drop=True)

    result.insert(
        0,
        "rank",
        np.arange(
            1,
            len(result) + 1,
        ),
    )

    return result


def save_feature_importance_table(
    importance: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Saves a complete feature-importance table.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    importance.to_csv(
        output_path,
        index=False,
    )


def save_feature_importance_plot(
    importance: pd.DataFrame,
    model_name: str,
    output_path: Path,
    top_n: int = 20,
) -> None:
    """
    Saves a horizontal bar chart of the top model
    features.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    top_features = (
        importance.head(top_n)
        .sort_values(
            by="importance",
            ascending=True,
        )
    )

    figure, axis = plt.subplots(
        figsize=(10, 8)
    )

    axis.barh(
        top_features["feature"],
        top_features["importance"],
    )

    axis.set_title(
        f"{model_name} — Top {top_n} Features"
    )

    axis.set_xlabel("Importance")
    axis.set_ylabel("Feature")

    axis.grid(
        axis="x",
        alpha=0.25,
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)
