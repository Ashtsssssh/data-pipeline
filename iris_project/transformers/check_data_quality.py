"""
iris_project/transformers/check_data_quality.py
Part C4 — Custom block: validates no missing values and exactly 3 classes.
Sits between load_iris and prepare_data.
"""

try:
    from mage_ai.data_preparation.decorators import transformer, test
except ImportError:
    def transformer(fn):
        return fn
    def test(fn):
        return fn

import pandas as pd


@transformer
def transform(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
    """
    Validate the raw Iris dataset:
      - No missing values in any column
      - Exactly 3 target classes
    Passes the DataFrame through unchanged if all checks pass.
    """
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        raise ValueError(
            f"Dataset has missing values:\n{null_counts[null_counts > 0]}"
        )

    n_classes = df["target"].nunique()
    if n_classes != 3:
        raise ValueError(
            f"Expected exactly 3 Iris classes, found {n_classes}"
        )

    print(f"[check_data_quality] ✓ No nulls. ✓ {n_classes} classes. "
          f"Shape: {df.shape}")
    return df


@test
def test_no_nulls(df: pd.DataFrame) -> None:
    """Fail the pipeline if any cell is null."""
    nulls = df.isnull().sum().sum()
    assert nulls == 0, f"Found {nulls} null values in dataset"


@test
def test_exactly_three_classes(df: pd.DataFrame) -> None:
    """Fail the pipeline if the number of classes is not 3."""
    n = df["target"].nunique()
    assert n == 3, f"Expected 3 classes, got {n}"
