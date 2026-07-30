"""
=========================================================
Evaluation Plotting Utilities

Creates:

- confusion matrices;
- combined ROC curves;
- combined precision-recall curves;
- probability calibration curves;
- model-comparison charts.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    auc,
    confusion_matrix,
    precision_recall_curve,
    roc_curve,
)


def _prepare_output_path(
    output_path: Path,
) -> Path:
    """
    Creates the output directory and returns the path.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return output_path


def save_confusion_matrix_plot(
    y_true,
    y_pred,
    model_name: str,
    output_path: Path,
) -> None:
    """
    Saves a confusion matrix for one model.
    """

    output_path = _prepare_output_path(
        output_path
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )

    display = ConfusionMatrixDisplay(
        confusion_matrix=matrix,
        display_labels=[
            "Retained",
            "LTFU",
        ],
    )

    figure, axis = plt.subplots(
        figsize=(7, 6)
    )

    display.plot(
        ax=axis,
        values_format=",d",
        colorbar=False,
    )

    axis.set_title(
        f"{model_name} — Confusion Matrix"
    )

    axis.set_xlabel("Predicted outcome")
    axis.set_ylabel("Actual outcome")

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)


def save_combined_roc_curve(
    y_true,
    probabilities: Dict[str, np.ndarray],
    output_path: Path,
) -> None:
    """
    Saves ROC curves for all evaluated models.
    """

    output_path = _prepare_output_path(
        output_path
    )

    figure, axis = plt.subplots(
        figsize=(9, 7)
    )

    for model_name, y_probability in (
        probabilities.items()
    ):
        false_positive_rate, true_positive_rate, _ = (
            roc_curve(
                y_true,
                y_probability,
            )
        )

        roc_auc = auc(
            false_positive_rate,
            true_positive_rate,
        )

        axis.plot(
            false_positive_rate,
            true_positive_rate,
            linewidth=2,
            label=(
                f"{model_name} "
                f"(AUC = {roc_auc:.3f})"
            ),
        )

    axis.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        linewidth=1.5,
        label="Chance",
    )

    axis.set_title(
        "Receiver Operating Characteristic Curves"
    )

    axis.set_xlabel("False-positive rate")
    axis.set_ylabel("True-positive rate")

    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1.02)

    axis.legend(loc="lower right")
    axis.grid(alpha=0.25)

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)


def save_combined_precision_recall_curve(
    y_true,
    probabilities: Dict[str, np.ndarray],
    output_path: Path,
) -> None:
    """
    Saves precision-recall curves for all models.
    """

    output_path = _prepare_output_path(
        output_path
    )

    figure, axis = plt.subplots(
        figsize=(9, 7)
    )

    prevalence = float(
        np.mean(np.asarray(y_true))
    )

    for model_name, y_probability in (
        probabilities.items()
    ):
        precision, recall, _ = (
            precision_recall_curve(
                y_true,
                y_probability,
            )
        )

        # Trapezoidal PR-AUC is used only for displaying
        # the curve. The metrics table stores average
        # precision as the primary PR summary.
        pr_auc = auc(
            recall,
            precision,
        )

        axis.plot(
            recall,
            precision,
            linewidth=2,
            label=(
                f"{model_name} "
                f"(area = {pr_auc:.3f})"
            ),
        )

    axis.axhline(
        prevalence,
        linestyle="--",
        linewidth=1.5,
        label=(
            "No-skill prevalence "
            f"({prevalence:.3f})"
        ),
    )

    axis.set_title(
        "Precision–Recall Curves"
    )

    axis.set_xlabel(
        "Recall / Sensitivity"
    )

    axis.set_ylabel("Precision")

    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1.02)

    axis.legend(loc="lower left")
    axis.grid(alpha=0.25)

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)


def save_calibration_curves(
    y_true,
    probabilities: Dict[str, np.ndarray],
    output_path: Path,
) -> None:
    """
    Saves observed-versus-predicted probability curves.

    Calibration assesses whether predicted risks such as
    0.70 correspond approximately to a 70% observed LTFU
    rate among similarly scored patients.
    """

    output_path = _prepare_output_path(
        output_path
    )

    figure, axis = plt.subplots(
        figsize=(9, 7)
    )

    for model_name, y_probability in (
        probabilities.items()
    ):
        observed_fraction, predicted_mean = (
            calibration_curve(
                y_true,
                y_probability,
                n_bins=10,
                strategy="quantile",
            )
        )

        axis.plot(
            predicted_mean,
            observed_fraction,
            marker="o",
            linewidth=2,
            label=model_name,
        )

    axis.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        linewidth=1.5,
        label="Perfect calibration",
    )

    axis.set_title(
        "Probability Calibration Curves"
    )

    axis.set_xlabel(
        "Mean predicted LTFU probability"
    )

    axis.set_ylabel(
        "Observed LTFU proportion"
    )

    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)

    axis.legend(loc="upper left")
    axis.grid(alpha=0.25)

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)


def save_model_comparison_plot(
    comparison: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Saves a grouped comparison of major model metrics.
    """

    output_path = _prepare_output_path(
        output_path
    )

    metrics_to_plot = [
        "balanced_accuracy",
        "precision",
        "recall_sensitivity",
        "specificity",
        "f1_score",
        "roc_auc",
        "pr_auc_average_precision",
    ]

    plot_data = comparison.set_index(
        "model"
    )[metrics_to_plot]

    figure, axis = plt.subplots(
        figsize=(13, 7)
    )

    plot_data.plot(
        kind="bar",
        ax=axis,
    )

    axis.set_title(
        "Held-Out Test Performance by Model"
    )

    axis.set_xlabel("Model")
    axis.set_ylabel("Metric value")

    axis.set_ylim(0, 1.05)

    axis.tick_params(
        axis="x",
        rotation=20,
    )

    axis.legend(
        title="Metric",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
    )

    axis.grid(
        axis="y",
        alpha=0.25,
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)
