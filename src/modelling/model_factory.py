"""
=========================================================
Model Factory

Constructs the four classification pipelines used in
the project:

1. Logistic Regression
2. Random Forest
3. AdaBoost
4. XGBoost

Each function returns an unfitted scikit-learn Pipeline
containing model-specific preprocessing followed by the
classifier.

=========================================================
"""

from typing import List

import pandas as pd

from sklearn.ensemble import (
    AdaBoostClassifier,
    RandomForestClassifier,
)

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from xgboost import XGBClassifier

from src.config import (
    N_JOBS,
    RANDOM_STATE,
)

from src.modelling.preprocessing import (
    build_linear_preprocessor,
    build_tree_preprocessor,
)


# =====================================================
# CLASS-IMBALANCE WEIGHT FOR XGBOOST
# =====================================================

def calculate_scale_pos_weight(
    y: pd.Series,
) -> float:
    """
    Calculates the XGBoost positive-class weight.

    The value is:

        number of negative cases / number of positive cases

    In this project:

        0 = retained or active
        1 = inactive or loss to follow-up

    A value greater than one gives additional importance
    to the less frequent positive class during training.

    Parameters
    ----------
    y : pandas.Series
        Binary training target.

    Returns
    -------
    float
        Positive-class weighting value.
    """

    negative_count = int((y == 0).sum())
    positive_count = int((y == 1).sum())

    if negative_count == 0:
        raise ValueError(
            "The training target contains no negative "
            "class observations."
        )

    if positive_count == 0:
        raise ValueError(
            "The training target contains no positive "
            "class observations."
        )

    return negative_count / positive_count


# =====================================================
# LOGISTIC REGRESSION
# =====================================================

def build_logistic_regression_pipeline(
    numeric_columns: List[str],
    boolean_columns: List[str],
) -> Pipeline:
    """
    Builds the Logistic Regression pipeline.

    class_weight='balanced' adjusts class contributions
    according to their frequencies in the training data.
    """

    preprocessor = build_linear_preprocessor(
        numeric_columns,
        boolean_columns,
    )

    classifier = LogisticRegression(
        solver="saga",
        penalty="l2",
        class_weight="balanced",
        max_iter=2_000,
        random_state=RANDOM_STATE,
        n_jobs=N_JOBS,
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "classifier",
                classifier,
            ),
        ]
    )


# =====================================================
# RANDOM FOREST
# =====================================================

def build_random_forest_pipeline(
    numeric_columns: List[str],
    boolean_columns: List[str],
) -> Pipeline:
    """
    Builds the Random Forest pipeline.

    balanced_subsample recalculates class weights for
    each bootstrap sample used to construct a tree.
    """

    preprocessor = build_tree_preprocessor(
        numeric_columns,
        boolean_columns,
    )

    classifier = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features="sqrt",
        class_weight="balanced_subsample",
        bootstrap=True,
        random_state=RANDOM_STATE,
        n_jobs=N_JOBS,
        verbose=0,
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "classifier",
                classifier,
            ),
        ]
    )


# =====================================================
# ADABOOST
# =====================================================

def build_adaboost_pipeline(
    numeric_columns: List[str],
    boolean_columns: List[str],
) -> Pipeline:
    """
    Builds the AdaBoost pipeline.

    A shallow decision tree is used as the weak learner.
    Class weighting is applied at the weak-learner level
    because AdaBoostClassifier does not expose its own
    class_weight parameter.
    """

    preprocessor = build_tree_preprocessor(
        numeric_columns,
        boolean_columns,
    )

    weak_learner = DecisionTreeClassifier(
        max_depth=1,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )

    classifier = AdaBoostClassifier(
        estimator=weak_learner,
        n_estimators=150,
        learning_rate=0.05,
        random_state=RANDOM_STATE,
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "classifier",
                classifier,
            ),
        ]
    )


# =====================================================
# XGBOOST
# =====================================================

def build_xgboost_pipeline(
    numeric_columns: List[str],
    boolean_columns: List[str],
    scale_pos_weight: float,
) -> Pipeline:
    """
    Builds the XGBoost classification pipeline.

    The histogram tree method is selected because it is
    efficient for large tabular datasets.

    scale_pos_weight is calculated from the training
    target and helps address binary class imbalance.
    """

    preprocessor = build_tree_preprocessor(
        numeric_columns,
        boolean_columns,
    )

    classifier = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        n_estimators=300,
        learning_rate=0.05,
        max_depth=6,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.0,
        reg_lambda=1.0,
        scale_pos_weight=scale_pos_weight,
        tree_method="hist",
        random_state=RANDOM_STATE,
        n_jobs=N_JOBS,
        verbosity=0,
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "classifier",
                classifier,
            ),
        ]
    )
