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
        calls["rewind_to"] = rewind_to
        return "LR"

    monkeypatch.setattr("llmflow.utils.linter.lint_pipeline_full", fake)
    p = _write(tmp_path)
    out = load_pipeline(p).lint(vars={"x": "1"}, rewind_to="chk")
    assert out == "LR"
    assert Path(calls["path"]) == p          # passes the source path through
    assert calls["vars"] == {"x": "1"}
    assert calls["rewind_to"] == "chk"


# --- Pipeline.run() (delegates to run_pipeline) ---

def test_run_delegates(tmp_path, monkeypatch):
    calls = {}

    def fake(pipeline_file, **kwargs):
        calls["pipeline_file"] = pipeline_file
        calls["kwargs"] = kwargs
        return "RAN"

    monkeypatch.setattr("llmflow.runner.run_pipeline", fake)
    p = _write(tmp_path)
    out = load_pipeline(p).run(vars={"x": "1"}, dry_run=True, stop_after="s", log_file="my.log")
    assert out == "RAN"
    assert Path(calls["pipeline_file"]) == p          # passes the source path
    assert calls["kwargs"]["vars"] == {"x": "1"}
    assert calls["kwargs"]["dry_run"] is True
    assert calls["kwargs"]["stop_after"] == "s"
    assert calls["kwargs"]["log_file"] == "my.log"


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


def test_parse_bible_reference_is_lazy_export():
    import llmflow
    from llmflow.utils.data import parse_bible_reference as direct

    assert llmflow.parse_bible_reference is direct


def test_model_metadata_is_lazy_export():
    import llmflow
    from llmflow.modules.telemetry import get_model_metadata as direct

    assert llmflow.model_metadata is direct


# --- Pipeline.schemas() — {step: schema_file} from response_format (config-only, recursive) ---

_SCHEMA_PIPELINE = """\
name: p
steps:
  - name: gen
    type: llm
    response_format:
      type: json_schema
      json_schema:
        schema_file: schemas/scene.json
  - name: plain
    type: llm
  - name: loop
    type: for-each
    for: ${items}
    steps:
      - name: inner
        response_format:
          type: json_schema
          json_schema:
            schema_file: schemas/inner.json
"""


def test_schemas_maps_steps_to_schema_files(tmp_path):
    p = _write(tmp_path, _SCHEMA_PIPELINE)
    assert load_pipeline(p).schemas() == {
        "gen": {"path": "schemas/scene.json", "kind": "response_format"},
        "inner": {"path": "schemas/inner.json", "kind": "response_format"},
    }


# --- api_catalog() — introspection-generated method catalog ---

def test_api_catalog_lists_the_verbs():
    from llmflow import api_catalog

    cat = api_catalog()
    names = {(e["node"], e["name"]) for e in cat}
    assert {
        ("Pipeline", "resolve"), ("Pipeline", "lint"), ("Pipeline", "run"),
        ("Pipeline", "schemas"), ("Pipeline", "saveas"), ("Step", "render_prompt"),
        ("llmflow", "load_pipeline"), ("llmflow", "call_llm"),
        ("llmflow", "parse_bible_reference"), ("llmflow", "model_metadata"),
    } <= names
    resolve = next(e for e in cat if e["node"] == "Pipeline" and e["name"] == "resolve")
    assert "self" not in resolve["signature"]   # self stripped for consumers
    assert resolve["doc"]                        # first docstring line present


# --- Pipeline.schemas() also reads .gpt prompt-frontmatter `schema:` refs ---

def test_schemas_reads_prompt_frontmatter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "gen.gpt").write_text(
        "---\nschema: schemas/scene.json\nrequires:\n  - passage\n---\nBody {{passage}}\n",
        encoding="utf-8",
    )
    p = _write(tmp_path, "name: p\nsteps:\n  - name: gen\n    type: llm\n    prompt: gen.gpt\n")
    assert load_pipeline(p).schemas() == {"gen": {"path": "schemas/scene.json", "kind": "frontmatter"}}


def test_schemas_response_format_takes_precedence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "gen.gpt").write_text("---\nschema: schemas/from_prompt.json\n---\nBody\n", encoding="utf-8")
    body = (
        "name: p\n"
        "steps:\n"
        "  - name: gen\n"
        "    type: llm\n"
        "    prompt: gen.gpt\n"
        "    response_format:\n"
        "      json_schema:\n"
        "        schema_file: schemas/from_rf.json\n"
    )
    assert load_pipeline(_write(tmp_path, body)).schemas() == {
        "gen": {"path": "schemas/from_rf.json", "kind": "response_format"},
    }


def test_schemas_skips_unfindable_prompt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = _write(tmp_path, "name: p\nsteps:\n  - name: gen\n    type: llm\n    prompt: nope.gpt\n")
    assert load_pipeline(p).schemas() == {}


def test_schemas_includes_validator_steps(tmp_path):
    body = (
        "name: p\n"
        "steps:\n"
        "  - name: validate_hierarchy\n"
        "    type: json_schema_validator\n"
        "    inputs:\n"
        "      payload: ${book_hierarchy}\n"
        "      schema_path: schemas/book-hierarchy.schema.json\n"
    )
    assert load_pipeline(_write(tmp_path, body)).schemas() == {
        "validate_hierarchy": {
            "path": "schemas/book-hierarchy.schema.json",
            "kind": "validator",
        },
    }


# --- Pipeline.saveas() — {step: saveas} targets (declared, recursive) ---

def test_saveas_maps_steps_to_targets(tmp_path):
    body = (
        "name: p\n"
        "steps:\n"
        "  - name: gen\n"
        "    type: llm\n"
        "    saveas: ${output_file_directory}/gen.txt\n"
        "  - name: plain\n"
        "    type: llm\n"
        "  - name: loop\n"
        "    type: for-each\n"
        "    for: ${items}\n"
        "    steps:\n"
        "      - name: inner\n"
        "        saveas:\n"
        "          path: ${output_file_directory}/inner.txt\n"
    )
    assert load_pipeline(_write(tmp_path, body)).saveas() == {
        "gen": "${output_file_directory}/gen.txt",
        "inner": {"path": "${output_file_directory}/inner.txt"},
    }
