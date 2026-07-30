"""
=========================================================
Model Preprocessing

Builds model-specific preprocessing transformers.

The datasets have already been one-hot encoded during
feature engineering. Consequently, this module mainly:

- identifies numeric and Boolean predictors;
- imputes missing numeric values using the training median;
- imputes missing Boolean values using the most frequent
  training value;
- standardises continuous numeric variables for Logistic
  Regression;
- preserves the original numeric scale for tree models.

All preprocessing is fitted inside each model pipeline.
This prevents information from the held-out test set from
being used during imputation or scaling.

=========================================================
"""

from typing import List, Tuple

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# =====================================================
# IDENTIFY FEATURE TYPES
# =====================================================

def identify_feature_types(
    X: pd.DataFrame,
) -> Tuple[List[str], List[str]]:
    """
    Identifies continuous numeric and Boolean features.

    Boolean columns usually represent one-hot-encoded
    categorical variables.

    Parameters
    ----------
    X : pandas.DataFrame
        Predictor matrix.

    Returns
    -------
    tuple
        numeric_columns and boolean_columns.
    """

    boolean_columns = X.select_dtypes(
        include=["bool"]
    ).columns.tolist()

    numeric_columns = X.select_dtypes(
        include=["number"]
    ).columns.tolist()

    # Boolean values are not normally returned by the
    # numeric selector, but this exclusion protects the
    # function against dtype differences across versions.
    numeric_columns = [
        column
        for column in numeric_columns
        if column not in boolean_columns
    ]

    represented_columns = set(
        numeric_columns + boolean_columns
    )

    unsupported_columns = [
        column
        for column in X.columns
        if column not in represented_columns
    ]

    if unsupported_columns:
        raise TypeError(
            "Unsupported feature types were found: "
            f"{unsupported_columns}"
        )

    if not numeric_columns and not boolean_columns:
        raise ValueError(
            "No model-compatible predictor columns "
            "were identified."
        )

    return numeric_columns, boolean_columns


# =====================================================
# NUMERIC PREPROCESSOR FOR LINEAR MODELS
# =====================================================

def _build_scaled_numeric_pipeline() -> Pipeline:
    """
    Builds preprocessing for continuous variables used
    by Logistic Regression.

    Missing values are replaced with the training median.
    StandardScaler then places continuous variables on a
    comparable scale.
    """

    return Pipeline(
        steps=[
            (
                "median_imputer",
                SimpleImputer(
                    strategy="median",
                    keep_empty_features=True,
                ),
            ),
            (
                "standard_scaler",
                StandardScaler(),
            ),
        ]
    )


# =====================================================
# NUMERIC PREPROCESSOR FOR TREE MODELS
# =====================================================

def _build_unscaled_numeric_pipeline() -> Pipeline:
    """
    Builds preprocessing for continuous variables used
    by tree-based classifiers.

    Tree models do not require standardised feature
    magnitudes, so only median imputation is applied.
    """

    return Pipeline(
        steps=[
            (
                "median_imputer",
                SimpleImputer(
                    strategy="median",
                    keep_empty_features=True,
                ),
            ),
        ]
    )


# =====================================================
# BOOLEAN PREPROCESSOR
# =====================================================

def _build_boolean_pipeline() -> Pipeline:
    """
    Builds preprocessing for one-hot-encoded Boolean
    predictors.

    Missing values, if any, are replaced with the most
    frequently observed training value.
    """

    return Pipeline(
        steps=[
            (
                "most_frequent_imputer",
                SimpleImputer(
                    strategy="most_frequent",
                    keep_empty_features=True,
                ),
            ),
        ]
    )


# =====================================================
# LINEAR MODEL PREPROCESSOR
# =====================================================

def build_linear_preprocessor(
    numeric_columns: List[str],
    boolean_columns: List[str],
) -> ColumnTransformer:
    """
    Builds preprocessing for Logistic Regression.

    Numeric variables are median-imputed and scaled.
    Boolean dummy variables are imputed but not scaled.
    """

    transformers = []

    if numeric_columns:
        transformers.append(
            (
                "numeric",
                _build_scaled_numeric_pipeline(),
                numeric_columns,
            )
        )

    if boolean_columns:
        transformers.append(
            (
                "boolean",
                _build_boolean_pipeline(),
                boolean_columns,
            )
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )


# =====================================================
# TREE MODEL PREPROCESSOR
# =====================================================

def build_tree_preprocessor(
    numeric_columns: List[str],
    boolean_columns: List[str],
) -> ColumnTransformer:
    """
    Builds preprocessing for Random Forest, AdaBoost
    and XGBoost.

    Numeric values are median-imputed without scaling.
    Boolean variables are imputed and retained.
    """

    transformers = []

    if numeric_columns:
        transformers.append(
            (
                "numeric",
                _build_unscaled_numeric_pipeline(),
                numeric_columns,
            )
        )

    if boolean_columns:
        transformers.append(
            (
                "boolean",
                _build_boolean_pipeline(),
                boolean_columns,
            )
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )
