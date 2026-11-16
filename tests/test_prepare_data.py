"""
tests/test_prepare_data.py
Part A — CI gate test for the Mage prepare_data transformer.

The block file can be imported outside Mage because it only imports
the decorators when the mage_ai package is present (they are no-ops
otherwise). This lets pytest pick it up without a running Mage server.
"""

import sys
import os

# Allow importing the iris_project package without installing it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sklearn.datasets import load_iris
from iris_project.transformers.prepare_data import transform


def test_split_is_80_20():
    """
    The prepare_data transformer must split 150 Iris rows into
    120 training rows and 30 test rows (80 / 20 split).
    """
    df = load_iris(as_frame=True).frame
    out = transform(df)

    assert "split" in out.columns, "Output must contain a 'split' column"
    assert (out["split"] == "train").sum() == 120, \
        f"Expected 120 train rows, got {(out['split'] == 'train').sum()}"
    assert (out["split"] == "test").sum() == 30, \
        f"Expected 30 test rows, got {(out['split'] == 'test').sum()}"


def test_output_has_all_rows():
    """No rows should be dropped during the split."""
    df = load_iris(as_frame=True).frame
    out = transform(df)
    assert len(out) == 150, f"Expected 150 total rows, got {len(out)}"


def test_split_column_values():
    """The split column should only contain 'train' or 'test'."""
    df = load_iris(as_frame=True).frame
    out = transform(df)
    unique_values = set(out["split"].unique())
    assert unique_values == {"train", "test"}, \
        f"Unexpected split values: {unique_values}"
