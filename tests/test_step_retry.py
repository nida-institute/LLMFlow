"""Tests for step-level retry logic."""

from pathlib import Path
import tempfile
from unittest.mock import patch

import pytest

from llmflow.runner import run_pipeline
from llmflow.exceptions import StepRetryError


# Helpers for function-step retries (module-level so pipeline can import by path)
FUNCTION_RETRY_STATE = {"calls": 0}


def flaky_function_no_inputs():  # pragma: no cover - executed via pipeline
    FUNCTION_RETRY_STATE["calls"] += 1
    if FUNCTION_RETRY_STATE["calls"] < 3:
        raise ValueError("not yet")
    return f"ok-{FUNCTION_RETRY_STATE['calls']}"


def constant_short_text():  # pragma: no cover - executed via pipeline
    return "tiny"


def _build_prompt(tmpdir: Path) -> Path:
    prompt_file = Path(tmpdir) / "retry-test.gpt"
    prompt_file.write_text("---\nprompt:\n  requires: []\n---\nReturn sample text")
    return prompt_file


def test_llm_step_retries_until_condition_passes():
    """LLM step should retry until condition resolves to False."""
    outputs = ["short", "still short", "this is finally long enough"]

    def fake_call_llm(*args, **kwargs):
        return outputs.pop(0)

    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_file = _build_prompt(Path(tmpdir))

        pipeline = {
            "name": "retry-text",
            "steps": [
                {
                    "name": "payload",
                    "type": "llm",
                    "prompt": {"file": str(prompt_file)},
                    "outputs": "payload",
                    "retry": {
                        "max_attempts": 3,
                        "delay_seconds": 0,
                        "condition": "${len(payload or '') < 20}"
                    }
                }
            ]
        }

        with patch("llmflow.runner.call_llm", side_effect=fake_call_llm) as call_spy:
            with patch("time.sleep"):
                context = run_pipeline(pipeline, skip_lint=True)

        assert call_spy.call_count == 3
        assert context["payload"] == "this is finally long enough"


def test_llm_step_retry_condition_failure_raises():
    """If condition stays true, raise StepRetryError after max attempts."""
    outputs = ["short", "still short", "never long enough"]

    def fake_call_llm(*args, **kwargs):
        return outputs.pop(0)

    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_file = _build_prompt(Path(tmpdir))

        pipeline = {
            "name": "retry-failure",
            "steps": [
                {
                    "name": "payload",
                    "type": "llm",
                    "prompt": {"file": str(prompt_file)},
                    "outputs": "payload",
                    "retry": {
                        "max_attempts": 3,
                        "delay_seconds": 0,
                        "condition": "${len(payload or '') < 50}"
                    }
                }
            ]
        }

        with patch("llmflow.runner.call_llm", side_effect=fake_call_llm) as call_spy:
            with patch("time.sleep"):
                with pytest.raises(StepRetryError) as err:
                    run_pipeline(pipeline, skip_lint=True)

        assert call_spy.call_count == 3
        assert "payload" in str(err.value)
        assert "condition" in str(err.value)


def test_function_step_retries_on_exception_until_success():
    """Function steps should retry when the callable raises."""
    FUNCTION_RETRY_STATE["calls"] = 0

    pipeline = {
        "name": "function-retry",
        "steps": [
            {
                "name": "flaky",
                "type": "function",
                "function": "tests.test_step_retry.flaky_function_no_inputs",
                "outputs": "result",
                "retry": {
                    "max_attempts": 4,
                    "delay_seconds": 0,
                    # no condition -> exception-driven retries
                },
            }
        ],
    }

    with patch("time.sleep"):
        context = run_pipeline(pipeline, skip_lint=True)

    assert FUNCTION_RETRY_STATE["calls"] == 3
    assert context["result"].startswith("ok-")


def test_append_to_state_restored_when_retry_fails():
    """Append targets should rollback if retries exhaust without success."""
    pipeline = {
        "name": "append-rollback",
        "variables": {"history": ["seed"]},
        "steps": [
            {
                "name": "short-text",
                "type": "function",
                "function": "tests.test_step_retry.constant_short_text",
                "outputs": "payload",
                "append_to": "history",
                "retry": {
                    "max_attempts": 2,
                    "delay_seconds": 0,
                    "condition": "${len(payload or '') < 10}",
                },
            }
        ],
    }

    with patch("time.sleep"):
        with pytest.raises(StepRetryError) as err:
            run_pipeline(pipeline, skip_lint=True)

    err_context = err.value.context
    assert err_context["history"] == ["seed"]
    assert "payload" not in err_context
