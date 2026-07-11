"""Tests for #145: runner clears outputs/debug/ at the start of every pipeline run."""

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
    def test_stale_debug_files_removed_on_run(self, tmp_project):
        debug_dir = tmp_project / "outputs" / "debug" / "pipeline"
        debug_dir.mkdir(parents=True)
        stale = debug_dir / "mark_1_old_request.txt"
        stale.write_text("stale content")

        _run(tmp_project / "pipeline.yaml")

        assert not stale.exists(), "stale debug file should be removed at run start"

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

    def test_dry_run_does_not_clear_debug(self, tmp_project):
        debug_dir = tmp_project / "outputs" / "debug" / "pipeline"
        debug_dir.mkdir(parents=True)
        stale = debug_dir / "keep_me.txt"
        stale.write_text("keep")

        _run(tmp_project / "pipeline.yaml", dry_run=True)

        assert stale.exists(), "dry_run should not clear debug files"
