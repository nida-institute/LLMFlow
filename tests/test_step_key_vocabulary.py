"""Per-type step vocabulary (project/plans/design-schema-single-source.md).

`PIPELINE_SCHEMA` is the single declaration of the step vocabulary, and it is *per type*:
which keys a step may carry depends on its `type`. These tests cover what that buys —

- a key that is real but belongs to another type is a lint **error**, where the global
  allowed-set accepted it and the handler then ignored it silently;
- plugin / registered types stay permissive (they receive the whole step dict);
- one spelling per concept: `outputs`, never `output` (see test_one_syntax.py);
- the linter keeps no key list of its own.
"""
import pytest

from llmflow.pipeline_schema import allowed_step_keys, common_step_keys, step_keys
from llmflow.utils.linter import lint_pipeline_steps


# --- the schema's per-type derivation -------------------------------------------------


def test_llm_keys_are_not_valid_on_a_function_step():
    assert "output_type" in allowed_step_keys("llm")
    assert "output_type" not in allowed_step_keys("function")


def test_loop_keys_are_not_valid_on_an_llm_step():
    assert "cursor" not in step_keys()          # nested !window_advance key, not a step key
    assert "size" in allowed_step_keys("window")
    assert "size" not in allowed_step_keys("llm")


def test_common_keys_are_valid_on_every_declared_type():
    for step_type in ("llm", "function", "for-each", "window", "if", "json", "save", "basex"):
        assert common_step_keys() <= allowed_step_keys(step_type), step_type


def test_registered_and_unknown_types_are_permissive():
    """Plugin steps get the whole step dict as a flat config, so keys can't be enumerated."""
    assert allowed_step_keys("xpath") is None
    assert allowed_step_keys("tsv") is None


def test_step_keys_is_the_union_of_every_type():
    union = set()
    for step_type in ("llm", "function", "duckdb", "basex", "for-each", "window", "if",
                      "json", "save", "load_csv"):
        union |= allowed_step_keys(step_type)
    assert union <= step_keys()
    assert {"output_type", "size", "value", "content", "columns"} <= step_keys()


def test_loader_filter_keys_are_declared():
    """utils/data.py reads these top-level on load_* steps; all are covered by tests."""
    allowed = allowed_step_keys("load_csv")
    assert {"key", "where", "limit", "offset", "columns"} <= allowed
    assert {"xpath", "namespaces", "output_format"} <= allowed_step_keys("load_xml")


def test_dead_keys_are_gone():
    """Never read top-level by run_llm_step — only nested in llm_options/response_format."""
    assert {"tools", "response_mime_type", "response_schema"} & step_keys() == set()


# --- the linter enforces it -----------------------------------------------------------


def test_wrong_type_key_is_an_error_not_a_silent_ignore():
    steps = [{"name": "s", "type": "function", "function": "m.f", "output_type": "json"}]
    errors = lint_pipeline_steps(steps)
    assert errors, "output_type on a function step must not be accepted"
    assert "output_type" in errors[0]
    assert "'function'" in errors[0]


def test_query_file_on_an_llm_step_is_an_error():
    steps = [{"name": "s", "type": "llm", "query_file": "q.xq"}]
    errors = lint_pipeline_steps(steps)
    assert errors
    assert "query_file" in errors[0]


def test_correct_per_type_keys_pass():
    steps = [
        {"name": "gen", "type": "llm", "prompt": "p.gpt", "output_type": "json",
         "output": "r", "description": "doc", "log": "info"},
        {"name": "call", "type": "function", "function": "m.f", "inputs": {}, "output": "r"},
        {"name": "win", "type": "window", "in": "${xs}", "for": "item", "size": 3,
         "steps": [{"name": "inner", "type": "llm", "prompt": "p.gpt"}]},
        {"name": "db", "type": "basex", "database": "acai", "query_file": "q.xq",
         "inputs": {"book": "MRK"}, "output": "r"},
        # Templated path: the loader's on-disk existence check only fires on literal paths.
        {"name": "rows", "type": "load_csv", "path": "${data_file}", "output": "r",
         "where": "ref == 'GEN 1:1'", "limit": 2, "columns": ["ref"]},
    ]
    assert lint_pipeline_steps(steps) == []


def test_plugin_step_keys_are_not_rejected():
    steps = [{"name": "x", "type": "xpath", "path": "a.xml", "xpath": "//v",
              "output_format": "text", "output": "r"}]
    assert lint_pipeline_steps(steps) == []


def test_unknown_key_still_reports_as_unknown_with_typo_hint():
    steps = [{"name": "s", "type": "for-each", "apend_to": "${x}", "steps": []}]
    errors = lint_pipeline_steps(steps)
    assert errors
    assert "unknown keyword 'apend_to'" in errors[0]
    assert "append_to" in errors[0]


def test_loop_modifier_keys_are_valid():
    steps = [{"name": "loop", "type": "for-each", "in": "${xs}", "for": "item",
              "group_by": "${item.book}", "order_by": {"key": "${item}"},
              "steps": [{"name": "inner", "type": "llm", "prompt": "p.gpt"}]}]
    assert lint_pipeline_steps(steps) == []


# --- one output spelling ---------------------------------------------------------------


def test_outputs_is_the_only_output_spelling():
    steps = [{"name": "j", "type": "json", "output": "obj", "value": {"a": 1}}]
    assert lint_pipeline_steps(steps) == []


def test_outputs_does_not_warn():
    warnings = []
    steps = [{"name": "s", "type": "function", "function": "m.f", "output": "r"}]
    lint_pipeline_steps(steps, warnings=warnings)
    assert warnings == []


# --- one source ------------------------------------------------------------------------


def test_linter_keeps_no_step_key_list_of_its_own():
    """The pre-existing second source (`_EXTRA_STEP_KEYS` / `ALLOWED_STEP_KEYS`) is gone."""
    from llmflow.utils import linter

    assert not hasattr(linter, "_EXTRA_STEP_KEYS")
    assert not hasattr(linter, "ALLOWED_STEP_KEYS")
    assert not hasattr(linter, "_SCHEMA_STEP_KEYS")
