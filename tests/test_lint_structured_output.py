"""`sp lint` rejects structured-output schemas the provider will reject (LLMFlow#196).

End-to-end counterpart to test_schema_preflight.py, which unit-tests the checker. Here the
question is whether the check is reachable from the command a user actually runs, and
whether it fires on the right steps and stays quiet on the wrong ones.

Two gating decisions are pinned here:

* **`strict: true` gates the errors.** Without it OpenAI does not enforce the subset, so
  the hard rules would be false positives. A schema without `strict` gets a warning saying
  the guarantee is not in force.
* **`response_format` is the trigger, not the model name.** `response_format` with
  `json_schema` is OpenAI's API shape by construction. Gemini's equivalent is
  `response_schema` (#191) and is not measured against OpenAI's rules.
"""
import json

import pytest

from llmflow.utils.linter import lint_pipeline_full

BAD_SCHEMA = {
    "type": "object",
    "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
    "required": ["a"],                      # b missing -> 400 under strict
    "additionalProperties": False,
}

GOOD_SCHEMA = {
    "type": "object",
    "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
    "required": ["a", "b"],
    "additionalProperties": False,
}


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    """Build a one-step llm pipeline with a real prompt file, return its path.

    Prompt paths and `schema_file` both resolve against the working directory, so the
    test runs from inside tmp_path.
    """
    monkeypatch.chdir(tmp_path)

    def _build(response_format, *, linter_config=None, extra_step=None):
        (tmp_path / "prompts").mkdir(exist_ok=True)
        (tmp_path / "prompts" / "p.gpt").write_text(
            "<!--\nprompt:\n  requires:\n    - book\n-->\nSummarise {{book}}.\n",
            encoding="utf-8",
        )
        step = {
            "name": "s", "type": "llm",
            "model": "gpt-4o-2024-08-06",
            "prompt": {"file": "prompts/p.gpt", "inputs": {"book": "${book}"}},
            "output": "r",
        }
        if response_format is not None:
            step["response_format"] = response_format
        if extra_step:
            step.update(extra_step)
        cfg = {"name": "p", "variables": {"book": "Mark"}, "steps": [step]}
        if linter_config:
            cfg["linter_config"] = linter_config
        p = tmp_path / "p.yaml"
        p.write_text(json.dumps(cfg), encoding="utf-8")   # JSON is valid YAML
        return str(p)
    return _build


def _lint(path):
    return lint_pipeline_full(path)


class TestBadSchemaFailsLint:
    def test_missing_required_property_fails(self, pipeline):
        result = _lint(pipeline({
            "type": "json_schema",
            "json_schema": {"name": "s", "strict": True, "schema": BAD_SCHEMA},
        }))
        assert not result.valid
        assert any("required" in e for e in result.errors), result.errors

    def test_error_names_the_property_and_the_step(self, pipeline):
        result = _lint(pipeline({
            "type": "json_schema",
            "json_schema": {"name": "s", "strict": True, "schema": BAD_SCHEMA},
        }))
        joined = " ".join(result.errors)
        assert "b" in joined and "'s'" in joined, joined

    def test_good_schema_passes(self, pipeline):
        result = _lint(pipeline({
            "type": "json_schema",
            "json_schema": {"name": "s", "strict": True, "schema": GOOD_SCHEMA},
        }))
        assert result.valid, result.errors


class TestGating:
    def test_no_response_format_is_untouched(self, pipeline):
        assert _lint(pipeline(None)).valid

    def test_without_strict_it_warns_rather_than_fails(self, pipeline):
        """OpenAI does not enforce the subset unless strict is true."""
        result = _lint(pipeline({
            "type": "json_schema",
            "json_schema": {"name": "s", "schema": BAD_SCHEMA},
        }))
        assert result.valid, result.errors
        assert any("strict" in w for w in result.warnings), result.warnings

    def test_json_object_mode_is_not_schema_checked(self, pipeline):
        """response_format: {type: json_object} carries no schema to check."""
        assert _lint(pipeline({"type": "json_object"})).valid


class TestSchemaFile:
    def test_schema_file_is_loaded_and_checked(self, pipeline, tmp_path):
        (tmp_path / "s.json").write_text(json.dumps(BAD_SCHEMA), encoding="utf-8")
        result = _lint(pipeline({
            "type": "json_schema",
            "json_schema": {"name": "s", "strict": True, "schema_file": "s.json"},
        }))
        assert not result.valid
        assert any("required" in e for e in result.errors), result.errors

    def test_missing_schema_file_is_reported(self, pipeline):
        result = _lint(pipeline({
            "type": "json_schema",
            "json_schema": {"name": "s", "strict": True, "schema_file": "nope.json"},
        }))
        assert not result.valid
        assert any("nope.json" in e for e in result.errors), result.errors


class TestEscapeHatch:
    def test_can_be_switched_off(self, pipeline):
        """A stale rule table must never be able to block real work."""
        result = _lint(pipeline(
            {"type": "json_schema",
             "json_schema": {"name": "s", "strict": True, "schema": BAD_SCHEMA}},
            linter_config={"skip_strict_schema_check": True},
        ))
        assert result.valid, result.errors
