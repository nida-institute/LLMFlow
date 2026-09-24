"""A response cut off at the output budget is reported as truncated, not as bad JSON (#247).

Step behaviour is driven through `load_pipeline(...).run()` rather than by handing
`run_llm_step` a dict, per `project/rules.md` rule 1. The stop-reason reader and the
ceiling are pure helpers and are called directly, which that rule's carve-out allows.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from llmflow import load_pipeline
from llmflow.exceptions import TruncationError
from llmflow.modules.telemetry import output_headroom, output_token_ceiling
from llmflow.utils.llm_runner import read_stop_reason

# --------------------------------------------------------------------------------------
# Fakes standing in for a provider response
# --------------------------------------------------------------------------------------

class _FakeUsage:
    def __init__(self, prompt_tokens, completion_tokens):
        self.input = prompt_tokens
        self.output = completion_tokens


class _FakeLLMResponse:
    """The shape `llm.models.Response` presents to `_call_model`."""

    def __init__(self, text, response_json, prompt_tokens=100, completion_tokens=2500):
        self._text = text
        self.response_json = response_json
        self._usage = _FakeUsage(prompt_tokens, completion_tokens)

    def text(self):
        return self._text

    def usage(self):
        return self._usage


class _FakeModel:
    def __init__(self, response):
        self._response = response

    def prompt(self, prompt, **options):
        return self._response


class _FinishReason:
    """An SDK object, to prove the reader walks attributes and not only dict keys."""

    def __init__(self, finish_reason):
        self.finish_reason = finish_reason


class _SDKResponse:
    def __init__(self, finish_reason):
        self.choices = [_FinishReason(finish_reason)]


def _pipeline_file(tmpdir, step_extra=None, pipeline_extra=None):
    prompt_file = Path(tmpdir) / "truncation-test.gpt"
    prompt_file.write_text("---\nprompt:\n  requires: []\n---\nReturn sample JSON")

    step = {
        "name": "segment_window",
        "type": "llm",
        "prompt": {"file": str(prompt_file)},
        "output": "payload",
        "output_type": "json",
        "model": "gpt-4o",
        "max_tokens": 2500,
    }
    if step_extra:
        step.update(step_extra)

    pipeline = {"name": "truncation-test", "steps": [step]}
    if pipeline_extra:
        pipeline.update(pipeline_extra)

    path = Path(tmpdir) / "truncation-test.yaml"
    path.write_text(yaml.safe_dump(pipeline))
    return path


def _defects_after_run(tmpdir, response):
    """Run a one-step pipeline against *response* and return the defect log it wrote."""
    intermediate = Path(tmpdir) / "intermediate"
    path = _pipeline_file(
        tmpdir, pipeline_extra={"intermediate_file_directory": str(intermediate)}
    )
    with patch("llmflow.utils.llm_runner.get_model", return_value=_FakeModel(response)):
        load_pipeline(str(path)).run(skip_lint=True)
    return json.loads((intermediate / "defects.json").read_text())


# --------------------------------------------------------------------------------------
# Reading the stop reason — one reader, several providers
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"choices": [{"finish_reason": "length"}]}, "length"),
        ({"stop_reason": "max_tokens"}, "max_tokens"),
        ({"candidates": [{"finishReason": "MAX_TOKENS"}]}, "max_tokens"),
        ({"incomplete_details": {"reason": "max_output_tokens"}}, "max_output_tokens"),
        ({"finish_reason": "length"}, "length"),
    ],
    ids=["openai-chat", "anthropic", "gemini", "responses-api", "flattened"],
)
def test_the_stop_reason_is_read_from_each_provider_shape(payload, expected):
    assert read_stop_reason(payload) == expected


def test_the_stop_reason_is_read_from_an_sdk_object_not_only_a_dict():
    assert read_stop_reason(_SDKResponse("length")) == "length"


def test_a_normal_stop_is_read_and_is_not_a_truncation():
    assert read_stop_reason({"choices": [{"finish_reason": "stop"}]}) == "stop"


def test_a_payload_carrying_no_stop_reason_reads_as_none():
    """None means 'could not be read' — never 'was not truncated'."""
    assert read_stop_reason({"something": "else"}) is None
    assert read_stop_reason(None) is None


# --------------------------------------------------------------------------------------
# The ceiling — derived, or declared underivable
# --------------------------------------------------------------------------------------

def test_the_ceiling_is_the_smaller_of_the_output_budget_and_the_remaining_context():
    # gpt-4o: max_output 16384, max_context 128000.
    assert output_token_ceiling("gpt-4o", prompt_tokens=100) == 16384
    # With the context nearly spent, the remaining context is the binding limit.
    assert output_token_ceiling("gpt-4o", prompt_tokens=120000) == 8000


def test_the_ceiling_is_none_for_a_model_the_table_does_not_carry():
    """Underivable is None and must be said, not guessed."""
    assert output_token_ceiling("totally-fake-model-9000", prompt_tokens=100) is None


def test_the_ceiling_is_never_negative():
    assert output_token_ceiling("gpt-4o", prompt_tokens=999_999) == 0


# --------------------------------------------------------------------------------------
# A truncation never reaches the JSON parser
# --------------------------------------------------------------------------------------

def test_a_truncated_response_never_reaches_the_json_parser():
    truncated = '{"segments": [{"text": "In the beginning was the W'
    response = _FakeLLMResponse(truncated, {"choices": [{"finish_reason": "length"}]})

    with tempfile.TemporaryDirectory() as tmpdir:
        path = _pipeline_file(tmpdir)

        with patch("llmflow.utils.llm_runner.get_model", return_value=_FakeModel(response)):
            with patch("llmflow.utils.llm_runner.parse_llm_json_response") as parser_spy:
                with patch("time.sleep"):
                    with pytest.raises(TruncationError):
                        load_pipeline(str(path)).run(skip_lint=True)

        assert parser_spy.call_count == 0, (
            "a truncated response reached the JSON parser; it must be refused before that"
        )


def test_a_response_that_stopped_normally_is_parsed_as_usual():
    response = _FakeLLMResponse('{"ok": true}', {"choices": [{"finish_reason": "stop"}]})

    with tempfile.TemporaryDirectory() as tmpdir:
        path = _pipeline_file(tmpdir)

        with patch("llmflow.utils.llm_runner.get_model", return_value=_FakeModel(response)):
            context = load_pipeline(str(path)).run(skip_lint=True)

    assert context["payload"] == {"ok": True}


def test_a_provider_whose_stop_reason_cannot_be_read_says_so(caplog):
    """Unreadable must not read as 'not truncated' — the run says which it is."""
    response = _FakeLLMResponse('{"ok": true}', {"no_stop_reason_here": True})

    with tempfile.TemporaryDirectory() as tmpdir:
        path = _pipeline_file(tmpdir)

        with patch("llmflow.utils.llm_runner.get_model", return_value=_FakeModel(response)):
            context = load_pipeline(str(path)).run(skip_lint=True)

    assert context["payload"] == {"ok": True}
    assert any(
        "stop reason" in record.message.lower() for record in caplog.records
    ), "the engine must say when it could not read whether a response was truncated"


# --------------------------------------------------------------------------------------
# A truncation is not retried
# --------------------------------------------------------------------------------------

def test_a_truncation_fails_on_the_first_attempt_rather_than_the_third():
    """Truncation is a certainty, not a transient failure. Retrying it buys nothing."""
    truncating = TruncationError(
        "cut off", provider="openai", model="gpt-4o", stop_reason="length",
        configured_max_tokens=2500, completion_tokens=2500, prompt_tokens=100,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = _pipeline_file(tmpdir)

        with patch("llmflow.steps.llm.call_llm", side_effect=truncating) as call_spy:
            with patch("time.sleep"):
                with pytest.raises(TruncationError):
                    load_pipeline(str(path)).run(skip_lint=True)

    assert call_spy.call_count == 1, (
        f"a truncation cost {call_spy.call_count} calls to discover; it must cost one"
    )


def test_a_transient_failure_is_still_retried():
    """The retry loop stays correct for what it was written for."""
    outcomes = [ConnectionError("flaky"), ConnectionError("flaky"), {"content": {"ok": True}, "usage": {}}]

    with tempfile.TemporaryDirectory() as tmpdir:
        path = _pipeline_file(tmpdir)

        with patch("llmflow.steps.llm.call_llm", side_effect=outcomes) as call_spy:
            with patch("time.sleep"):
                context = load_pipeline(str(path)).run(skip_lint=True)

    assert call_spy.call_count == 3
    assert context["payload"] == {"ok": True}


# --------------------------------------------------------------------------------------
# What the report says
# --------------------------------------------------------------------------------------

def test_the_report_names_the_step_and_the_budget_that_was_hit():
    truncated = '{"segments": [{"text": "cut off here'
    response = _FakeLLMResponse(
        truncated, {"choices": [{"finish_reason": "length"}]},
        prompt_tokens=100, completion_tokens=2500,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = _pipeline_file(tmpdir)

        with patch("llmflow.utils.llm_runner.get_model", return_value=_FakeModel(response)):
            with patch("time.sleep"):
                with pytest.raises(TruncationError) as err:
                    load_pipeline(str(path)).run(skip_lint=True)

    message = str(err.value)
    assert "segment_window" in message, "the report must name the step"
    assert "2500" in message, "the report must name the budget that was hit"
    assert "position" not in message.lower(), (
        "the report must not describe a truncation as a character-offset parse failure"
    )


def test_the_report_names_the_ceiling_when_it_can_be_derived():
    response = _FakeLLMResponse(
        '{"cut', {"choices": [{"finish_reason": "length"}]},
        prompt_tokens=100, completion_tokens=2500,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = _pipeline_file(tmpdir)

        with patch("llmflow.utils.llm_runner.get_model", return_value=_FakeModel(response)):
            with patch("time.sleep"):
                with pytest.raises(TruncationError) as err:
                    load_pipeline(str(path)).run(skip_lint=True)

    # gpt-4o with 100 prompt tokens: min(16384, 128000 - 100) == 16384.
    assert "16384" in str(err.value), "the report must name the derivable ceiling"


def test_the_report_says_when_the_ceiling_cannot_be_derived():
    """A number it cannot derive is never printed — it says so instead."""
    response = _FakeLLMResponse(
        '{"cut', {"choices": [{"finish_reason": "length"}]},
        prompt_tokens=100, completion_tokens=2500,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = _pipeline_file(tmpdir, step_extra={"model": "totally-fake-model-9000"})

        with patch("llmflow.utils.llm_runner.get_model", return_value=_FakeModel(response)):
            with patch("time.sleep"):
                with pytest.raises(TruncationError) as err:
                    load_pipeline(str(path)).run(skip_lint=True)

    message = str(err.value).lower()
    assert "could not be derived" in message or "not in the model table" in message


def test_the_report_says_plainly_when_the_budget_already_equals_the_ceiling():
    """The case an operator most needs told: raising max_tokens cannot help."""
    response = _FakeLLMResponse(
        '{"cut', {"choices": [{"finish_reason": "length"}]},
        prompt_tokens=100, completion_tokens=16384,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = _pipeline_file(tmpdir, step_extra={"max_tokens": 16384})

        with patch("llmflow.utils.llm_runner.get_model", return_value=_FakeModel(response)):
            with patch("time.sleep"):
                with pytest.raises(TruncationError) as err:
                    load_pipeline(str(path)).run(skip_lint=True)

    assert "already at the ceiling" in str(err.value).lower()


# --------------------------------------------------------------------------------------
# Headroom — the near miss, reported while the run is still worth saving (#247 item 4)
#
# The channel is the defect log (#232): a step recording what it noticed but did not fail
# on. The record carries the provider's own numbers, not a bare warning.
# --------------------------------------------------------------------------------------

def test_headroom_reports_the_providers_own_numbers():
    found = output_headroom("gpt-4o", configured_max_tokens=2500,
                            prompt_tokens=100, completion_tokens=2400)
    assert found["completion_tokens"] == 2400
    assert found["configured_max_tokens"] == 2500
    assert found["prompt_tokens"] == 100
    assert found["remaining"] == 100
    assert found["utilization"] == pytest.approx(0.96)
    assert found["ceiling"] == 16384


def test_headroom_flags_a_step_close_to_its_budget():
    assert output_headroom("gpt-4o", 2500, 100, 2400)["is_high"] is True


def test_headroom_does_not_flag_a_step_well_inside_its_budget():
    assert output_headroom("gpt-4o", 2500, 100, 500)["is_high"] is False


def test_headroom_says_when_the_budget_is_already_at_the_ceiling():
    found = output_headroom("gpt-4o", 16384, 100, 16000)
    assert found["at_ceiling"] is True


def test_headroom_is_none_when_there_is_nothing_to_say():
    """No budget configured, or nothing generated: the question does not apply."""
    assert output_headroom("gpt-4o", None, 100, 2400) is None
    assert output_headroom("gpt-4o", 2500, 100, 0) is None


def test_a_step_close_to_its_budget_is_recorded_in_the_defect_log():
    response = _FakeLLMResponse(
        '{"ok": true}', {"choices": [{"finish_reason": "stop"}]},
        prompt_tokens=100, completion_tokens=2400,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        written = _defects_after_run(tmpdir, response)

    assert written["counts"]["warning"] == 1
    entry = written["defects"][0]
    assert entry["step"] == "segment_window"
    assert "output budget" in entry["message"].lower()


def test_the_defect_carries_the_numbers_the_provider_gave_us():
    response = _FakeLLMResponse(
        '{"ok": true}', {"choices": [{"finish_reason": "stop"}]},
        prompt_tokens=100, completion_tokens=2400,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        written = _defects_after_run(tmpdir, response)

    detail = written["defects"][0]["detail"]
    assert detail["completion_tokens"] == 2400
    assert detail["configured_max_tokens"] == 2500
    assert detail["prompt_tokens"] == 100
    assert detail["ceiling"] == 16384
    assert detail["model"] == "gpt-4o"


def test_a_step_well_inside_its_budget_records_no_defect():
    """`[]` is the run saying it looked and found nothing."""
    response = _FakeLLMResponse(
        '{"ok": true}', {"choices": [{"finish_reason": "stop"}]},
        prompt_tokens=100, completion_tokens=200,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        written = _defects_after_run(tmpdir, response)

    assert written["defects"] == []
    assert written["counts"] == {"warning": 0, "error": 0}


def test_provider_usage_details_are_forwarded_rather_than_discarded():
    """Cached and reasoning token counts are optimization information the provider gave us."""
    response = _FakeLLMResponse('{"ok": true}', {"choices": [{"finish_reason": "stop"}]})
    response._usage.details = {"cached_tokens": 64, "reasoning_tokens": 128}

    with patch("llmflow.utils.llm_runner.get_model", return_value=_FakeModel(response)):
        from llmflow.utils.llm_runner import _call_model
        result = _call_model(_FakeModel(response), "prompt", {"model": "gpt-4o"})

    assert result["usage"]["details"] == {"cached_tokens": 64, "reasoning_tokens": 128}
