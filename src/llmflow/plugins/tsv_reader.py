"""TSV/CSV reader plugin for loading tabular data."""

import csv
from pathlib import Path
from typing import Iterator

from llmflow.modules.logger import Logger

logger = Logger()


class Row:
    """Row object that supports both dot notation and dict-like access"""

    def __init__(self, data: dict):
        self._data = data
        for key, value in data.items():
            setattr(self, key, value)

    def __getitem__(self, key):
        """Support dict-like access: row['key']"""
        return self._data[key]

    def __repr__(self):
        return f"Row({self._data})"

    def to_dict(self):
        """Convert to plain dictionary"""
        return self._data.copy()


def execute(step_config) -> Iterator[Row]:
    """
    Read TSV/CSV file and yield Row objects.

    Args:
        step_config: Dictionary containing:
            - inputs: Dict with:
                - path: Path to file (can use 'from' as alias)
                - limit: Optional max rows to read
                - delimiter: Optional delimiter (default: tab)

    Yields:
        Row objects with dot notation and dict-like access
    """
    # Support both old (inputs nested) and new (flat) config structure
    if "inputs" in step_config:
        config = step_config["inputs"]
    else:
        config = step_config

    path = config.get("path") or config.get("from")
    if not path:
        raise ValueError("tsv_reader requires 'path' or 'from' key")

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"TSV file not found: {path}")

    limit = config.get("limit")
    delimiter = config.get("delimiter", "\t")

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)

        for i, row_dict in enumerate(reader):
            if limit and i >= limit:
                break
            yield Row(row_dict)


def register():
    """Register the tsv plugin."""
    return {
        "tsv": execute
    }