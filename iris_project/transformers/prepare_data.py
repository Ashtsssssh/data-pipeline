"""
iris_project/transformers/prepare_data.py
Mage transformer block — adds an 80/20 train/test split column.
"""

if 'transformer' not in globals():
    try:
        from mage_ai.data_preparation.decorators import transformer
    except ImportError:
        def transformer(fn): return fn

if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(fn): return fn

import pandas as pd
from sklearn.model_selection import train_test_split


@transformer
def transform(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
    train_idx, test_idx = train_test_split(
        df.index,
        test_size=0.2,
        random_state=42,
        stratify=df["target"],
    )
    df = df.copy()
    df["split"] = "train"
    df.loc[test_idx, "split"] = "test"
    return df


@test
def test_split_ratio(df: pd.DataFrame) -> None:
    n_train = (df["split"] == "train").sum()
    n_test  = (df["split"] == "test").sum()
    assert n_train == 120, f"Expected 120 train rows, got {n_train}"
    assert n_test  == 30,  f"Expected 30 test rows, got {n_test}"
