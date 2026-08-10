"""Pipeline.resolve() — the resolved view of a pipeline (LLMFlow#187 slice 3).

Supersedes the removed `resolve_pipeline_paths` flat accessor. `build_run_context` (the
shared context builder, still internal) is exercised here too; `sp clean` reaches the same
code via `load_pipeline().resolve()`.
"""
import textwrap
from pathlib import Path

from llmflow import load_pipeline
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


# --- build_run_context: the shared merge the runner and .resolve() both use ---

def test_build_run_context_precedence():
    cfg = {
        "intermediate_file_directory": "I",
        "output_file_directory": "O",
        "variables": {"a": "1", "b": "2"},
    }
    ctx = build_run_context(cfg, {"a": "override", "c": "cli"})
    assert ctx["intermediate_file_directory"] == "I"
    assert ctx["output_file_directory"] == "O"
    assert ctx["b"] == "2"
    assert ctx["a"] == "override"
    assert ctx["c"] == "cli"


def test_build_run_context_no_vars():
    assert build_run_context({"variables": {"a": "1"}}) == {"a": "1"}


# --- Pipeline.resolve() ---

def test_resolve_dirs_and_variables(tmp_path):
    r = load_pipeline(_write(tmp_path)).resolve()
    assert r.intermediate_file_directory == Path("outputs/intermediate")
    assert r.output_file_directory == Path("outputs/out")     # ${base} -> outputs
    assert r.variables["book_dir"] == "outputs/out/books"     # derived + transitive


def test_resolve_var_override(tmp_path):
    r = load_pipeline(_write(tmp_path)).resolve(vars={"output_file_directory": "acc/out"})
    assert r.output_file_directory == Path("acc/out")         # --var wins
    assert r.variables["book_dir"] == "acc/out/books"


def test_resolve_missing_dirs(tmp_path):
    p = tmp_path / "bare.yaml"
    p.write_text("name: bare\nsteps: []\n", encoding="utf-8")
    r = load_pipeline(p).resolve()
    assert r.intermediate_file_directory is None
    assert r.output_file_directory is None
    assert r.variables == {}


def test_resolved_view_is_same_shape(tmp_path):
    r = load_pipeline(_write(tmp_path)).resolve()
    assert r.name == "sample"          # navigable exactly like a Pipeline
    assert r.steps == []


# --- sp clean honors --var (now via load_pipeline().resolve()) ---

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
    assert str(override) in out       # targeted the --var override...
    assert "canonical" not in out     # ...not the pipeline's declared dir
