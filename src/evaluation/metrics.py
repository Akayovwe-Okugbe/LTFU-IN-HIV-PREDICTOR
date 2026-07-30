"""
=========================================================
Binary Classification Evaluation Metrics

Calculates clinically relevant performance metrics for
predicting loss to follow-up.

Class interpretation
--------------------
0 = Active or retained in treatment
1 = Inactive or loss to follow-up

The positive class is therefore class 1.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)


def calculate_binary_classification_metrics(
    y_true,
    y_pred,
    y_probability,
) -> Dict[str, Any]:
    """
    Calculates test-set performance metrics for a binary
    classifier.

    Parameters
    ----------
    y_true : array-like
        True binary outcomes.

    y_pred : array-like
        Predicted binary outcomes generated using the
        fixed classification threshold.

    y_probability : array-like
        Estimated probability of class 1, representing
        loss to follow-up.

    Returns
    -------
    dict
        Dictionary containing discrimination,
        classification and probability-quality metrics.
        Values may be integers or floating-point numbers.
    """

    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    y_probability = np.asarray(
        y_probability,
        dtype=float,
    )

    if not (
        len(y_true)
        == len(y_pred)
        == len(y_probability)
    ):
        raise ValueError(
            "The true labels, predicted labels and "
            "predicted probabilities must have equal "
            "lengths."
        )

    if not np.isfinite(y_probability).all():
        raise ValueError(
            "Predicted probabilities contain NaN or "
            "infinite values."
        )

    if np.any(
        (y_probability < 0)
        | (y_probability > 1)
    ):
        raise ValueError(
            "Predicted probabilities must be between "
            "zero and one."
        )

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )

    tn, fp, fn, tp = matrix.ravel()

    specificity = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else 0.0
    )

    negative_predictive_value = (
        tn / (tn + fn)
        if (tn + fn) > 0
        else 0.0
    )

    false_positive_rate = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0.0
    )

    false_negative_rate = (
        fn / (fn + tp)
        if (fn + tp) > 0
        else 0.0
    )

    prevalence = float(np.mean(y_true))

    predicted_positive_rate = float(
        np.mean(y_pred)
    )

    metrics = {
        "test_records": int(len(y_true)),
        "actual_ltfu_records": int(
            np.sum(y_true == 1)
        ),
        "actual_retained_records": int(
            np.sum(y_true == 0)
        ),
        "predicted_ltfu_records": int(
            np.sum(y_pred == 1)
        ),
        "predicted_retained_records": int(
            np.sum(y_pred == 0)
        ),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
        "prevalence": prevalence,
        "predicted_positive_rate": (
            predicted_positive_rate
        ),
        "accuracy": float(
            accuracy_score(
                y_true,
                y_pred,
            )
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(
                y_true,
                y_pred,
            )
        ),
        "precision": float(
            precision_score(
                y_true,
                y_pred,
                pos_label=1,
                zero_division=0,
            )
        ),
        "recall_sensitivity": float(
            recall_score(
                y_true,
                y_pred,
                pos_label=1,
                zero_division=0,
            )
        ),
        "specificity": float(specificity),
        "negative_predictive_value": float(
            negative_predictive_value
        ),
        "f1_score": float(
            f1_score(
                y_true,
                y_pred,
                pos_label=1,
                zero_division=0,
            )
        ),
        "false_positive_rate": float(
            false_positive_rate
        ),
        "false_negative_rate": float(
            false_negative_rate
        ),
        "matthews_correlation_coefficient": float(
            matthews_corrcoef(
                y_true,
                y_pred,
            )
        ),
        "roc_auc": float(
            roc_auc_score(
                y_true,
                y_probability,
            )
        ),
        "pr_auc_average_precision": float(
            average_precision_score(
                y_true,
                y_probability,
            )
        ),
        "brier_score": float(
            brier_score_loss(
                y_true,
                y_probability,
            )
        ),
        "log_loss": float(
            log_loss(
                y_true,
                y_probability,
                labels=[0, 1],
            )
        ),
    }

    return metrics
