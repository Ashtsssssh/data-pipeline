"""
iris_project/transformers/train_model.py
Mage transformer block — trains a DecisionTreeClassifier and returns predictions.
Accepts --runtime-vars max_depth=N to sweep depths.
"""

try:
    from mage_ai.data_preparation.decorators import transformer, test
except ImportError:
    def transformer(fn):
        return fn
    def test(fn):
        return fn

import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score


@transformer
def transform(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
    """
    Train a DecisionTreeClassifier.
    Runtime variable:
        max_depth (int, default=3)  — passed via --runtime-vars max_depth=N
    Returns the original DataFrame with added columns:
        predicted, test_accuracy
    """
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

    print(f"[train_model] max_depth={max_depth}  "
          f"test_accuracy={df['test_accuracy'].iloc[0]:.4f}")
    return df


# ---------------------------------------------------------------------------
# @test — GATE: accuracy must be >= 0.90 to allow save_results to run
# ---------------------------------------------------------------------------
@test
def test_accuracy_gate(df: pd.DataFrame) -> None:
    """
    Block save_results from running if test accuracy is below threshold.
    This is better than saving first and checking afterwards because
    the bad file never reaches disk.
    """
    acc = df["test_accuracy"].iloc[0]
    assert acc >= 0.90, (
        f"Test accuracy {acc:.4f} is below the 0.90 threshold — "
        "save_results will NOT run."
    )
