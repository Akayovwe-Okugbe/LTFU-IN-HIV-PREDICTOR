"""
=========================================================
Utility Functions

LTFU Prediction in HIV Treatment Programmes
Rome Business School Capstone Project

Purpose:
    Collection of reusable helper functions used throughout
    the project for data exploration, preprocessing,
    feature engineering, model development, and evaluation.

Author:
    Akayovwe Okugbe

=========================================================
"""

from pathlib import Path

import pandas as pd


# =====================================================
# PRINT SECTION HEADER
# =====================================================

def print_header(title: str) -> None:
    """
    Print a formatted section header.

    Parameters
    ----------
    title : str
        Section title.
    """

    print("\n" + "=" * 70)
    print(title.upper())
    print("=" * 70)


# =====================================================
# PRINT SUBHEADER
# =====================================================

def print_subheader(title: str) -> None:
    """
    Print a formatted subsection header.

    Parameters
    ----------
    title : str
        Subsection title.
    """

    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)


# =====================================================
# DATASET SHAPE
# =====================================================

def dataset_shape(df: pd.DataFrame) -> tuple[int, int]:
    """
    Display dataset dimensions.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset.

    Returns
    -------
    tuple
        Number of rows and columns.
    """

    rows = df.shape[0]
    cols = df.shape[1]

    print(f"Rows    : {rows:,}")
    print(f"Columns : {cols}")

    return rows, cols


# =====================================================
# MISSING VALUE SUMMARY
# =====================================================

def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a summary of missing values.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset.

    Returns
    -------
    pandas.DataFrame
        Missing counts and percentages.
    """

    summary = pd.DataFrame({
        "Missing": df.isna().sum(),
        "Percentage (%)": (df.isna().mean() * 100).round(2)
    })

    summary = summary.sort_values(
        by="Missing",
        ascending=False
    )

    return summary


# =====================================================
# DUPLICATE SUMMARY
# =====================================================

def duplicate_summary(df: pd.DataFrame) -> int:
    """
    Count duplicate records.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset.

    Returns
    -------
    int
        Number of duplicate rows.
    """

    duplicates = df.duplicated().sum()

    print(f"Duplicate rows : {duplicates:,}")

    return duplicates


# =====================================================
# COLUMN INFORMATION
# =====================================================

def column_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Display column names and data types.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset.

    Returns
    -------
    pandas.DataFrame
        Column information.
    """

    return pd.DataFrame({
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str)
    })


# =====================================================
# UNIQUE VALUES
# =====================================================

def unique_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count unique values for every column.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset.

    Returns
    -------
    pandas.DataFrame
        Number of unique values per column.
    """

    return pd.DataFrame({
        "Unique Values": df.nunique()
    })


# =====================================================
# INVALID DATE SUMMARY
# =====================================================

def invalid_dates(
    df: pd.DataFrame,
    columns: list[str]
) -> pd.DataFrame:
    """
    Summarise missing or invalid dates after conversion.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset.

    columns : list
        List of date columns.

    Returns
    -------
    pandas.DataFrame
        Missing/invalid dates and percentages.
    """

    results = []

    total_rows = len(df)

    for column in columns:

        if column in df.columns:

            missing = df[column].isna().sum()

            percentage = round(
                (missing / total_rows) * 100,
                2
            )

            results.append({

                "Column": column,

                "Missing / Invalid Dates": missing,

                "Percentage (%)": percentage

            })

    return pd.DataFrame(results)


# =====================================================
# FREQUENCY TABLE
# =====================================================

def frequency_table(
    df: pd.DataFrame,
    column: str
) -> pd.DataFrame:
    """
    Generate frequency counts and percentages for a
    categorical variable.

    Parameters
    ----------
    df : pandas.DataFrame

    column : str

    Returns
    -------
    pandas.DataFrame
    """

    table = (
        df[column]
        .value_counts(dropna=False)
        .sort_index()
        .rename("Count")
        .to_frame()
    )

    table["Percentage (%)"] = (
        table["Count"] / len(df) * 100
    ).round(2)

    return table


# =====================================================
# NUMERICAL SUMMARY
# =====================================================

def numerical_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate descriptive statistics for all
    numerical variables.

    Returns
    -------
    pandas.DataFrame
    """

    return (
        df.describe()
        .transpose()
        .round(2)
    )


# =====================================================
# DATE RANGE
# =====================================================

def date_range(
    df: pd.DataFrame,
    column: str
) -> dict:
    """
    Display minimum and maximum dates.

    Parameters
    ----------
    df : pandas.DataFrame

    column : str

    Returns
    -------
    dict
    """

    return {
        "Minimum": df[column].min(),
        "Maximum": df[column].max()
    }


# =====================================================
# SAVE DATAFRAME
# =====================================================

def save_dataframe(
    df: pd.DataFrame,
    filepath: str | Path
) -> None:
    """
    Save a DataFrame as a CSV file.

    Parameters
    ----------
    df : pandas.DataFrame

    filepath : str | pathlib.Path
    """

    path = Path(filepath)

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        path,
        index=False
    )

    print("\nDataset successfully saved.")

    print(f"Location : {path.resolve()}")