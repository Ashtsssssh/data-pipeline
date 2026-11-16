"""
iris_project/data_exporters/save_results.py
Mage data exporter block — writes predictions to iris_predictions.csv.
"""

if 'data_exporter' not in globals():
    try:
        from mage_ai.data_preparation.decorators import data_exporter
    except ImportError:
        def data_exporter(fn): return fn

if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(fn): return fn

import pandas as pd
import os

OUTPUT_PATH = "iris_predictions.csv"


@data_exporter
def export_data(df: pd.DataFrame, *args, **kwargs) -> None:
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"[save_results] Saved {len(df)} rows -> {OUTPUT_PATH}")


@test
def test_file_created(output=None, *args, **kwargs) -> None:
    assert os.path.exists(OUTPUT_PATH), f"Expected {OUTPUT_PATH} to exist after export"
    saved = pd.read_csv(OUTPUT_PATH)
    assert len(saved) == 150, f"Expected 150 rows in CSV, got {len(saved)}"
