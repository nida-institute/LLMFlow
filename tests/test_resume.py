"""Tests for GH #166: sp run --resume skips steps whose saveas files already exist.

Design:
  - Steps with saveas whose file exists are skipped; file content loaded into context
  - Steps without saveas always run
  - Without --resume, steps always run regardless of existing saveas files
  - For-each: each iteration is evaluated independently at the step level
  - Skipped step output is available in context for downstream steps
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from llmflow.runner import run_pipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_pipeline(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "pipeline.yaml"
    p.write_text(body)
    return p


def _write_prompt(tmp_path: Path, name: str = "test.gpt") -> Path:
    p = tmp_path / "prompts" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\nprompt:\n  requires:\n    - text\n---\nDefine: {{text}}\n")
    return p


def _run(pipeline_file, *, resume=False, vars=None, **kwargs):
    """Run pipeline with mocked LLM/plugin/function steps. Returns the llm mock."""
    llm_mock = MagicMock(return_value="llm output")
    fn_mock = MagicMock(return_value="fn output")
    with (
        patch("llmflow.runner.run_llm_step", llm_mock),
        patch("llmflow.runner.run_plugin_step", MagicMock(return_value="plugin output")),
        patch("llmflow.runner.run_function_step", fn_mock),
    ):
        run_pipeline(str(pipeline_file), skip_lint=True, resume=resume, vars=vars, **kwargs)
    return llm_mock, fn_mock


# ---------------------------------------------------------------------------
# Single step — basic resume behavior
# ---------------------------------------------------------------------------

class TestResumeSingleStep:

    def test_skips_llm_step_when_saveas_file_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        out = tmp_path / "output" / "result.md"
        out.parent.mkdir(parents=True)
        out.write_text("saved content")

        pipeline = _write_pipeline(tmp_path, f"""
name: test
steps:
  - name: gen
    type: llm
    prompt:
      file: test.gpt
      inputs:
        text: "hello"
    output: result
    saveas: output/result.md
""")
        llm_mock, _ = _run(pipeline, resume=True)
        assert llm_mock.call_count == 0

    def test_runs_llm_step_when_saveas_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        pipeline = _write_pipeline(tmp_path, f"""
name: test
steps:
  - name: gen
    type: llm
    prompt:
      file: test.gpt
      inputs:
        text: "hello"
    output: result
    saveas: output/result.md
""")
        llm_mock, _ = _run(pipeline, resume=True)
        assert llm_mock.call_count == 1

    def test_step_without_saveas_always_runs(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        pipeline = _write_pipeline(tmp_path, """
name: test
steps:
  - name: gen
    type: llm
    prompt:
      file: test.gpt
      inputs:
        text: "hello"
    output: result
""")
        llm_mock, _ = _run(pipeline, resume=True)
        assert llm_mock.call_count == 1

    def test_without_resume_runs_even_if_saveas_file_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        out = tmp_path / "output" / "result.md"
        out.parent.mkdir(parents=True)
        out.write_text("saved content")

        pipeline = _write_pipeline(tmp_path, f"""
name: test
steps:
  - name: gen
    type: llm
    prompt:
      file: test.gpt
      inputs:
        text: "hello"
    output: result
    saveas: output/result.md
""")
        llm_mock, _ = _run(pipeline, resume=False)
        assert llm_mock.call_count == 1

    def test_skipped_step_loads_file_content_into_context(self, tmp_path, monkeypatch):
        """Downstream step must see the saved content as the skipped step's output."""
        monkeypatch.chdir(tmp_path)
        out = tmp_path / "output" / "result.md"
        out.parent.mkdir(parents=True)
        out.write_text("the saved definition")

        # Second step is a function that receives ${result}
        pipeline = _write_pipeline(tmp_path, f"""
name: test
steps:
  - name: gen
    type: llm
    prompt:
      file: test.gpt
      inputs:
        text: "hello"
    output: result
    saveas: output/result.md

  - name: use_result
    type: function
    function: llmflow.utils.io.write_markdown
    inputs:
      path: output/final.md
      content: "${{result}}"
""")
        _, fn_mock = _run(pipeline, resume=True)

        # run_function_step is called as (step, context, pipeline_config)
        # verify the context passed to it has the saved content
        assert fn_mock.call_count == 1
        call_context = fn_mock.call_args[0][1]  # second positional arg is context
        assert call_context.get("result") == "the saved definition"

    def test_resume_with_variable_saveas_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        out = tmp_path / "output" / "result.md"
        out.parent.mkdir(parents=True)
        out.write_text("saved")

        pipeline = _write_pipeline(tmp_path, f"""
name: test
variables:
  output_dir: output
steps:
  - name: gen
    type: llm
    prompt:
      file: test.gpt
      inputs:
        text: "hello"
    output: result
    saveas: "${{output_dir}}/result.md"
""")
        llm_mock, _ = _run(pipeline, resume=True)
        assert llm_mock.call_count == 0


# ---------------------------------------------------------------------------
# For-each loops
# ---------------------------------------------------------------------------

class TestResumeForEach:

    def _for_each_pipeline(self, tmp_path, items):
        return _write_pipeline(tmp_path, """
name: test
variables:
  output_dir: output
steps:
  - name: loop
    type: for-each
    in: "${items}"
    for: concept
    steps:
      - name: define
        type: llm
        prompt:
          file: test.gpt
          inputs:
            text: "${concept}"
        output: definition
        saveas: "${output_dir}/${concept}.md"
"""), items

    def test_skips_iterations_where_saveas_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        out = tmp_path / "output"
        out.mkdir()
        (out / "a.md").write_text("done")
        (out / "b.md").write_text("done")
        # "c" is not done

        pipeline, items = self._for_each_pipeline(tmp_path, ["a", "b", "c"])
        llm_mock, _ = _run(pipeline, resume=True, vars={"items": items})
        assert llm_mock.call_count == 1

    def test_runs_all_iterations_when_no_saveas_files_exist(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        pipeline, items = self._for_each_pipeline(tmp_path, ["a", "b", "c"])
        llm_mock, _ = _run(pipeline, resume=True, vars={"items": items})
        assert llm_mock.call_count == 3

    def test_skips_all_iterations_when_all_saveas_files_exist(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        out = tmp_path / "output"
        out.mkdir()
        for name in ["a", "b", "c"]:
            (out / f"{name}.md").write_text("done")

        pipeline, items = self._for_each_pipeline(tmp_path, ["a", "b", "c"])
        llm_mock, _ = _run(pipeline, resume=True, vars={"items": items})
        assert llm_mock.call_count == 0

    def test_without_resume_runs_all_iterations_regardless(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        out = tmp_path / "output"
        out.mkdir()
        (out / "a.md").write_text("done")
        (out / "b.md").write_text("done")

        pipeline, items = self._for_each_pipeline(tmp_path, ["a", "b", "c"])
        llm_mock, _ = _run(pipeline, resume=False, vars={"items": items})
        assert llm_mock.call_count == 3

    def test_multi_step_iteration_partial_saveas(self, tmp_path, monkeypatch):
        """If the first sub-step is done but the second isn't, only the first is skipped."""
        monkeypatch.chdir(tmp_path)
        out = tmp_path / "output"
        out.mkdir()
        (out / "a.md").write_text("full definition")
        # a_short.md does NOT exist

        pipeline = _write_pipeline(tmp_path, """
name: test
variables:
  output_dir: output
steps:
  - name: loop
    type: for-each
    in: "${items}"
    for: concept
    steps:
      - name: define
        type: llm
        prompt:
          file: test.gpt
          inputs:
            text: "${concept}"
        output: definition
        saveas: "${output_dir}/${concept}.md"

      - name: shorten
        type: llm
        prompt:
          file: test.gpt
          inputs:
            text: "${definition}"
        output: short_definition
        saveas: "${output_dir}/${concept}_short.md"
""")
        llm_mock, _ = _run(pipeline, resume=True, vars={"items": ["a"]})
        # define is skipped (file exists), shorten runs (file missing)
        assert llm_mock.call_count == 1

    def test_multi_step_iteration_loads_first_output_for_second_step(self, tmp_path, monkeypatch):
        """When the first sub-step is skipped, its saved content must be available
        to the second sub-step as ${definition}."""
        monkeypatch.chdir(tmp_path)
        out = tmp_path / "output"
        out.mkdir()
        (out / "a.md").write_text("the full definition from disk")

        captured_contexts = {}

        def capture_llm(step, context, pipeline_config):
            captured_contexts[step["name"]] = dict(context)
            return "short output"

        pipeline = _write_pipeline(tmp_path, """
name: test
variables:
  output_dir: output
steps:
  - name: loop
    type: for-each
    in: "${items}"
    for: concept
    steps:
      - name: define
        type: llm
        prompt:
          file: test.gpt
          inputs:
            text: "${concept}"
        output: definition
        saveas: "${output_dir}/${concept}.md"

      - name: shorten
        type: llm
        prompt:
          file: test.gpt
          inputs:
            text: "${definition}"
        output: short_definition
        saveas: "${output_dir}/${concept}_short.md"
""")
        with patch("llmflow.runner.run_llm_step", side_effect=capture_llm):
            run_pipeline(str(pipeline), skip_lint=True, resume=True, vars={"items": ["a"]})

        assert "shorten" in captured_contexts
        assert captured_contexts["shorten"].get("definition") == "the full definition from disk"


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

class TestResumeCLI:

    def test_cli_resume_flag_accepted(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline = _write_pipeline(tmp_path, """
name: test
steps: []
""")
        result = subprocess.run(
            [sys.executable, "-m", "llmflow.cli", "run",
             "--pipeline", str(pipeline), "--resume", "--skip-lint"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr

    def test_cli_resume_flag_missing_does_not_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline = _write_pipeline(tmp_path, """
name: test
steps: []
""")
        result = subprocess.run(
            [sys.executable, "-m", "llmflow.cli", "run",
             "--pipeline", str(pipeline), "--skip-lint"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
