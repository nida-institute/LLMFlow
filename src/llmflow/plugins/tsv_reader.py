"""TSV/CSV reader plugin for loading tabular data.

Deprecated: prefer type: load_tsv / type: load_csv steps.
The filtering logic (where, limit, offset, columns) now lives in
llmflow.utils.data.apply_tabular_filters and is shared by both paths.
"""

import csv
from pathlib import Path
from typing import Iterator

from llmflow.modules.logger import Logger
from llmflow.utils.data import apply_tabular_filters

logger = Logger()


class Row:
    """Row object with dot notation and dict-like access (legacy plugin surface)."""

    def __init__(self, data: dict):
        self._data = data
        for key, value in data.items():
            setattr(self, key, value)

    def __getitem__(self, key):
        return self._data[key]

    def __repr__(self):
        return f"Row({self._data})"

    def to_dict(self):
        return self._data.copy()


def execute(step_config) -> Iterator[Row]:
    """Read TSV/CSV file and yield Row objects (legacy plugin interface).

    Prefer type: load_tsv or type: load_csv steps instead.
    """
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

    delimiter = config.get("delimiter", "\t")

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = list(reader)

    rows = apply_tabular_filters(rows, config)
    return (Row(r) for r in rows)


def register():
    """Register the tsv plugin."""
    return {
        "tsv": execute
    }
