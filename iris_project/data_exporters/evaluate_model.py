"""
iris_project/data_exporters/evaluate_model.py
Mage data exporter block (Part C3) — evaluation branch off train_model.
Prints confusion matrix and per-class metrics; does NOT save predictions.
Runs in parallel with save_results as a second downstream of train_model.
"""

try:
    from mage_ai.data_preparation.decorators import data_exporter, test
except ImportError:
    def data_exporter(fn):
        return fn
    def test(fn):
        return fn

import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
)


@data_exporter
def export_data(df: pd.DataFrame, *args, **kwargs) -> None:
    """
    Compute and print the confusion matrix and classification report
    for the test-set predictions produced by train_model.
    """
    test_df = df[df["split"] == "test"].copy()

    y_true = test_df["target"].values
    y_pred = test_df["predicted"].values

    cm = confusion_matrix(y_true, y_pred)
    report = classification_report(
        y_true, y_pred,
        target_names=["setosa", "versicolor", "virginica"],
    )
    acc = accuracy_score(y_true, y_pred)

    print("=" * 50)
    print("CONFUSION MATRIX (test set)")
    print("=" * 50)
    print(pd.DataFrame(
        cm,
        index=["true_setosa", "true_versicolor", "true_virginica"],
        columns=["pred_setosa", "pred_versicolor", "pred_virginica"],
    ).to_string())
    print()
    print("CLASSIFICATION REPORT")
    print(report)
    print(f"Overall test accuracy: {acc:.4f}")
    print("=" * 50)


@test
def test_evaluation_ran(output=None, *args, **kwargs) -> None:
    """Evaluation block is considered passing if it runs without error."""
    pass  # Errors in export_data() will cause this block to fail automatically
