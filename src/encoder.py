"""
Categorical Variable Encoding
"""

import pandas as pd


def one_hot_encode(df: pd.DataFrame, columns: list):

    return pd.get_dummies(

        df,

        columns=columns,

        drop_first=True

    )