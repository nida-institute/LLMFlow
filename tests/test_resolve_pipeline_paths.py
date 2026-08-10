"""Public API for resolved pipeline paths (LLMFlow#186).

Consumers need a pipeline's resolved directories + variables from outside a run,
with the same precedence and ${...} expansion a real run uses. These tests pin the
contract for the shared `build_run_context` helper and the public
`resolve_pipeline_paths` accessor.
"""
import textwrap
from pathlib import Path

import pytest

from llmflow import resolve_pipeline_paths
from llmflow.utils.context import build_run_context

PIPELINE = textwrap.dedent("""
    name: sample
    intermediate_file_directory: outputs/intermediate
    output_file_directory: ${base}/out
    variables:
      base: outputs
      book_dir: ${output_file_directory}/books
    steps: []
""")


def _write(tmp_path) -> Path:
    p = tmp_path / "sample.yaml"
    p.write_text(PIPELINE, encoding="utf-8")
    return p


# --- build_run_context: the shared merge the runner uses ---

def test_build_run_context_precedence():
    cfg = {
        "intermediate_file_directory": "I",
        "output_file_directory": "O",
        "variables": {"a": "1", "b": "2"},
    }
    ctx = build_run_context(cfg, {"a": "override", "c": "cli"})
    # dir keys seeded as base
    assert ctx["intermediate_file_directory"] == "I"
    assert ctx["output_file_directory"] == "O"
    # variables present
    assert ctx["b"] == "2"
    # --var wins over variables, and adds new keys
    assert ctx["a"] == "override"
    assert ctx["c"] == "cli"


def test_build_run_context_no_vars():
    cfg = {"variables": {"a": "1"}}
    assert build_run_context(cfg) == {"a": "1"}


# --- resolve_pipeline_paths: the public accessor ---

def test_resolve_paths_basic(tmp_path):
    r = resolve_pipeline_paths(_write(tmp_path))
    assert str(r.intermediate_file_directory) == "outputs/intermediate"
    assert str(r.output_file_directory) == "outputs/out"          # ${base} -> outputs
    assert r.variables["book_dir"] == "outputs/out/books"          # derived + transitive


def test_resolve_paths_var_override(tmp_path):
    r = resolve_pipeline_paths(_write(tmp_path), vars={"output_file_directory": "acc/out"})
    assert str(r.output_file_directory) == "acc/out"               # --var wins
    assert r.variables["book_dir"] == "acc/out/books"              # derived picks up override


def test_resolve_paths_missing_dirs(tmp_path):
    p = tmp_path / "bare.yaml"
    p.write_text("name: bare\nsteps: []\n", encoding="utf-8")
    r = resolve_pipeline_paths(p)
    assert r.intermediate_file_directory is None
    assert r.output_file_directory is None
    assert r.variables == {}


# --- sp clean honors --var (resolves its target through the accessor) ---

def test_clean_honors_var(tmp_path, capsys):
    from llmflow.cli import main

    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(
        "name: p\nintermediate_file_directory: canonical/inter\nsteps: []\n",
        encoding="utf-8",
    )
    override = tmp_path / "acc" / "inter"
    override.mkdir(parents=True)
    (override / "x.txt").write_text("x", encoding="utf-8")

    main([
        "clean", "--pipeline", str(pipeline), "--dry-run",
        "--var", f"intermediate_file_directory={override}",
    ])
    out = capsys.readouterr().out
    assert str(override) in out       # clean targeted the --var override...
    assert "canonical" not in out     # ...not the pipeline's declared dir
