"""
iris_project/data_loaders/load_iris.py
Mage data loader block — loads the sklearn Iris dataset as a DataFrame.
"""

# ---------------------------------------------------------------------------
# Graceful import: decorators are no-ops when mage_ai is not installed,
# so this file can be imported directly by pytest.
# ---------------------------------------------------------------------------
try:
    from mage_ai.data_preparation.decorators import data_loader, test
except ImportError:
    def data_loader(fn):
        return fn
    def test(fn):
        return fn

import pandas as pd
from sklearn.datasets import load_iris


@data_loader
def load_data(*args, **kwargs) -> pd.DataFrame:
    """
    Load the Iris dataset from sklearn and return it as a pandas DataFrame.
    Columns: sepal length (cm), sepal width (cm), petal length (cm),
             petal width (cm), target
    """
    iris = load_iris(as_frame=True)
    df = iris.frame  # 150 rows × 5 columns
    df["target_name"] = df["target"].map(
        dict(enumerate(iris.target_names))
    )
    return df


# ---------------------------------------------------------------------------
# @test — gate: block fails if dataset is wrong shape or has nulls
# ---------------------------------------------------------------------------
@test
def test_dataset_shape(df: pd.DataFrame) -> None:
    """Iris must be 150 rows, 6 columns (5 original + target_name)."""
    assert df is not None, "Loaded dataframe is None"
    assert df.shape == (150, 6), f"Expected (150, 6), got {df.shape}"
    assert df.isnull().sum().sum() == 0, "Dataset contains null values"


@test
def test_three_classes(df: pd.DataFrame) -> None:
    """Iris must have exactly 3 target classes."""
    n_classes = df["target"].nunique()
    assert n_classes == 3, f"Expected 3 classes, got {n_classes}"
