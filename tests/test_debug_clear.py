"""Debug directory lifecycle at the start of a pipeline run.

Originally #145: the runner emptied `outputs/debug/` on every run, so stale files from an
earlier run could not be mistaken for this one's.

**Reversed by #198.** The clear was `shutil.rmtree()` on a directory keyed by pipeline
filename alone, so running the same pipeline for a second passage destroyed the first
passage's requests, replies and run log — reported from Ears to Hear. Deleting the audit
trail is a worse failure than leaving a stale file next to a fresh one, and #145's actual
intent is served better by keeping runs apart: a run distinguished by `--var` now gets its
own subdirectory, so it cannot be polluted by a different run in the first place.

What remains from #145 is the guarantee that the directory exists. Re-running the *same*
key writes over files in place, so a stale file from a previous run of that key can still
linger — accepted deliberately, and the run manifest in #198 will make it unambiguous.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from llmflow.runner import run_pipeline


@pytest.fixture()
def tmp_project(tmp_path, monkeypatch):
    """Minimal pipeline project in a temp directory."""
    monkeypatch.chdir(tmp_path)

    pipeline = tmp_path / "pipeline.yaml"
    pipeline.write_text("name: test\nsteps: []\n")
    return tmp_path


def _run(pipeline_file, **kwargs):
    with (
        patch("llmflow.runner.run_llm_step", return_value="ok"),
        patch("llmflow.runner.run_plugin_step", return_value="ok"),
        patch("llmflow.runner.run_function_step", return_value="ok"),
    ):
        try:
            run_pipeline(str(pipeline_file), **kwargs)
        except SystemExit:
            pass


class TestDebugDirCleared:
    def test_earlier_debug_files_survive_a_run(self, tmp_project):
        """The #198 reversal: a run must not delete what a previous run recorded.

        This asserted the opposite until #198 — that a stale file was removed at run
        start. That clear was an rmtree of the whole directory, which is how a Ruth run's
        evidence disappeared when Mark was run next.
        """
        debug_dir = tmp_project / "outputs" / "debug" / "pipeline"
        debug_dir.mkdir(parents=True)
        earlier = debug_dir / "mark_1_old_request.txt"
        earlier.write_text("recorded by an earlier run")

        _run(tmp_project / "pipeline.yaml")

        assert earlier.exists(), "a previous run's debug output was destroyed"
        assert earlier.read_text() == "recorded by an earlier run"

    def test_runs_with_different_vars_are_kept_apart(self, tmp_project):
        """#145's intent — no confusion between runs — now achieved by separation."""
        _run(tmp_project / "pipeline.yaml", vars={"book": "Ruth"})
        _run(tmp_project / "pipeline.yaml", vars={"book": "Mark"})

        base = tmp_project / "outputs" / "debug" / "pipeline"
        assert (base / "book-Ruth").is_dir(), sorted(p.name for p in base.iterdir())
        assert (base / "book-Mark").is_dir(), sorted(p.name for p in base.iterdir())

    def test_debug_dir_recreated_after_clear(self, tmp_project):
        debug_dir = tmp_project / "outputs" / "debug" / "pipeline"
        debug_dir.mkdir(parents=True)
        (debug_dir / "old.txt").write_text("old")

        _run(tmp_project / "pipeline.yaml")

        assert debug_dir.exists(), "outputs/debug/pipeline/ should exist after clear"

    def test_no_debug_dir_is_fine(self, tmp_project):
        """First run with no pre-existing debug dir should not raise."""
        assert not (tmp_project / "outputs" / "debug").exists()
        _run(tmp_project / "pipeline.yaml")

    def test_dry_run_does_not_touch_debug(self, tmp_project):
        debug_dir = tmp_project / "outputs" / "debug" / "pipeline"
        debug_dir.mkdir(parents=True)
        keep = debug_dir / "keep_me.txt"
        keep.write_text("keep")

        _run(tmp_project / "pipeline.yaml", dry_run=True)

        assert keep.exists(), "dry_run should not touch debug files"
