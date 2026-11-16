"""
iris_project/transformers/train_model.py
Mage transformer block — trains a DecisionTreeClassifier and returns predictions.
Accepts --runtime-vars max_depth=N to sweep depths.
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
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score


@transformer
def transform(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
    max_depth = int(kwargs.get("max_depth", 3))

    feature_cols = [
        "sepal length (cm)", "sepal width (cm)",
        "petal length (cm)", "petal width (cm)",
    ]

    train_df = df[df["split"] == "train"]
    test_df  = df[df["split"] == "test"]

    X_train, y_train = train_df[feature_cols], train_df["target"]
    X_test,  y_test  = test_df[feature_cols],  test_df["target"]

    clf = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
    clf.fit(X_train, y_train)

    df = df.copy()
    df["predicted"]     = clf.predict(df[feature_cols])
    df["test_accuracy"] = accuracy_score(y_test, clf.predict(X_test))

    print(f"[train_model] max_depth={max_depth} test_accuracy={df['test_accuracy'].iloc[0]:.4f}")
    return df


@test
def test_accuracy_gate(df: pd.DataFrame) -> None:
    acc = df["test_accuracy"].iloc[0]
    assert acc >= 0.90, (
        f"Test accuracy {acc:.4f} is below the 0.90 threshold — "
        "save_results will NOT run."
    )
