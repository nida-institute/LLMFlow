"""Tests for step-level retry logic."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from llmflow import load_pipeline
from llmflow.exceptions import ModerationError, StepRetryError
from llmflow.runner import run_pipeline

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
                    "output": "payload",
                    "retry": {
                        "max_attempts": 3,
                        "delay_seconds": 0,
                        "condition": "${len(payload or '') < 20}"
                    }
                }
            ]
        }

        with patch("llmflow.steps.llm.call_llm", side_effect=fake_call_llm) as call_spy:
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
                    "output": "payload",
                    "retry": {
                        "max_attempts": 3,
                        "delay_seconds": 0,
                        "condition": "${len(payload or '') < 50}"
                    }
                }
            ]
        }

        with patch("llmflow.steps.llm.call_llm", side_effect=fake_call_llm) as call_spy:
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
                "output": "result",
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
                "output": "payload",
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


def test_a_moderation_block_is_not_retried():
    """A provider block is a certainty, not a transient failure.

    `docs/moderation-handling.md` states that retries "will not succeed until the prompt
    changes" — the remedy is the mitigation checklist, which a human applies. Re-asking the
    identical prompt spends three blocked calls and six seconds of backoff to establish what
    the first call already did.

    Driven through `load_pipeline(...).run()` rather than a raw dict, per `project/rules.md`
    rule 1; the older tests above predate it (→ #250).
    """
    blocked = ModerationError(
        "OpenAI Responses API blocked step 'analyse' for model gpt-4o.",
        provider="openai",
        model="gpt-4o",
        step_name="analyse",
        reason="content_filter",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_file = _build_prompt(Path(tmpdir))
        path = Path(tmpdir) / "moderation.yaml"
        path.write_text(yaml.safe_dump({
            "name": "moderation-test",
            "steps": [{
                "name": "analyse",
                "type": "llm",
                "prompt": {"file": str(prompt_file)},
                "output": "payload",
                "model": "gpt-4o",
            }],
        }))

        with patch("llmflow.steps.llm.call_llm", side_effect=blocked) as call_spy:
            with patch("time.sleep"):
                with pytest.raises(ModerationError):
                    load_pipeline(str(path)).run(skip_lint=True)

    assert call_spy.call_count == 1, (
        f"a moderation block cost {call_spy.call_count} blocked calls to discover; it must cost one"
    )
