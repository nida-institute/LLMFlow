"""Tests for pipeline rewind behavior using saved artifacts."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from llmflow.runner import run_pipeline
from llmflow.utils.linter import lint_pipeline_full
from llmflow.utils.rewind import StepRewindManager


@pytest.fixture
def rewind_pipeline(tmp_path):
    """Create a simple two-step pipeline with saveas output."""
    output_path = tmp_path / "outputs" / "first.txt"
    pipeline_content = {
        "name": "rewind-pipeline",
        "variables": {"output_path": str(output_path)},
        "llm_config": {"model": "gpt-4o", "temperature": 0.1},
        "steps": [
            {
                "name": "save_step",
                "type": "function",
                "function": "tests.test_helpers.save_text",
                "inputs": {"path": "${output_path}", "content": "snapshot"},
                "outputs": "saved_content",
                "saveas": "${output_path}",
            },
            {
                "name": "second_step",
                "type": "function",
                "function": "tests.test_helpers.mock_function",
                "inputs": {"a": "${saved_content}", "p": "done"},
                "outputs": "final_value",
            },
        ],
    }
    pipeline_path = tmp_path / "rewind_pipeline.yaml"
    pipeline_path.write_text(yaml.safe_dump(pipeline_content), encoding="utf-8")

    return {
        "pipeline_path": str(pipeline_path),
        "output_path": output_path,
    }


@pytest.fixture
def dynamic_path_pipeline(tmp_path):
    """Pipeline that mirrors the real-world pattern:
    Step 1: cheap function, no saveas — computes a prefix dict (like parse_bible_reference)
    Step 2: llm-like function, saveas uses ${prefix_info.prefix} — the dynamic path
    Step 3: downstream consumer

    The saveas path in step 2 can only be resolved after step 1 has executed.
    """
    output_dir = tmp_path / "outputs"
    pipeline_content = {
        "name": "dynamic-path-pipeline",
        "variables": {"name": "mark_11"},
        "llm_config": {"model": "gpt-4o", "temperature": 0.1},
        "steps": [
            {
                "name": "parse_ref",
                "type": "function",
                "function": "tests.test_helpers.make_prefix",
                "inputs": {"name": "${name}"},
                "outputs": "prefix_info",
                # No saveas — just a cheap setup step
            },
            {
                "name": "heavy_step",
                "type": "function",
                "function": "tests.test_helpers.save_text",
                "inputs": {
                    "path": str(output_dir / "${prefix_info.prefix}_result.txt"),
                    "content": "heavy result",
                },
                "outputs": "heavy_content",
                "saveas": str(output_dir / "${prefix_info.prefix}_result.txt"),
            },
            {
                "name": "final_step",
                "type": "function",
                "function": "tests.test_helpers.mock_function",
                "inputs": {"a": "${heavy_content}", "p": "done"},
                "outputs": "final_value",
            },
        ],
    }
    pipeline_path = tmp_path / "dynamic_pipeline.yaml"
    pipeline_path.write_text(yaml.safe_dump(pipeline_content), encoding="utf-8")

    return {
        "pipeline_path": str(pipeline_path),
        "output_dir": output_dir,
        "artifact_path": output_dir / "mark_11_result.txt",
    }


# ---------------------------------------------------------------------------
# Unit tests for StepRewindManager
# ---------------------------------------------------------------------------

class TestStepRewindManagerUnit:
    def test_should_replay_returns_false_for_step_without_saveas(self):
        manager = StepRewindManager(rewind_to="target_step")
        step_no_saveas = {"name": "setup_step", "type": "function"}
        assert manager.should_replay("setup_step", step=step_no_saveas) is False

    def test_should_replay_returns_true_for_step_with_saveas(self):
        manager = StepRewindManager(rewind_to="target_step")
        step_with_saveas = {"name": "target_step", "type": "function", "saveas": "out.json"}
        assert manager.should_replay("target_step", step=step_with_saveas) is True

    def test_should_replay_returns_false_when_no_rewind_to(self):
        manager = StepRewindManager(rewind_to=None)
        step = {"name": "any_step", "saveas": "out.json"}
        assert manager.should_replay("any_step", step=step) is False

    def test_should_replay_returns_false_after_rewind_complete(self):
        manager = StepRewindManager(rewind_to="target_step")
        manager._rewind_complete = True
        step = {"name": "later_step", "saveas": "out.json"}
        assert manager.should_replay("later_step", step=step) is False

    def test_in_rewind_phase_true_before_target(self):
        manager = StepRewindManager(rewind_to="target_step")
        assert manager.in_rewind_phase is True

    def test_in_rewind_phase_false_when_no_rewind_to(self):
        manager = StepRewindManager(rewind_to=None)
        assert manager.in_rewind_phase is False

    def test_in_rewind_phase_false_after_complete(self):
        manager = StepRewindManager(rewind_to="target_step")
        manager._rewind_complete = True
        assert manager.in_rewind_phase is False

    def test_mark_target_reached_completes_rewind(self):
        manager = StepRewindManager(rewind_to="target_step")
        assert manager.in_rewind_phase is True
        manager.mark_target_reached("target_step")
        assert manager.in_rewind_phase is False
        assert manager._rewind_complete is True

    def test_mark_target_reached_ignores_other_steps(self):
        manager = StepRewindManager(rewind_to="target_step")
        manager.mark_target_reached("some_other_step")
        assert manager.in_rewind_phase is True


# ---------------------------------------------------------------------------
# Integration tests: execution
# ---------------------------------------------------------------------------

class TestRewindExecution:
    def test_saved_artifact_reused_on_rewind(self, rewind_pipeline):
        # First run writes the saveas artifact
        result = run_pipeline(
            rewind_pipeline["pipeline_path"],
            skip_lint=True,
        )
        assert result["final_value"] == "snapshot_done"
        assert rewind_pipeline["output_path"].exists(), "saveas artifact should exist"

        # Second run rewinds first step, so save_text must not be called
        with patch("tests.test_helpers.save_text", side_effect=AssertionError("should not run")):
            result = run_pipeline(
                rewind_pipeline["pipeline_path"],
                skip_lint=True,
                rewind_to="save_step",
            )
        assert result["final_value"] == "snapshot_done"

    def test_stop_after_prevents_following_steps(self, rewind_pipeline):
        with patch("tests.test_helpers.mock_function", side_effect=AssertionError("should not run")):
            result = run_pipeline(
                rewind_pipeline["pipeline_path"],
                skip_lint=True,
                stop_after="save_step",
            )
        assert "final_value" not in result

    def test_rewind_reruns_function_steps_without_saveas(self, dynamic_path_pipeline):
        """Steps with no saveas are re-executed during rewind to populate context,
        then the saveas step is replayed from its artifact."""
        # First run: writes the artifact
        result = run_pipeline(dynamic_path_pipeline["pipeline_path"], skip_lint=True)
        assert result["final_value"] == "heavy result_done"
        assert dynamic_path_pipeline["artifact_path"].exists()

        # Second run with rewind_to=heavy_step:
        # - parse_ref (no saveas) should RE-EXECUTE to populate prefix_info
        # - heavy_step (has saveas) should be REPLAYED from its artifact
        # - final_step should run normally
        with patch("tests.test_helpers.save_text", side_effect=AssertionError("heavy_step should not execute")):
            result = run_pipeline(
                dynamic_path_pipeline["pipeline_path"],
                skip_lint=True,
                rewind_to="heavy_step",
            )
        assert result["final_value"] == "heavy result_done"

    def test_rewind_to_no_saveas_step_executes_and_completes_phase(self, dynamic_path_pipeline):
        """When rewind_to targets a step with no saveas, that step re-executes and
        rewind is marked complete so subsequent steps also run normally."""
        # Rewind to parse_ref (no saveas) — it should execute, then heavy_step and
        # final_step should also run normally (not attempt to replay).
        result = run_pipeline(
            dynamic_path_pipeline["pipeline_path"],
            skip_lint=True,
            rewind_to="parse_ref",
        )
        assert result["final_value"] == "heavy result_done"


# ---------------------------------------------------------------------------
# Integration tests: linting
# ---------------------------------------------------------------------------

class TestRewindLinting:
    def test_lint_requires_saved_artifact(self, rewind_pipeline):
        lint_result = lint_pipeline_full(
            rewind_pipeline["pipeline_path"],
            vars={},
            rewind_to="save_step",
        )
        assert not lint_result.valid
        assert any("saved artifact" in err for err in lint_result.errors)

        # Create artifact manually then lint again
        rewind_pipeline["output_path"].parent.mkdir(parents=True, exist_ok=True)
        rewind_pipeline["output_path"].write_text("snapshot", encoding="utf-8")
        lint_result = lint_pipeline_full(
            rewind_pipeline["pipeline_path"],
            vars={},
            rewind_to="save_step",
        )
        assert lint_result.valid

    def test_lint_no_error_for_step_without_saveas(self, rewind_pipeline):
        """Removing saveas from a step in the rewind chain should not be a lint error;
        the step will simply be re-executed during rewind."""
        pipeline_path = rewind_pipeline["pipeline_path"]
        data = yaml.safe_load(Path(pipeline_path).read_text(encoding="utf-8"))
        data["steps"][0].pop("saveas")
        # Also pre-create artifact so the remaining saveas check can pass
        # (there is no saveas to check since we removed it — lint should just pass)
        Path(pipeline_path).write_text(yaml.safe_dump(data), encoding="utf-8")

        lint_result = lint_pipeline_full(
            pipeline_path,
            vars={},
            rewind_to="save_step",
        )
        # No error — step without saveas is silently re-executed
        assert not any("must declare saveas" in err for err in lint_result.errors)

    def test_lint_skips_existence_check_for_dynamic_saveas_path(self, dynamic_path_pipeline):
        """Steps whose saveas path contains unresolved variables (dynamic, depending on
        runtime outputs) should not cause a lint error — they are deferred to execution."""
        lint_result = lint_pipeline_full(
            dynamic_path_pipeline["pipeline_path"],
            vars={},
            rewind_to="heavy_step",
        )
        # Should NOT error due to unresolved ${prefix_info.prefix} in saveas path
        assert not any("unresolved" in err.lower() for err in lint_result.errors)
        assert not any("must declare saveas" in err for err in lint_result.errors)

    def test_lint_still_errors_for_resolvable_missing_artifact(self, rewind_pipeline):
        """A fully-resolvable saveas path that points to a missing file is still an error."""
        lint_result = lint_pipeline_full(
            rewind_pipeline["pipeline_path"],
            vars={},
            rewind_to="save_step",
        )
        assert not lint_result.valid
        assert any("saved artifact" in err for err in lint_result.errors)
