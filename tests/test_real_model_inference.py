"""
=========================================================
Real Model Inference Test

Confirms that the inference module can load the actual
trained Logistic Regression pipeline and generate valid
predictions using the held-out test dataset schema.

Author:
    Akayovwe Okugbe

=========================================================
"""

import pandas as pd

from src.config import (
    LOGISTIC_REGRESSION_MODEL_PATH,
    TEST_DATA_PATH,
    TARGET_COLUMN,
)

from src.inference.predict import predict_batch


# =====================================================
# TEST ACTUAL TRAINED MODEL
# =====================================================

def test_real_model_inference():
    """
    Tests the actual trained Logistic Regression model
    against ten records from the held-out test dataset.
    """

    # -------------------------------------------------
    # Load the held-out test dataset
    # -------------------------------------------------

    test_data = pd.read_parquet(
        TEST_DATA_PATH
    )

    # -------------------------------------------------
    # Remove the target because inference should receive
    # predictor variables only
    # -------------------------------------------------

    sample_features = (
        test_data
        .drop(columns=[TARGET_COLUMN])
        .head(10)
    )

    # -------------------------------------------------
    # Generate predictions using the actual saved model
    # -------------------------------------------------

    predictions = predict_batch(
        sample_features,
        model_path=LOGISTIC_REGRESSION_MODEL_PATH,
    )

    # -------------------------------------------------
    # Validate number of returned predictions
    # -------------------------------------------------

    assert len(predictions) == 10

    # -------------------------------------------------
    # Confirm only valid binary classes are returned
    # -------------------------------------------------

    assert predictions[
        "predicted_class"
    ].isin([0, 1]).all()

    # -------------------------------------------------
    # Confirm LTFU probabilities are valid
    # -------------------------------------------------

    assert predictions[
        "ltfu_probability"
    ].between(0, 1).all()

    # -------------------------------------------------
    # Confirm retained probabilities are valid
    # -------------------------------------------------

    assert predictions[
        "retained_probability"
    ].between(0, 1).all()

    # -------------------------------------------------
    # Confirm both probabilities sum to one
    # -------------------------------------------------

    probability_total = (
        predictions["ltfu_probability"]
        +
        predictions["retained_probability"]
    )

    assert probability_total.between(
        0.999999,
        1.000001,
    ).all()

    # -------------------------------------------------
    # Confirm valid labels are returned
    # -------------------------------------------------

    assert predictions[
        "predicted_label"
    ].isin(
        [
            "Retained",
            "LTFU",
        ]
    ).all()

    # -------------------------------------------------
    # Confirm valid risk categories are returned
    # -------------------------------------------------

    assert predictions[
        "risk_category"
    ].isin(
        [
            "Low",
            "Moderate",
            "High",
        ]
    ).all()
