"""Tests for sp clean command and intermediate_file_directory / output_file_directory.

GH #157 — sp clean command and pipeline directory declaration.
"""

import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from llmflow.runner import run_pipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "llmflow.cli", *args],
        capture_output=True,
        text=True,
    )


def _run_pipeline(pipeline_file, **kwargs):
    with (
        patch("llmflow.runner.run_llm_step", return_value="ok"),
        patch("llmflow.runner.run_plugin_step", return_value="ok"),
        patch("llmflow.runner.run_function_step", return_value="ok"),
    ):
        run_pipeline(str(pipeline_file), **kwargs)


def _write_pipeline(tmp_path, body: str) -> Path:
    p = tmp_path / "pipeline.yaml"
    p.write_text(body)
    return p


# ---------------------------------------------------------------------------
# sp clean — basic behavior
# ---------------------------------------------------------------------------

class TestCleanCommand:

    def test_clean_deletes_contents_of_intermediate_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        work = tmp_path / "work"
        work.mkdir()
        (work / "extracted.json").write_text('{"a": 1}')
        (work / "draft.md").write_text("# Draft")

        pipeline = _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{work}"
output_file_directory: "{tmp_path / 'output'}"
steps: []
""")
        result = _run_cli("clean", "--pipeline", str(pipeline))

        assert result.returncode == 0
        assert not (work / "extracted.json").exists()
        assert not (work / "draft.md").exists()

    def test_clean_leaves_intermediate_dir_itself(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        work = tmp_path / "work"
        work.mkdir()
        (work / "file.txt").write_text("content")

        pipeline = _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{work}"
output_file_directory: "{tmp_path / 'output'}"
steps: []
""")
        _run_cli("clean", "--pipeline", str(pipeline))

        assert work.exists(), "intermediate_file_directory itself should not be deleted"

    def test_clean_does_not_touch_output_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        work = tmp_path / "work"
        work.mkdir()
        output = tmp_path / "output"
        output.mkdir()
        (work / "intermediate.json").write_text("{}")
        final = output / "final.md"
        final.write_text("# Final")

        pipeline = _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{work}"
output_file_directory: "{output}"
steps: []
""")
        _run_cli("clean", "--pipeline", str(pipeline))

        assert final.exists(), "output_file_directory contents must not be deleted"

    def test_clean_warns_and_exits_cleanly_when_no_intermediate_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline = _write_pipeline(tmp_path, f"""
name: test
output_file_directory: "{tmp_path / 'output'}"
steps: []
""")
        result = _run_cli("clean", "--pipeline", str(pipeline))

        assert result.returncode == 0
        assert "intermediate_file_directory" in result.stdout + result.stderr

    def test_clean_resolves_variable_references(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        work = tmp_path / "work"
        work.mkdir()
        (work / "file.txt").write_text("content")

        pipeline = _write_pipeline(tmp_path, f"""
name: test
variables:
  work_root: "{work}"
intermediate_file_directory: "${{work_root}}"
output_file_directory: "{tmp_path / 'output'}"
steps: []
""")
        result = _run_cli("clean", "--pipeline", str(pipeline))

        assert result.returncode == 0
        assert not (work / "file.txt").exists()

    def test_clean_nonexistent_intermediate_dir_warns_does_not_fail(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline = _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{tmp_path / 'nonexistent'}"
output_file_directory: "{tmp_path / 'output'}"
steps: []
""")
        result = _run_cli("clean", "--pipeline", str(pipeline))

        assert result.returncode == 0


# ---------------------------------------------------------------------------
# sp clean --dry-run
# ---------------------------------------------------------------------------

class TestCleanDryRun:

    def test_dry_run_does_not_delete_files(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        work = tmp_path / "work"
        work.mkdir()
        f = work / "file.txt"
        f.write_text("keep me")

        pipeline = _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{work}"
output_file_directory: "{tmp_path / 'output'}"
steps: []
""")
        result = _run_cli("clean", "--pipeline", str(pipeline), "--dry-run")

        assert result.returncode == 0
        assert f.exists(), "--dry-run must not delete files"

    def test_dry_run_reports_files_that_would_be_deleted(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        work = tmp_path / "work"
        work.mkdir()
        (work / "extracted.json").write_text("{}")

        pipeline = _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{work}"
output_file_directory: "{tmp_path / 'output'}"
steps: []
""")
        result = _run_cli("clean", "--pipeline", str(pipeline), "--dry-run")

        assert "extracted.json" in result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Debug file routing
# ---------------------------------------------------------------------------

class TestDebugFileRouting:

    def test_debug_files_routed_to_intermediate_dir_when_declared(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        work = tmp_path / "work"

        pipeline = _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{work}"
output_file_directory: "{tmp_path / 'output'}"
linter_config:
  log_level: debug
steps:
  - name: step1
    type: llm
    prompt:
      file: dummy.gpt
      inputs: {{}}
    output: result
""")
        _run_pipeline(pipeline, skip_lint=True)

        debug_dir = work / "debug" / "pipeline"
        assert debug_dir.exists(), "debug files should go to intermediate_file_directory/debug/{pipeline-name}/"

    def test_debug_files_fall_back_to_outputs_debug_when_no_intermediate_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        pipeline = _write_pipeline(tmp_path, f"""
name: test
output_file_directory: "{tmp_path / 'output'}"
linter_config:
  log_level: debug
steps:
  - name: step1
    type: llm
    prompt:
      file: dummy.gpt
      inputs: {{}}
    output: result
""")
        _run_pipeline(pipeline, skip_lint=True)

        fallback = tmp_path / "outputs" / "debug" / "pipeline"
        assert fallback.exists(), "should fall back to outputs/debug/{pipeline-name}/ when no intermediate_file_directory"

    def test_log_file_routed_to_debug_dir_when_intermediate_declared(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        work = tmp_path / "work"

        pipeline = _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{work}"
output_file_directory: "{tmp_path / 'output'}"
linter_config:
  log_level: debug
steps: []
""")
        _run_pipeline(pipeline, skip_lint=True)

        # The run-key segment ("default" for a run with no --var) is always present, so the
        # start-of-run clear can only ever empty one run's directory (LLMFlow#198).
        log_file = work / "debug" / "pipeline" / "default" / "llmflow.log"
        assert log_file.exists(), (
            "llmflow.log should be written to debug/{pipeline-name}/{run-key}/"
        )


# ---------------------------------------------------------------------------
# Linter warnings
# ---------------------------------------------------------------------------

class TestLinterWarnings:

    def test_linter_warns_saveas_outside_declared_dirs(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline = _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{tmp_path / 'work'}"
output_file_directory: "{tmp_path / 'output'}"
steps:
  - name: step1
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: "hello"
    output: result
    saveas: "{tmp_path / 'elsewhere' / 'file.txt'}"
""")
        result = _run_cli("lint", "--pipeline", str(pipeline))

        combined = result.stdout + result.stderr
        assert "intermediate_file_directory" in combined or "output_file_directory" in combined, \
            "linter should warn when saveas falls outside declared directories"

    def test_linter_does_not_warn_saveas_inside_intermediate_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline = _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{tmp_path / 'work'}"
output_file_directory: "{tmp_path / 'output'}"
steps:
  - name: step1
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: "hello"
    output: result
    saveas: "{tmp_path / 'work' / 'file.txt'}"
""")
        result = _run_cli("lint", "--pipeline", str(pipeline))

        assert result.returncode == 0

    def test_linter_does_not_warn_saveas_inside_output_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline = _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{tmp_path / 'work'}"
output_file_directory: "{tmp_path / 'output'}"
steps:
  - name: step1
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: "hello"
    output: result
    saveas: "{tmp_path / 'output' / 'final.md'}"
""")
        result = _run_cli("lint", "--pipeline", str(pipeline))

        assert result.returncode == 0

    def test_linter_no_warning_when_no_dirs_declared(self, tmp_path, monkeypatch):
        """Pipelines without declared dirs are still valid — no warning."""
        monkeypatch.chdir(tmp_path)
        pipeline = _write_pipeline(tmp_path, f"""
name: test
steps:
  - name: step1
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: "hello"
    output: result
    saveas: "{tmp_path / 'anywhere' / 'file.txt'}"
""")
        result = _run_cli("lint", "--pipeline", str(pipeline))

        assert result.returncode == 0


# ---------------------------------------------------------------------------
# sp clean --debug-only
# ---------------------------------------------------------------------------

class TestCleanDebugOnly:

    def _pipeline_with_work(self, tmp_path):
        work = tmp_path / "work"
        work.mkdir()
        debug = work / "debug" / "pipeline"
        debug.mkdir(parents=True)
        (debug / "req.txt").write_text("request")
        (work / "intermediate.json").write_text("{}")
        return _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{work}"
output_file_directory: "{tmp_path / 'output'}"
steps: []
"""), work, debug

    def test_debug_only_deletes_debug_subdir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline, work, debug = self._pipeline_with_work(tmp_path)

        result = _run_cli("clean", "--pipeline", str(pipeline), "--debug-only")

        assert result.returncode == 0
        assert not (debug / "req.txt").exists()

    def test_debug_only_preserves_intermediate_files(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline, work, debug = self._pipeline_with_work(tmp_path)

        _run_cli("clean", "--pipeline", str(pipeline), "--debug-only")

        assert (work / "intermediate.json").exists()

    def test_debug_only_fallback_to_outputs_debug_when_no_intermediate_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        fallback = tmp_path / "outputs" / "debug" / "pipeline"
        fallback.mkdir(parents=True)
        (fallback / "old.txt").write_text("stale")

        pipeline = _write_pipeline(tmp_path, f"""
name: test
output_file_directory: "{tmp_path / 'output'}"
steps: []
""")
        result = _run_cli("clean", "--pipeline", str(pipeline), "--debug-only")

        assert result.returncode == 0
        assert not (fallback / "old.txt").exists()

    def test_debug_only_dry_run_does_not_delete(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline, work, debug = self._pipeline_with_work(tmp_path)
        req = debug / "req.txt"

        _run_cli("clean", "--pipeline", str(pipeline), "--debug-only", "--dry-run")

        assert req.exists()


# ---------------------------------------------------------------------------
# sp clean --intermediate-only
# ---------------------------------------------------------------------------

class TestCleanIntermediateOnly:

    def _pipeline_with_work(self, tmp_path):
        work = tmp_path / "work"
        work.mkdir()
        debug = work / "debug" / "pipeline"
        debug.mkdir(parents=True)
        (debug / "req.txt").write_text("request")
        (work / "intermediate.json").write_text("{}")
        return _write_pipeline(tmp_path, f"""
name: test
intermediate_file_directory: "{work}"
output_file_directory: "{tmp_path / 'output'}"
steps: []
"""), work, debug

    def test_intermediate_only_deletes_non_debug_files(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline, work, debug = self._pipeline_with_work(tmp_path)

        result = _run_cli("clean", "--pipeline", str(pipeline), "--intermediate-only")

        assert result.returncode == 0
        assert not (work / "intermediate.json").exists()

    def test_intermediate_only_preserves_debug_subdir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline, work, debug = self._pipeline_with_work(tmp_path)

        _run_cli("clean", "--pipeline", str(pipeline), "--intermediate-only")

        assert (debug / "req.txt").exists()

    def test_intermediate_only_dry_run_does_not_delete(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline, work, debug = self._pipeline_with_work(tmp_path)
        f = work / "intermediate.json"

        _run_cli("clean", "--pipeline", str(pipeline), "--intermediate-only", "--dry-run")

        assert f.exists()

    def test_intermediate_only_warns_when_no_intermediate_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline = _write_pipeline(tmp_path, f"""
name: test
output_file_directory: "{tmp_path / 'output'}"
steps: []
""")
        result = _run_cli("clean", "--pipeline", str(pipeline), "--intermediate-only")

        assert result.returncode == 0
        assert "intermediate_file_directory" in result.stdout + result.stderr
