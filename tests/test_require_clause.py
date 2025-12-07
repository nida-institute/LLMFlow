import pytest
from llmflow.runner import run_pipeline

# Minimal pipelines that do not depend on StoryFlow or external prompts/templates.

MINIMAL_OK = {
    "name": "require-clause-minimal-ok",
    "steps": [
        {
            "name": "produce_value",
            "type": "function",
            "function": "llmflow.utils.io.echo",
            "inputs": {"value": "Hello"},
            "outputs": "greeting",
            "require": [
                {"if": "greeting and len(str(greeting).strip()) > 0", "message": "greeting must be non-empty"}
            ],
        },
        {
            "name": "render_echo",
            "type": "function",
            "function": "llmflow.utils.io.echo",
            "inputs": {"value": "${greeting}"},
            "outputs": "rendered",
            "require": [
                {"if": "rendered and len(str(rendered).strip()) > 0", "message": "rendered must be non-empty"}
            ],
        },
    ],
}

MINIMAL_FAIL_REQUIRE = {
    "name": "require-clause-minimal-fail",
    "steps": [
        {
            "name": "produce_empty",
            "type": "function",
            "function": "llmflow.utils.io.echo",
            "inputs": {"value": "   "},  # empty after strip
            "outputs": "greeting",
            "require": [
                {"if": "greeting and len(str(greeting).strip()) > 0", "message": "greeting must be non-empty"}
            ],
        }
    ],
}

MINIMAL_WARN_ONLY = {
    "name": "warn-clause-minimal",
    "steps": [
        {
            "name": "produce_empty_but_warn",
            "type": "function",
            "function": "llmflow.utils.io.echo",
            "inputs": {"value": "   "},  # empty after strip
            "outputs": "greeting",
            "warn": [
                {"if": "not greeting or len(str(greeting).strip()) == 0", "message": "greeting is empty"}
            ],
        },
        {
            "name": "still_runs_next_step",
            "type": "function",
            "function": "llmflow.utils.io.echo",
            "inputs": {"value": "OK"},
            "outputs": "status",
        },
    ],
}

MINIMAL_REQUIRE_AND_WARN = {
    "name": "require-and-warn-mixed",
    "steps": [
        {
            "name": "produce_value",
            "type": "function",
            "function": "llmflow.utils.io.echo",
            "inputs": {"value": "Hi"},
            "outputs": "greeting",
            "warn": [
                {"if": "len(str(greeting)) < 3", "message": "greeting is very short"}
            ],
            "require": [
                {"if": "len(str(greeting)) >= 1", "message": "greeting must exist"}
            ],
        },
        {
            "name": "echo_again",
            "type": "function",
            "function": "llmflow.utils.io.echo",
            "inputs": {"value": "${greeting}"},
            "outputs": "echoed",
            "warn": [
                {"if": "len(str(echoed)) < 3", "message": "echoed result is still short"}
            ],
        },
    ],
}


def test_require_if_passes_with_nonempty_output():
    # Should pass once require is implemented; currently may pass but is a sanity check.
    res = run_pipeline(MINIMAL_OK)
    assert "rendered" in res
    assert "Hello" in str(res["rendered"])


def test_require_if_fails_on_empty_output():
    # Must fail (raise) when require condition is false.
    with pytest.raises(Exception) as exc:
        run_pipeline(MINIMAL_FAIL_REQUIRE)
    assert "greeting must be non-empty" in str(exc.value)


def test_warn_if_does_not_block_pipeline_and_is_surfaced():
    # Warn should not block, but must be surfaced on the result.
    res = run_pipeline(MINIMAL_WARN_ONLY)
    assert "status" in res
    assert res["status"] == "OK"
    warnings = res.get("_warnings", [])
    assert any("greeting is empty" in str(w) for w in warnings), "warn message not surfaced"


def test_require_and_warn_both_supported():
    res = run_pipeline(MINIMAL_REQUIRE_AND_WARN)
    assert res["echoed"] == "Hi"
    warnings = res.get("_warnings", [])
    expected = {"greeting is very short", "echoed result is still short"}
    assert any(any(msg in str(w) for msg in expected) for w in warnings), "expected warn not recorded"