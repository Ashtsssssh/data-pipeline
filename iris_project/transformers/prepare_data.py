"""
iris_project/transformers/prepare_data.py
Mage transformer block — adds an 80/20 train/test split column.
"""

try:
    from mage_ai.data_preparation.decorators import transformer, test
except ImportError:
    def transformer(fn):
        return fn
    def test(fn):
        return fn

import pandas as pd
from sklearn.model_selection import train_test_split


@transformer
def transform(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
    """
    Add a 'split' column to the Iris DataFrame.
    80 % of rows get 'train', 20 % get 'test'.
    Random state is fixed for reproducibility.
    """
    train_idx, test_idx = train_test_split(
        df.index,
        test_size=0.3,        
        random_state=42,
        stratify=df["target"],
    )
    df = df.copy()
    df["split"] = "train"
    df.loc[test_idx, "split"] = "test"
    return df


# ---------------------------------------------------------------------------
# @test — gate: CI fails if the split ratio is wrong
# ---------------------------------------------------------------------------
@test
def test_split_ratio(df: pd.DataFrame) -> None:
    """Train must be 120 rows and test must be 30 rows."""
    n_train = (df["split"] == "train").sum()
    n_test  = (df["split"] == "test").sum()
    assert n_train == 120, f"Expected 120 train rows, got {n_train}"
    assert n_test  == 30,  f"Expected 30 test rows, got {n_test}"
