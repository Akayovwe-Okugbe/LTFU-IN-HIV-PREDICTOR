"""
=========================================================
Model Training Pipeline

Trains the four baseline classifiers used to predict
90-day HIV treatment inactivity or loss to follow-up:

1. Logistic Regression
2. Random Forest
3. AdaBoost
4. XGBoost

The script:

- loads the prepared training and testing datasets;
- validates both datasets;
- confirms that train and test schemas match;
- separates predictors and target;
- identifies numeric and Boolean features;
- measures the training-set class distribution;
- builds model-specific preprocessing pipelines;
- trains each model using only the training data;
- saves the complete fitted pipelines;
- saves metadata describing the training run.

The held-out test dataset is not used to fit or select
any model. It will be used later in evaluate.py.

Run from the project root with:

    python -m src.train

=========================================================
"""

from time import perf_counter
from typing import Any, Dict

import pandas as pd

from src.config import (
    ADABOOST_MODEL_PATH,
    LOGISTIC_REGRESSION_MODEL_PATH,
    RANDOM_FOREST_MODEL_PATH,
    TARGET_COLUMN,
    XGBOOST_MODEL_PATH,
)

from src.logger import logger

from src.modelling import (
    build_adaboost_pipeline,
    build_logistic_regression_pipeline,
    build_random_forest_pipeline,
    build_xgboost_pipeline,
    calculate_scale_pos_weight,
    identify_feature_types,
    load_testing_dataset,
    load_training_dataset,
    save_model,
    save_training_metadata,
    split_features_target,
    validate_modelling_dataset,
)


# =====================================================
# CONSOLE FORMATTING
# =====================================================

def print_header(title: str) -> None:
    """
    Prints a major console heading.
    """

    print("\n" + "=" * 70)
    print(title.upper())
    print("=" * 70)


def print_subheader(title: str) -> None:
    """
    Prints a secondary console heading.
    """

    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)


# =====================================================
# VALIDATE TRAIN-TEST SCHEMA
# =====================================================

def validate_train_test_schema(
    train_dataframe: pd.DataFrame,
    test_dataframe: pd.DataFrame,
) -> None:
    """
    Confirms that train and test datasets contain the
    same columns in the same order.

    The feature engineering pipeline should have produced
    both files from the same encoded dataset.
    """

    train_columns = train_dataframe.columns.tolist()
    test_columns = test_dataframe.columns.tolist()

    if train_columns == test_columns:
        logger.info(
            "Training and testing schemas match."
        )
        return

    missing_from_test = sorted(
        set(train_columns) - set(test_columns)
    )

    extra_in_test = sorted(
        set(test_columns) - set(train_columns)
    )

    raise ValueError(
        "Training and testing dataset schemas do not "
        "match. "
        f"Missing from test: {missing_from_test}. "
        f"Extra in test: {extra_in_test}."
    )


# =====================================================
# LOG CLASS DISTRIBUTION
# =====================================================

def describe_target_distribution(
    y: pd.Series,
) -> Dict[str, Any]:
    """
    Logs and returns the training target distribution.
    """

    class_counts = (
        y.value_counts()
        .sort_index()
    )

    class_percentages = (
        y.value_counts(
            normalize=True
        )
        .sort_index()
        .mul(100)
    )

    negative_count = int(
        class_counts.get(0, 0)
    )

    positive_count = int(
        class_counts.get(1, 0)
    )

    negative_percentage = float(
        class_percentages.get(0, 0.0)
    )

    positive_percentage = float(
        class_percentages.get(1, 0.0)
    )

    logger.info(
        "Training target distribution:"
    )

    logger.info(
        "Class 0 — Active/retained: "
        "%s records (%.2f%%)",
        f"{negative_count:,}",
        negative_percentage,
    )

    logger.info(
        "Class 1 — Inactive/LTFU: "
        "%s records (%.2f%%)",
        f"{positive_count:,}",
        positive_percentage,
    )

    return {
        "class_0_count": negative_count,
        "class_0_percentage": negative_percentage,
        "class_1_count": positive_count,
        "class_1_percentage": positive_percentage,
    }


# =====================================================
# TRAIN AND SAVE ONE MODEL
# =====================================================

def train_and_save_model(
    model_name: str,
    model: Any,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    output_path,
) -> float:
    """
    Fits and saves one model pipeline.

    Parameters
    ----------
    model_name : str
        Human-readable name used in logs.

    model : Any
        Unfitted scikit-learn-compatible estimator.

    X_train : pandas.DataFrame
        Training predictors.

    y_train : pandas.Series
        Training target.

    output_path : pathlib.Path
        Destination for the fitted pipeline.

    Returns
    -------
    float
        Training duration in seconds.
    """

    print_subheader(
        f"Training {model_name}"
    )

    logger.info(
        "Beginning %s training...",
        model_name,
    )

    start_time = perf_counter()

    try:
        model.fit(
            X_train,
            y_train,
        )

    except Exception as error:
        logger.exception(
            "%s training failed.",
            model_name,
        )

        raise RuntimeError(
            f"Unable to train {model_name}."
        ) from error

    elapsed_seconds = (
        perf_counter() - start_time
    )

    logger.info(
        "%s training completed in %.2f seconds.",
        model_name,
        elapsed_seconds,
    )

    save_model(
        model=model,
        file_path=output_path,
        model_name=model_name,
    )

    return elapsed_seconds


# =====================================================
# MAIN TRAINING WORKFLOW
# =====================================================

def train_models() -> None:
    """
    Runs the complete model-training workflow.
    """

    logger.info("=" * 60)
    logger.info("STARTING MODEL TRAINING")
    logger.info("=" * 60)

    print_header("Model Training")

    # -------------------------------------------------
    # LOAD DATA
    # -------------------------------------------------

    print_subheader("Loading Modelling Data")

    train_dataframe = load_training_dataset()
    test_dataframe = load_testing_dataset()

    # -------------------------------------------------
    # VALIDATE DATA
    # -------------------------------------------------

    print_subheader("Validating Modelling Data")

    validate_modelling_dataset(
        train_dataframe,
        "training",
    )

    validate_modelling_dataset(
        test_dataframe,
        "testing",
    )

    validate_train_test_schema(
        train_dataframe,
        test_dataframe,
    )

    # -------------------------------------------------
    # SPLIT PREDICTORS AND TARGET
    # -------------------------------------------------

    X_train, y_train = split_features_target(
        train_dataframe
    )

    X_test, y_test = split_features_target(
        test_dataframe
    )

    # X_test and y_test are intentionally not supplied
    # to model.fit(). They are used here only for schema
    # and metadata checks. Formal performance assessment
    # belongs in evaluate.py.

    if X_train.columns.tolist() != X_test.columns.tolist():
        raise ValueError(
            "Training and testing predictor columns "
            "do not match."
        )

    logger.info(
        "Training predictor matrix: "
        "%s rows × %s features.",
        f"{X_train.shape[0]:,}",
        f"{X_train.shape[1]:,}",
    )

    logger.info(
        "Held-out test predictor matrix: "
        "%s rows × %s features.",
        f"{X_test.shape[0]:,}",
        f"{X_test.shape[1]:,}",
    )

    # -------------------------------------------------
    # IDENTIFY FEATURE TYPES
    # -------------------------------------------------

    print_subheader("Identifying Feature Types")

    (
        numeric_columns,
        boolean_columns,
    ) = identify_feature_types(X_train)

    logger.info(
        "Numeric features: %s",
        len(numeric_columns),
    )

    logger.info(
        "Boolean encoded features: %s",
        len(boolean_columns),
    )

    logger.info(
        "Total predictor features: %s",
        X_train.shape[1],
    )

    # -------------------------------------------------
    # CLASS DISTRIBUTION
    # -------------------------------------------------

    print_subheader("Analysing Target Distribution")

    target_distribution = (
        describe_target_distribution(y_train)
    )

    scale_pos_weight = (
        calculate_scale_pos_weight(y_train)
    )

    logger.info(
        "XGBoost scale_pos_weight: %.4f",
        scale_pos_weight,
    )

    # -------------------------------------------------
    # BUILD MODELS
    # -------------------------------------------------

    print_subheader("Building Model Pipelines")

    logistic_regression_pipeline = (
        build_logistic_regression_pipeline(
            numeric_columns,
            boolean_columns,
        )
    )

    random_forest_pipeline = (
        build_random_forest_pipeline(
            numeric_columns,
            boolean_columns,
        )
    )

    adaboost_pipeline = (
        build_adaboost_pipeline(
            numeric_columns,
            boolean_columns,
        )
    )

    xgboost_pipeline = (
        build_xgboost_pipeline(
            numeric_columns,
            boolean_columns,
            scale_pos_weight,
        )
    )

    logger.info(
        "All model pipelines built successfully."
    )

    # -------------------------------------------------
    # TRAIN AND SAVE MODELS
    # -------------------------------------------------

    training_durations = {}

    training_durations[
        "logistic_regression_seconds"
    ] = train_and_save_model(
        model_name="Logistic Regression",
        model=logistic_regression_pipeline,
        X_train=X_train,
        y_train=y_train,
        output_path=LOGISTIC_REGRESSION_MODEL_PATH,
    )

    training_durations[
        "random_forest_seconds"
    ] = train_and_save_model(
        model_name="Random Forest",
        model=random_forest_pipeline,
        X_train=X_train,
        y_train=y_train,
        output_path=RANDOM_FOREST_MODEL_PATH,
    )

    training_durations[
        "adaboost_seconds"
    ] = train_and_save_model(
        model_name="AdaBoost",
        model=adaboost_pipeline,
        X_train=X_train,
        y_train=y_train,
        output_path=ADABOOST_MODEL_PATH,
    )

    training_durations[
        "xgboost_seconds"
    ] = train_and_save_model(
        model_name="XGBoost",
        model=xgboost_pipeline,
        X_train=X_train,
        y_train=y_train,
        output_path=XGBOOST_MODEL_PATH,
    )

    # -------------------------------------------------
    # SAVE TRAINING METADATA
    # -------------------------------------------------

    print_subheader("Saving Training Metadata")

    metadata = {
        "target_column": TARGET_COLUMN,
        "training_records": int(
            train_dataframe.shape[0]
        ),
        "testing_records": int(
            test_dataframe.shape[0]
        ),
        "predictor_count": int(
            X_train.shape[1]
        ),
        "numeric_feature_count": len(
            numeric_columns
        ),
        "boolean_feature_count": len(
            boolean_columns
        ),
        "numeric_features": numeric_columns,
        "boolean_features": boolean_columns,
        "feature_order": X_train.columns.tolist(),
        "target_distribution": (
            target_distribution
        ),
        "xgboost_scale_pos_weight": float(
            scale_pos_weight
        ),
        "models_trained": [
            "Logistic Regression",
            "Random Forest",
            "AdaBoost",
            "XGBoost",
        ],
        "training_durations_seconds": (
            training_durations
        ),
        "test_data_used_for_training": False,
    }

    save_training_metadata(metadata)

    # -------------------------------------------------
    # COMPLETION
    # -------------------------------------------------

    print_header("Model Training Completed")

    print(
        "Models trained and saved successfully:"
    )

    print(
        f"1. {LOGISTIC_REGRESSION_MODEL_PATH}"
    )

    print(
        f"2. {RANDOM_FOREST_MODEL_PATH}"
    )

    print(
        f"3. {ADABOOST_MODEL_PATH}"
    )

    print(
        f"4. {XGBOOST_MODEL_PATH}"
    )

    logger.info("=" * 60)
    logger.info("MODEL TRAINING COMPLETED")
    logger.info("=" * 60)


# =====================================================
# SCRIPT ENTRY POINT
# =====================================================

if __name__ == "__main__":

    try:
        train_models()

    except Exception:
        logger.exception(
            "Model training pipeline failed."
        )

        raise
