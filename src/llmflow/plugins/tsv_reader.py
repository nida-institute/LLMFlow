"""TSV/CSV reader plugin for loading tabular data."""

import csv
import re
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


# Matches: column == 'value' or column == "value"
_EQ_RE = re.compile(r'^(\w+)\s*==\s*[\'"]([^\'"]*)[\'"]$')
# Matches: column startswith 'prefix'
_STARTSWITH_RE = re.compile(r'^(\w+)\s+startswith\s+[\'"]([^\'"]*)[\'"]$')
# Matches: book(column) == 'value', chapter(column) == 'value', etc.
_USFM_RE = re.compile(r'^(book|chapter|verse|word)\((\w+)\)\s*==\s*[\'"]([^\'"]*)[\'"]$')


def _extract_usfm_part(cell: str, part: str) -> str:
    """Extract book/chapter/verse/word from a USFM ref like 'PHM 1:10!3'."""
    # Expected format: "BOOK chapter:verse!word"
    try:
        book, cv = cell.split(" ", 1)       # "PHM", "1:10!3"
        if part == "book":
            return book
        cv_part, word = (cv.split("!", 1) if "!" in cv else (cv, ""))
        chapter, verse = cv_part.split(":", 1)
        if part == "chapter":
            return chapter
        if part == "verse":
            return verse
        if part == "word":
            return word
    except (ValueError, AttributeError):
        pass
    return ""


def _parse_where(where_expr: str) -> list[tuple[str, str, str, str]]:
    """Parse a where expression into a list of (extractor, column, operator, value) tuples.

    extractor is one of: '' (plain column), 'book', 'chapter', 'verse', 'word'.
    operator is one of: '==', 'startswith'.

    Supported forms (joined by 'and'):
        column == 'value'
        column startswith 'prefix'
        book(column) == 'value'
        chapter(column) == 'value'
        verse(column) == 'value'
        word(column) == 'value'
    """
    conditions = []
    for atom in (a.strip() for a in where_expr.split(" and ")):
        m = _USFM_RE.match(atom)
        if m:
            conditions.append((m.group(1), m.group(2), "==", m.group(3)))
            continue
        m = _EQ_RE.match(atom)
        if m:
            conditions.append(("", m.group(1), "==", m.group(2)))
            continue
        m = _STARTSWITH_RE.match(atom)
        if m:
            conditions.append(("", m.group(1), "startswith", m.group(2)))
            continue
        raise ValueError(
            f"tsv_reader: cannot parse where condition: {atom!r}. "
            "Supported: column == 'value'  |  column startswith 'prefix'  |  "
            "book/chapter/verse/word(column) == 'value'  (joined by 'and')"
        )
    return conditions


def _matches(row_dict: dict, extractor: str, col: str, op: str, val: str) -> bool:
    """Test one condition against a row."""
    cell = row_dict.get(col, "")
    if extractor:
        cell = _extract_usfm_part(cell, extractor)
    if op == "==":
        return cell == val
    if op == "startswith":
        return cell.startswith(val)
    return False  # unreachable: _parse_where rejects unknown operators


def execute(step_config) -> Iterator[Row]:
    """
    Read TSV/CSV file and yield Row objects.

    Args:
        step_config: Dictionary containing:
            - inputs: Dict with:
                - path: Path to file (can use 'from' as alias)
                - limit: Optional max rows to read (applied after where)
                - offset: Optional number of rows to skip (applied after where)
                - delimiter: Optional delimiter (default: tab)
                - where: Optional filter expression, e.g. "book == 'GEN' and chapter == '1'"
                - columns: Optional list of column names to include

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
    offset = int(config.get("offset", 0))
    delimiter = config.get("delimiter", "\t")
    where = config.get("where")
    columns = config.get("columns")

    where_conditions = _parse_where(where) if where else None

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)

        # Validate columns against file header before iterating
        fieldnames = list(reader.fieldnames or [])
        if columns:
            unknown = [c for c in columns if c not in fieldnames]
            if unknown:
                raise ValueError(
                    f"tsv_reader: unknown columns: {unknown}. Available: {fieldnames}"
                )

        # Warn once if a where condition references a column not in the file
        if where_conditions:
            for _ext, col, _op, _val in where_conditions:
                if col not in fieldnames:
                    logger.warning(
                        f"tsv_reader: where condition references unknown column {col!r} — no rows will match"
                    )
                    return

        filtered = 0
        yielded = 0
        for row_dict in reader:
            # Apply where filter
            if where_conditions:
                if not all(_matches(row_dict, ext, col, op, val) for ext, col, op, val in where_conditions):
                    continue

            filtered += 1
            if filtered <= offset:
                continue
            if limit and yielded >= int(limit):
                break

            # Apply column projection
            if columns:
                row_dict = {k: row_dict[k] for k in columns}

            yield Row(row_dict)
            yielded += 1


def register():
    """Register the tsv plugin."""
    return {
        "tsv": execute
    }
