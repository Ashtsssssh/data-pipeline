"""
iris_project/data_exporters/save_results.py
Mage data exporter block — writes predictions to iris_predictions.csv.
Only runs if train_model's @test passes (accuracy >= 0.90).
"""

try:
    from mage_ai.data_preparation.decorators import data_exporter, test
except ImportError:
    def data_exporter(fn):
        return fn
    def test(fn):
        return fn

import pandas as pd
import os


OUTPUT_PATH = "iris_predictions.csv"


@data_exporter
def export_data(df: pd.DataFrame, *args, **kwargs) -> None:
    """Save the full DataFrame (with split, predicted, test_accuracy) to CSV."""
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"[save_results] Saved {len(df)} rows → {OUTPUT_PATH}")


@test
def test_file_created(output=None, *args, **kwargs) -> None:
    """Verify the CSV was actually written."""
    assert os.path.exists(OUTPUT_PATH), \
        f"Expected {OUTPUT_PATH} to exist after export"
    saved = pd.read_csv(OUTPUT_PATH)
    assert len(saved) == 150, \
        f"Expected 150 rows in CSV, got {len(saved)}"
