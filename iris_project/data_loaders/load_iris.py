"""
iris_project/data_loaders/load_iris.py
Mage data loader block — loads the sklearn Iris dataset as a DataFrame.
"""

if 'data_loader' not in globals():
    try:
        from mage_ai.data_preparation.decorators import data_loader
    except ImportError:
        def data_loader(fn): return fn

if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(fn): return fn

import pandas as pd
from sklearn.datasets import load_iris


@data_loader
def load_data(*args, **kwargs) -> pd.DataFrame:
    """
    Load the Iris dataset from sklearn and return it as a pandas DataFrame.
    """
    iris = load_iris(as_frame=True)
    df = iris.frame
    df["target_name"] = df["target"].map(
        dict(enumerate(iris.target_names))
    )
    return df


@test
def test_dataset_shape(df: pd.DataFrame) -> None:
    assert df is not None, "Loaded dataframe is None"
    assert df.shape == (150, 6), f"Expected (150, 6), got {df.shape}"
    assert df.isnull().sum().sum() == 0, "Dataset contains null values"


@test
def test_three_classes(df: pd.DataFrame) -> None:
    n_classes = df["target"].nunique()
    assert n_classes == 3, f"Expected 3 classes, got {n_classes}"
