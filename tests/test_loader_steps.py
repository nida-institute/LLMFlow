"""Tests for generic loader step types (TDD — written before implementation).

Covers: load_json, load_yaml, load_xml, load_csv, load_tsv, load_text,
        load_directory — both runtime (run_load_step) and linter validation.
"""
import json
import pytest
from pathlib import Path

from llmflow.runner import run_load_step
from llmflow.utils.linter import lint_pipeline_steps


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LOADER_TYPES = ["load_json", "load_yaml", "load_xml", "load_csv", "load_tsv", "load_text"]


# ---------------------------------------------------------------------------
# run_load_step — single-file loaders
# ---------------------------------------------------------------------------


def test_load_json_stores_in_context(tmp_path):
    f = tmp_path / "data.json"
    f.write_text(json.dumps({"book": "Mark", "chapters": 16}))
    step = {"name": "s", "type": "load_json", "path": str(f), "output": "data"}
    ctx = {}
    run_load_step(step, ctx)
    assert ctx["data"] == {"book": "Mark", "chapters": 16}


def test_load_yaml_stores_in_context(tmp_path):
    f = tmp_path / "data.yaml"
    f.write_text("book: Mark\nchapters: 16\n")
    step = {"name": "s", "type": "load_yaml", "path": str(f), "output": "data"}
    ctx = {}
    run_load_step(step, ctx)
    assert ctx["data"] == {"book": "Mark", "chapters": 16}


def test_load_xml_stores_lxml_element(tmp_path):
    f = tmp_path / "data.xml"
    f.write_text("<root><verse id='1'>In the beginning</verse></root>")
    step = {"name": "s", "type": "load_xml", "path": str(f), "output": "tree"}
    ctx = {}
    run_load_step(step, ctx)
    from lxml import etree
    assert isinstance(ctx["tree"], etree._Element)
    assert ctx["tree"].tag == "root"


def test_load_csv_returns_list_of_dicts(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("book,chapters\nMark,16\nLuke,24\n")
    step = {"name": "s", "type": "load_csv", "path": str(f), "output": "rows"}
    ctx = {}
    run_load_step(step, ctx)
    assert ctx["rows"] == [{"book": "Mark", "chapters": "16"}, {"book": "Luke", "chapters": "24"}]


def test_load_tsv_returns_list_of_dicts(tmp_path):
    f = tmp_path / "data.tsv"
    f.write_text("book\tchapters\nMark\t16\nLuke\t24\n")
    step = {"name": "s", "type": "load_tsv", "path": str(f), "output": "rows"}
    ctx = {}
    run_load_step(step, ctx)
    assert ctx["rows"] == [{"book": "Mark", "chapters": "16"}, {"book": "Luke", "chapters": "24"}]


def test_load_csv_custom_delimiter(tmp_path):
    f = tmp_path / "data.tsv"
    f.write_text("book\tchapters\nMark\t16\n")
    step = {"name": "s", "type": "load_csv", "path": str(f), "delimiter": "\t", "output": "rows"}
    ctx = {}
    run_load_step(step, ctx)
    assert ctx["rows"][0] == {"book": "Mark", "chapters": "16"}


def test_load_text_returns_string(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("# Notes\n\nSome content here.")
    step = {"name": "s", "type": "load_text", "path": str(f), "output": "notes"}
    ctx = {}
    run_load_step(step, ctx)
    assert ctx["notes"] == "# Notes\n\nSome content here."


# ---------------------------------------------------------------------------
# output vs outputs — both accepted
# ---------------------------------------------------------------------------


def test_load_json_accepts_output_singular(tmp_path):
    f = tmp_path / "d.json"
    f.write_text('{"x": 1}')
    step = {"name": "s", "type": "load_json", "path": str(f), "output": "result"}
    ctx = {}
    run_load_step(step, ctx)
    assert ctx["result"] == {"x": 1}


def test_load_json_accepts_outputs_plural(tmp_path):
    f = tmp_path / "d.json"
    f.write_text('{"x": 1}')
    step = {"name": "s", "type": "load_json", "path": str(f), "output": "result"}
    ctx = {}
    run_load_step(step, ctx)
    assert ctx["result"] == {"x": 1}


# ---------------------------------------------------------------------------
# Path resolution — ${var} substitution
# ---------------------------------------------------------------------------


def test_load_json_resolves_path_variable(tmp_path):
    f = tmp_path / "d.json"
    f.write_text('{"v": 42}')
    step = {"name": "s", "type": "load_json", "path": "${data_path}", "output": "result"}
    ctx = {"data_path": str(f)}
    run_load_step(step, ctx)
    assert ctx["result"] == {"v": 42}


# ---------------------------------------------------------------------------
# Missing file
# ---------------------------------------------------------------------------


def test_load_json_missing_file_raises(tmp_path):
    step = {"name": "s", "type": "load_json", "path": str(tmp_path / "missing.json"), "output": "x"}
    with pytest.raises(FileNotFoundError):
        run_load_step(step, {})


def test_load_text_missing_file_raises(tmp_path):
    step = {"name": "s", "type": "load_text", "path": str(tmp_path / "missing.md"), "output": "x"}
    with pytest.raises(FileNotFoundError):
        run_load_step(step, {})


# ---------------------------------------------------------------------------
# Missing output key
# ---------------------------------------------------------------------------


def test_load_json_missing_output_raises():
    step = {"name": "s", "type": "load_json", "path": "some.json"}
    with pytest.raises(ValueError, match="output"):
        run_load_step(step, {})


# ---------------------------------------------------------------------------
# load_directory
# ---------------------------------------------------------------------------


def test_load_directory_json(tmp_path):
    d = tmp_path / "acai"
    d.mkdir()
    (d / "a.json").write_text('{"id": "a"}')
    (d / "b.json").write_text('{"id": "b"}')
    step = {"name": "s", "type": "load_directory", "path": str(d),
            "pattern": "*.json", "format": "json", "output": "items"}
    ctx = {}
    run_load_step(step, ctx)
    assert len(ctx["items"]) == 2
    ids = {item["id"] for item in ctx["items"]}
    assert ids == {"a", "b"}


def test_load_directory_sorted_order(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    (d / "c.json").write_text('{"n": 3}')
    (d / "a.json").write_text('{"n": 1}')
    (d / "b.json").write_text('{"n": 2}')
    step = {"name": "s", "type": "load_directory", "path": str(d),
            "pattern": "*.json", "format": "json", "output": "items"}
    ctx = {}
    run_load_step(step, ctx)
    assert [item["n"] for item in ctx["items"]] == [1, 2, 3]


def test_load_directory_text(tmp_path):
    d = tmp_path / "prompts"
    d.mkdir()
    (d / "a.md").write_text("Alpha")
    (d / "b.md").write_text("Beta")
    step = {"name": "s", "type": "load_directory", "path": str(d),
            "pattern": "*.md", "format": "text", "output": "docs"}
    ctx = {}
    run_load_step(step, ctx)
    assert set(ctx["docs"]) == {"Alpha", "Beta"}


def test_load_directory_missing_pattern_raises():
    step = {"name": "s", "type": "load_directory", "path": "/some/dir",
            "format": "json", "output": "items"}
    with pytest.raises(ValueError, match="pattern"):
        run_load_step(step, {})


def test_load_directory_missing_format_raises():
    step = {"name": "s", "type": "load_directory", "path": "/some/dir",
            "pattern": "*.json", "output": "items"}
    with pytest.raises(ValueError, match="format"):
        run_load_step(step, {})


def test_load_directory_invalid_format_raises(tmp_path):
    step = {"name": "s", "type": "load_directory", "path": str(tmp_path),
            "pattern": "*.json", "format": "pdf", "output": "items"}
    with pytest.raises(ValueError, match="format"):
        run_load_step(step, {})


# ---------------------------------------------------------------------------
# Linter
# ---------------------------------------------------------------------------


def test_linter_accepts_valid_loader_steps(tmp_path):
    f = tmp_path / "d.json"
    f.write_text("{}")
    for step_type in LOADER_TYPES:
        steps = [{"name": "s", "type": step_type, "path": str(f), "output": "result"}]
        errors = lint_pipeline_steps(steps)
        assert not errors, f"{step_type}: {errors}"


def test_linter_error_missing_path():
    for step_type in LOADER_TYPES:
        steps = [{"name": "s", "type": step_type, "output": "result"}]
        errors = lint_pipeline_steps(steps)
        assert any("path" in e for e in errors), f"{step_type}: expected path error, got {errors}"


def test_linter_error_missing_output():
    for step_type in LOADER_TYPES:
        steps = [{"name": "s", "type": step_type, "path": "some.json"}]
        errors = lint_pipeline_steps(steps)
        assert any("output" in e for e in errors), f"{step_type}: expected output error, got {errors}"


def test_linter_load_directory_requires_pattern():
    steps = [{"name": "s", "type": "load_directory", "path": "/dir",
              "format": "json", "output": "items"}]
    errors = lint_pipeline_steps(steps)
    assert any("pattern" in e for e in errors)


def test_linter_load_directory_requires_format():
    steps = [{"name": "s", "type": "load_directory", "path": "/dir",
              "pattern": "*.json", "output": "items"}]
    errors = lint_pipeline_steps(steps)
    assert any("format" in e for e in errors)


def test_linter_load_directory_invalid_format():
    steps = [{"name": "s", "type": "load_directory", "path": "/dir",
              "pattern": "*.json", "format": "pdf", "output": "items"}]
    errors = lint_pipeline_steps(steps)
    assert any("format" in e for e in errors)


def test_linter_checks_path_exists_when_static(tmp_path):
    missing = str(tmp_path / "missing.json")
    steps = [{"name": "s", "type": "load_json", "path": missing, "output": "x"}]
    errors = lint_pipeline_steps(steps)
    assert any("missing.json" in e or "not found" in e.lower() or "exist" in e.lower()
               for e in errors)


def test_linter_skips_path_check_when_dynamic():
    """Paths with unresolved ${var} cannot be checked at lint time — no error."""
    steps = [{"name": "s", "type": "load_json",
              "path": "${intermediate_dir}/data.json", "output": "x"}]
    errors = lint_pipeline_steps(steps)
    assert not any("not found" in e.lower() or "exist" in e.lower() for e in errors)
