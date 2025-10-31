"""TSV/CSV reader plugin for LLMFlow pipelines."""

import csv
from pathlib import Path
from typing import Any, Dict, List


class Row:
    """A row object that allows dot notation access to columns."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        return self._data.get(name)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __repr__(self):
        return f"Row({self._data})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert row back to dictionary."""
        return self._data.copy()


def execute(step_config: Dict[str, Any]) -> List[Row]:
    """
    Read a TSV/CSV file and return rows as Row objects.

    The first row is used as column headers. All subsequent rows are returned
    as Row objects where columns can be accessed via dot notation or brackets.

    Step config keys:
    - path or from: Path to the TSV/CSV file
    - delimiter: Column delimiter (default: '\t' for TSV)
    - limit: Maximum number of rows to read (optional)

    Returns:
        List of Row objects with dot-notation access to columns

    Example usage:
        - name: read-status
          type: tsv
          path: inputs/Abbot-Smith/status.tsv
          limit: 10
          outputs:
            - rows

    Then access in subsequent steps:
        - type: for-each
          input: ${rows}
          item_var: row
          steps:
            - name: process
              inputs:
                lemma: ${row.lemma}
                status: ${row.status}
    """
    # Get file path (support both 'path' and 'from')
    file_path = step_config.get("from") or step_config.get("path")
    if not file_path:
        raise ValueError("tsv_reader requires 'path' or 'from' key")

    # Get delimiter (default to tab for TSV)
    delimiter = step_config.get("delimiter", "\t")

    # Get optional limit
    limit = step_config.get("limit")
    if limit:
        limit = int(limit)

    # Read the file
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"TSV file not found: {file_path}")

    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)

        for idx, row_dict in enumerate(reader):
            if limit and idx >= limit:
                break
            rows.append(Row(row_dict))

    return rows


def register():
    """Register this plugin with LLMFlow."""
    return {
        "tsv": execute,
        "csv": lambda config: execute({**config, "delimiter": ","}),
    }