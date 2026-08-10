"""Slice 4 of the public API (LLMFlow#187): Pipeline facade methods.

These are thin delegations to the engine's existing single-implementation functions
(no reimplementation) — verified here by delegation-wiring tests plus a real lint.
"""
import textwrap
from pathlib import Path

import pytest

from llmflow import Pipeline, load_pipeline


def _write(tmp_path, body="name: p\nsteps: []\n") -> Path:
    p = tmp_path / "p.yaml"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


# --- Pipeline.lint() -> LintResult (delegates to lint_pipeline_full) ---

def test_lint_returns_lintresult(tmp_path):
    result = load_pipeline(_write(tmp_path)).lint()
    assert hasattr(result, "valid")
    assert hasattr(result, "errors")
    assert hasattr(result, "warnings")


def test_lint_requires_source():
    # A Pipeline built from a dict (no source file) cannot lint.
    with pytest.raises(ValueError):
        Pipeline({"name": "p", "steps": []}).lint()


def test_lint_delegates_with_source_and_vars(tmp_path, monkeypatch):
    calls = {}

    def fake(pipeline_path, *, vars=None, rewind_to=None):
        calls["path"] = pipeline_path
        calls["vars"] = vars
        return "LR"

    monkeypatch.setattr("llmflow.utils.linter.lint_pipeline_full", fake)
    p = _write(tmp_path)
    out = load_pipeline(p).lint(vars={"x": "1"})
    assert out == "LR"
    assert Path(calls["path"]) == p          # passes the source path through
    assert calls["vars"] == {"x": "1"}


# --- Pipeline.run() (delegates to run_pipeline) ---

def test_run_delegates(tmp_path, monkeypatch):
    calls = {}

    def fake(pipeline_file, **kwargs):
        calls["pipeline_file"] = pipeline_file
        calls["kwargs"] = kwargs
        return "RAN"

    monkeypatch.setattr("llmflow.runner.run_pipeline", fake)
    p = _write(tmp_path)
    out = load_pipeline(p).run(vars={"x": "1"}, dry_run=True, stop_after="s")
    assert out == "RAN"
    assert Path(calls["pipeline_file"]) == p          # passes the source path
    assert calls["kwargs"]["vars"] == {"x": "1"}
    assert calls["kwargs"]["dry_run"] is True
    assert calls["kwargs"]["stop_after"] == "s"


# --- Step.render_prompt() (delegates to steps.llm.render_prompt) ---

def test_render_prompt_delegates(monkeypatch):
    from llmflow import Step

    calls = {}

    def fake(prompt_config, context):
        calls["prompt"] = prompt_config
        calls["context"] = context
        return "RENDERED"

    monkeypatch.setattr("llmflow.steps.llm.render_prompt", fake)
    out = Step({"name": "s", "prompt": "greet.gpt"}).render_prompt({"name": "World"})
    assert out == "RENDERED"
    assert calls["prompt"] == "greet.gpt"
    assert calls["context"] == {"name": "World"}


def test_render_prompt_requires_prompt():
    from llmflow import Step

    with pytest.raises(ValueError):
        Step({"name": "s"}).render_prompt({})


# --- call_llm: lazy top-level export (#175) ---

def test_call_llm_is_lazy_export():
    import llmflow
    from llmflow.utils.llm_runner import call_llm as direct

    assert llmflow.call_llm is direct
