"""Tests for where/limit/offset/columns filtering on load_tsv and load_csv steps."""
import pytest
from pathlib import Path
from llmflow.runner import run_load_step
from llmflow.utils.data import apply_tabular_filters


# ---------------------------------------------------------------------------
# Unit tests for apply_tabular_filters
# ---------------------------------------------------------------------------

ROWS = [
    {"ref": "GEN 1:1", "text": "In the beginning", "lang": "en"},
    {"ref": "GEN 1:2", "text": "The earth was void", "lang": "en"},
    {"ref": "GEN 2:1", "text": "Thus the heavens", "lang": "en"},
    {"ref": "EXO 1:1", "text": "These are the names", "lang": "en"},
    {"ref": "EXO 1:2", "text": "Reuben and Simeon", "lang": "en"},
]


class TestApplyTabularFilters:
    def test_no_filters_returns_all(self):
        result = apply_tabular_filters(ROWS, {})
        assert result == ROWS

    def test_where_eq(self):
        result = apply_tabular_filters(ROWS, {"where": "ref == 'GEN 1:1'"})
        assert len(result) == 1
        assert result[0]["ref"] == "GEN 1:1"

    def test_where_startswith(self):
        result = apply_tabular_filters(ROWS, {"where": "ref startswith 'GEN'"})
        assert len(result) == 3
        assert all(r["ref"].startswith("GEN") for r in result)

    def test_where_usfm_book(self):
        result = apply_tabular_filters(ROWS, {"where": "book(ref) == 'EXO'"})
        assert len(result) == 2
        assert all(r["ref"].startswith("EXO") for r in result)

    def test_where_usfm_chapter(self):
        result = apply_tabular_filters(ROWS, {"where": "chapter(ref) == '1' and book(ref) == 'GEN'"})
        assert len(result) == 2

    def test_where_and(self):
        result = apply_tabular_filters(ROWS, {"where": "book(ref) == 'GEN' and chapter(ref) == '2'"})
        assert len(result) == 1
        assert result[0]["ref"] == "GEN 2:1"

    def test_limit(self):
        result = apply_tabular_filters(ROWS, {"limit": 2})
        assert result == ROWS[:2]

    def test_offset(self):
        result = apply_tabular_filters(ROWS, {"offset": 2})
        assert result == ROWS[2:]

    def test_limit_and_offset(self):
        result = apply_tabular_filters(ROWS, {"offset": 1, "limit": 2})
        assert result == ROWS[1:3]

    def test_columns(self):
        result = apply_tabular_filters(ROWS, {"columns": ["ref", "text"]})
        assert all(set(r.keys()) == {"ref", "text"} for r in result)

    def test_where_then_limit(self):
        # limit applied after where
        result = apply_tabular_filters(ROWS, {"where": "book(ref) == 'GEN'", "limit": 2})
        assert len(result) == 2
        assert all(r["ref"].startswith("GEN") for r in result)

    def test_unknown_column_in_where_returns_empty(self):
        result = apply_tabular_filters(ROWS, {"where": "nonexistent == 'foo'"})
        assert result == []

    def test_invalid_where_raises(self):
        with pytest.raises(ValueError, match="cannot parse where condition"):
            apply_tabular_filters(ROWS, {"where": "INVALID EXPRESSION !!!"})

    def test_unknown_column_in_columns_raises(self):
        with pytest.raises(ValueError, match="unknown columns"):
            apply_tabular_filters(ROWS, {"columns": ["ref", "nonexistent"]})


# ---------------------------------------------------------------------------
# Integration tests via run_load_step
# ---------------------------------------------------------------------------

TSV_CONTENT = """\
ref\ttext\tlang
GEN 1:1\tIn the beginning\ten
GEN 1:2\tThe earth was void\ten
GEN 2:1\tThus the heavens\ten
EXO 1:1\tThese are the names\ten
EXO 1:2\tReuben and Simeon\ten
"""


@pytest.fixture
def tsv_file(tmp_path):
    p = tmp_path / "verses.tsv"
    p.write_text(TSV_CONTENT)
    return p


class TestLoadTsvStep:
    def test_basic_load(self, tsv_file):
        step = {"name": "load", "type": "load_tsv", "path": str(tsv_file), "output": "rows"}
        ctx = {}
        run_load_step(step, ctx)
        assert len(ctx["rows"]) == 5
        assert ctx["rows"][0] == {"ref": "GEN 1:1", "text": "In the beginning", "lang": "en"}

    def test_where_filter(self, tsv_file):
        step = {"name": "load", "type": "load_tsv", "path": str(tsv_file), "output": "rows",
                "where": "book(ref) == 'EXO'"}
        ctx = {}
        run_load_step(step, ctx)
        assert len(ctx["rows"]) == 2
        assert all(r["ref"].startswith("EXO") for r in ctx["rows"])

    def test_limit(self, tsv_file):
        step = {"name": "load", "type": "load_tsv", "path": str(tsv_file), "output": "rows",
                "limit": 2}
        ctx = {}
        run_load_step(step, ctx)
        assert len(ctx["rows"]) == 2

    def test_columns(self, tsv_file):
        step = {"name": "load", "type": "load_tsv", "path": str(tsv_file), "output": "rows",
                "columns": ["ref"]}
        ctx = {}
        run_load_step(step, ctx)
        assert all(list(r.keys()) == ["ref"] for r in ctx["rows"])

    def test_result_is_list_of_dicts(self, tsv_file):
        step = {"name": "load", "type": "load_tsv", "path": str(tsv_file), "output": "rows"}
        ctx = {}
        run_load_step(step, ctx)
        assert isinstance(ctx["rows"], list)
        assert isinstance(ctx["rows"][0], dict)

    def test_dot_notation_resolves_on_result(self, tsv_file):
        """${rows[0].ref} must work — confirms Row wrapper is not needed."""
        from llmflow.runner import resolve
        step = {"name": "load", "type": "load_tsv", "path": str(tsv_file), "output": "rows"}
        ctx = {}
        run_load_step(step, ctx)
        assert resolve("${rows[0].ref}", ctx) == "GEN 1:1"
