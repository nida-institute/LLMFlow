"""A run records what it wrote, so a re-run can remove its own output and nothing else (#245).

`/audit-output` reading a directory that holds two runs' files reasons about a mixture. The fix
is not `sp clean` before a run: that deletes every parameterisation's intermediates, which is
#198's bug moved from `debug/` into `intermediate/`, and it breaks `--rewind-to`, which replays
by reading the very files a pre-run clean would remove.

Instead a run records the paths it wrote and deletes only those on a matching re-run.
"""

from __future__ import annotations

import pytest

from llmflow import load_pipeline
from llmflow.utils import file_io

# --------------------------------------------------------------------------------------
# A pipeline whose artifact names come from the run rather than from `--var`.
#
# That is the case #245 is about: same parameters, different filenames, so the previous
# run's files are orphaned rather than overwritten. `next_name` supplies the name, so a
# test decides what each run writes without changing the run key.
# --------------------------------------------------------------------------------------

_NAMES: list[str] = []


def next_name(**_):
    """The name this run's artifacts take. Queued by the test via `_NAMES`."""
    return _NAMES.pop(0) if _NAMES else "unqueued"


PIPELINE = """
name: manifest-test
intermediate_file_directory: work
output_file_directory: final
steps:
  - name: pick
    type: function
    function: tests.test_run_manifest.next_name
    output: name

  - name: write_intermediate
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: "a working note"
    output: note
    saveas: "work/${name}.md"

  - name: write_deliverable
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: "the deliverable"
    output: deliverable
    saveas: "final/${name}.md"
"""


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    """A pipeline file in an empty working directory, with the name queue reset."""
    monkeypatch.chdir(tmp_path)
    _NAMES.clear()
    path = tmp_path / "pipeline.yaml"
    path.write_text(PIPELINE, encoding="utf-8")
    return path


def _run(pipeline, name, **kwargs):
    """Run the pipeline once, with *name* as the name its artifacts take."""
    _NAMES.append(name)
    return load_pipeline(str(pipeline)).run(skip_lint=True, **kwargs)


# --------------------------------------------------------------------------------------
# Rail 2 — the regression that would hurt most, so it is written first.
#
# It passes before the clean exists and must still pass after: `--rewind-to` replays a
# step by reading its `saveas` artifact, which is exactly what a clean would remove.
# --------------------------------------------------------------------------------------


def test_rewind_still_replays_from_the_artifacts_a_clean_would_remove(pipeline):
    """`--rewind-to` reads the previous run's files, so the clean must be skipped entirely.

    `utils/rewind.py` resolves a step's `saveas` path and reads it. A clean at the start of
    the run deletes that file first, and replay then fails with `Saved artifact missing`.
    """
    _run(pipeline, "alpha")
    artifact = pipeline.parent / "work" / "alpha.md"
    assert artifact.exists(), "the first run must leave the artifact rewind replays from"

    context = _run(pipeline, "alpha", rewind_to="write_intermediate")

    assert artifact.exists(), (
        "the rewind run deleted the artifact it was meant to replay from"
    )
    assert context["note"] == artifact.read_text(encoding="utf-8"), (
        "the step was not replayed from its file"
    )


# --------------------------------------------------------------------------------------
# The defect itself
# --------------------------------------------------------------------------------------


def test_a_re_run_removes_the_files_the_previous_run_wrote(pipeline):
    """Same parameters, different artifact names: the orphan is what an audit misreads."""
    _run(pipeline, "first")
    _run(pipeline, "second")

    work = pipeline.parent / "work"
    assert not (work / "first.md").exists(), (
        "the previous run's intermediate survived, so an audit reads two runs as one set"
    )
    assert (work / "second.md").exists(), "this run's own output was deleted"


def test_a_run_with_different_vars_leaves_the_other_run_alone(pipeline):
    """#198's ruling, kept: a Mark run must not delete the Ruth evidence."""
    _run(pipeline, "ruth", vars={"book": "Ruth"})
    _run(pipeline, "mark", vars={"book": "Mark"})

    work = pipeline.parent / "work"
    assert (work / "ruth.md").exists(), "a different parameterisation's files were deleted"
    assert (work / "mark.md").exists()


# --------------------------------------------------------------------------------------
# Rails 1, 3 and 4
# --------------------------------------------------------------------------------------


def test_nothing_outside_the_intermediate_directory_is_removed(pipeline):
    """Rail 1. `separate-output-from-intermediates` holds that clean cannot reach the
    deliverable, and that must stay true once the clean is implicit."""
    _run(pipeline, "first")
    _run(pipeline, "second")

    final = pipeline.parent / "final"
    assert (final / "first.md").exists(), (
        "a deliverable was deleted; clean must never reach outside intermediate_file_directory"
    )


def test_the_run_reports_what_it_deleted(pipeline, caplog):
    """Rail 3. A silent deletion inside a run is how #145 and #198 each went wrong."""
    _run(pipeline, "first")
    # Cleared, or this matches the *first* run's "Wrote file: …/first.md" and can never go
    # red — a guard that passes whatever the engine does, per `check-the-source-not-the-rendering`.
    caplog.clear()
    with caplog.at_level("INFO"):
        _run(pipeline, "second")

    assert "first.md" in caplog.text, "the run deleted a file without saying so"


def test_a_listed_file_already_gone_is_not_an_error(pipeline):
    """Rail 4. The manifest records an intent to have written, not a guarantee it survives."""
    _run(pipeline, "first")
    (pipeline.parent / "work" / "first.md").unlink()

    _run(pipeline, "second")

    assert (pipeline.parent / "work" / "second.md").exists()


def test_a_dry_run_deletes_nothing(pipeline):
    """A dry run calls no model and writes no file, so it must remove none either."""
    _run(pipeline, "first")
    _run(pipeline, "second", dry_run=True)

    assert (pipeline.parent / "work" / "first.md").exists(), (
        "a dry run deleted the previous run's output"
    )


# --------------------------------------------------------------------------------------
# Opting out
# --------------------------------------------------------------------------------------


def test_clean_before_run_false_keeps_the_previous_run(tmp_path, monkeypatch):
    """The pipeline's own opt-out."""
    monkeypatch.chdir(tmp_path)
    _NAMES.clear()
    path = tmp_path / "pipeline.yaml"
    path.write_text(PIPELINE.replace("name: manifest-test", "name: manifest-test\nclean_before_run: false"), encoding="utf-8")

    _run(path, "first")
    _run(path, "second")

    assert (tmp_path / "work" / "first.md").exists(), (
        "clean_before_run: false did not opt out"
    )


def test_no_clean_keeps_the_previous_run(pipeline):
    """The per-invocation override, `--no-clean` on `sp run`."""
    _run(pipeline, "first")
    _run(pipeline, "second", no_clean=True)

    assert (pipeline.parent / "work" / "first.md").exists(), "--no-clean did not opt out"


# --------------------------------------------------------------------------------------
# The declaration
# --------------------------------------------------------------------------------------


def test_the_schema_declares_clean_before_run_as_a_boolean():
    """`pipeline-schema`: a key the engine reads is declared, and a non-boolean is refused.

    Refusal is `PipelineConfig`, which `run_pipeline` validates against before executing
    anything. `yes` and `false` are not tested as strings: YAML reads both as booleans, so the
    value that reaches the engine from a pipeline file is already a `bool`.
    """
    from pydantic import ValidationError

    from llmflow.pipeline_schema import PIPELINE_SCHEMA, PipelineConfig

    declared = PIPELINE_SCHEMA["properties"].get("clean_before_run")
    assert declared == {"type": "boolean"}, "clean_before_run is not declared in the schema"

    assert PipelineConfig(name="x", steps=[], clean_before_run=False).clean_before_run is False
    with pytest.raises(ValidationError):
        PipelineConfig(name="x", steps=[], clean_before_run="sometimes")


def test_the_cli_accepts_no_clean(pipeline):
    """`--no-clean` reaches the runner, which no in-process test exercises.

    Through a subprocess, as `tests/test_resume.py` does for `--resume`: the flag is argparse
    wiring, and wiring is the part an in-process call cannot check.
    """
    import subprocess
    import sys

    # A stepless pipeline: this checks that the flag parses and reaches the runner, and a
    # subprocess started in the temporary directory cannot import the `tests` package that
    # supplies `next_name`.
    stepless = pipeline.parent / "stepless.yaml"
    stepless.write_text("name: cli-flag-test\nsteps: []\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "llmflow.cli", "run",
         "--pipeline", str(stepless), "--no-clean", "--skip-lint"],
        capture_output=True, text=True, cwd=str(pipeline.parent),
    )

    assert result.returncode == 0, result.stderr


def test_the_manifest_is_written_where_the_run_can_find_it_again(pipeline):
    """Keyed by pipeline and run key, and outside the debug tree.

    The debug run directory is emptied by `_clear_debug_dir` at the start of every run, so a
    manifest kept there would be destroyed before the run that needs it could read it.
    """
    _run(pipeline, "first")

    manifest = pipeline.parent / "work" / ".sp-runs" / "pipeline" / "default.json"
    assert manifest.exists(), f"no run manifest at {manifest}"
    assert "first.md" in manifest.read_text(encoding="utf-8")


def test_the_written_file_list_is_emptied_between_runs(tmp_path):
    """Two runs in one process must not share a written-file list.

    The list is what a re-run deletes from, so a stale entry is a file removed that this run
    never wrote. `runner` reset it with `global WRITTEN_FILES; WRITTEN_FILES = []`, which
    rebinds a name in `runner` rather than clearing `file_io`'s list, so nothing was reset:
    under the CLI one run is one process and it never showed, but the Python API and the test
    suite run many.
    """
    file_io.reset_written_files()
    assert file_io.WRITTEN_FILES == []

    first = tmp_path / "first.json"
    first.write_text("{}", encoding="utf-8")
    file_io._record_written_file(str(first))
    assert len(file_io.WRITTEN_FILES) == 1

    file_io.reset_written_files()
    assert file_io.WRITTEN_FILES == [], (
        "a second run starts with the first run's files still listed, so it would delete them"
    )


def test_resetting_keeps_the_same_list_object(tmp_path):
    """Callers hold a reference to the list, so it is cleared in place rather than rebound.

    Rebinding is exactly the defect this replaces: the name changed and every existing
    reference went on pointing at the old list.
    """
    before = file_io.WRITTEN_FILES
    file_io.reset_written_files()
    assert file_io.WRITTEN_FILES is before
