"""One syntax per concept — no aliases (project/plans/design-schema-single-source.md).

The language had four ad hoc duplications: `outputs`/`output`, `template`/`format_with`,
`timeout`/`timeout_seconds`, and hyphenated `group-by`/`order-by` against an otherwise
underscored vocabulary. Each was a second spelling the engine honoured silently, so a
reader could not tell which was canonical.

These tests pin the single spelling and assert the discarded ones are gone — from the
engine, from the linter, and from the editor schema that authors actually see while typing.
"""
import json
import pathlib

import pytest

from llmflow.pipeline_schema import allowed_step_keys, step_keys
from llmflow.utils.linter import COMMON_TYPOS, lint_pipeline_steps

REPO = pathlib.Path(__file__).resolve().parent.parent
EDITOR_SCHEMA = REPO / "src" / "llmflow" / "schema" / "pipeline.schema.json"


# --- the discarded spellings are gone -------------------------------------------------


@pytest.mark.parametrize("gone", ["outputs", "format_with", "timeout", "group-by", "order-by"])
def test_discarded_spelling_is_not_declared(gone):
    assert gone not in step_keys()


@pytest.mark.parametrize("canonical", ["output", "template", "timeout_seconds",
                                       "group_by", "order_by"])
def test_canonical_spelling_is_declared(canonical):
    assert canonical in step_keys()


def test_canonical_spellings_land_on_the_right_types():
    assert "template" in allowed_step_keys("llm")
    assert "timeout_seconds" in allowed_step_keys("basex")
    assert "timeout_seconds" in allowed_step_keys("llm")
    assert {"group_by", "order_by"} <= allowed_step_keys("for-each")


# --- the linter names the replacement -------------------------------------------------


@pytest.mark.parametrize("old,new", [
    ("outputs", "output"),
    ("format_with", "template"),
    ("group-by", "group_by"),
    ("order-by", "order_by"),
])
def test_discarded_spelling_is_a_lint_error_naming_its_replacement(old, new):
    assert COMMON_TYPOS.get(old) == new, f"{old} should hint at {new}"


def test_outputs_on_a_step_is_an_error_pointing_at_output():
    """`outputs` was the redundant plural; a step produces one result (see
    project/plans/design-pipeline-schema.md §1)."""
    errors = lint_pipeline_steps([{"name": "s", "type": "function",
                                   "function": "m.f", "outputs": "r"}])
    assert errors
    assert "outputs" in errors[0] and "output" in errors[0]


def test_hyphenated_loop_keys_are_errors_pointing_at_underscores():
    errors = lint_pipeline_steps([{"name": "loop", "type": "for-each", "in": "${xs}",
                                   "for": "item", "group-by": "${item.book}", "steps": []}])
    assert errors
    assert "group-by" in errors[0] and "group_by" in errors[0]


def test_underscored_loop_keys_pass():
    steps = [{"name": "loop", "type": "for-each", "in": "${xs}", "for": "item",
              "group_by": "${item.book}", "order_by": {"key": "${item}"},
              "steps": [{"name": "inner", "type": "llm", "prompt": "p.gpt"}]}]
    assert lint_pipeline_steps(steps) == []


def test_basex_uses_timeout_seconds():
    steps = [{"name": "q", "type": "basex", "database": "acai", "query_file": "q.xq",
              "timeout_seconds": 60, "output": "r"}]
    assert lint_pipeline_steps(steps) == []
    assert lint_pipeline_steps([{"name": "q", "type": "basex", "database": "acai",
                                 "query_file": "q.xq", "timeout": 60, "output": "r"}])


# --- one syntax means one declaration: the editor schema must agree -------------------


def _editor_step_keys() -> set:
    """Every step property the editor schema declares, across all its per-type $defs."""
    schema = json.loads(EDITOR_SCHEMA.read_text(encoding="utf-8"))
    keys: set = set()

    def walk(node):
        if isinstance(node, dict):
            props = node.get("properties")
            if isinstance(props, dict):
                keys.update(props)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for name, defn in schema.get("$defs", {}).items():
        if name.endswith("Step") or name == "CommonStepFields":
            walk(defn)
    return keys


def test_editor_schema_declares_no_discarded_spelling():
    """`.vscode/settings.json` wires this schema to pipelines/**/*.yaml, so it is what an
    author sees while typing. If it still offers `outputs:`, the language has two syntaxes
    no matter what the engine accepts.
    """
    offenders = _editor_step_keys() & {"outputs", "format_with", "timeout",
                                       "group-by", "order-by"}
    assert not offenders, (
        "src/llmflow/schema/pipeline.schema.json still declares discarded spellings: "
        f"{sorted(offenders)}"
    )


def test_editor_schema_declares_no_key_the_engine_rejects():
    """Every key the editor autocompletes must be real. The reverse direction is not
    asserted: the editor schema may lag on newly added keys, but it must never teach a
    key the engine would reject.
    """
    unknown = _editor_step_keys() - step_keys() - {"description"}
    assert not unknown, (
        "Editor schema declares step keys PIPELINE_SCHEMA does not: " f"{sorted(unknown)}"
    )
