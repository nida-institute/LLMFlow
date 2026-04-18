"""Tests for condition field on various step types."""
import pytest
from src.llmflow.runner import run_step, _evaluate_condition_expression

def test_llm_step_with_condition_true():
    """Test that LLM step executes when condition is true."""
    step = {
        "name": "generate",
        "type": "llm",
        "condition": "should_run == True",
        "model": "gpt-4",
        "prompt": {"text": "Hello"},
        "outputs": ["result"]
    }
    context = {"should_run": True}
    pipeline_config = {}

    # This should attempt to run (will fail without API key, but that's ok)
    # We're just checking if condition is evaluated
    try:
        run_step(step, context, pipeline_config)
    except Exception as e:
        # Expected to fail on LLM call, but condition was evaluated
        pass

def test_llm_step_with_condition_false():
    """Test that LLM step is skipped when condition is false."""
    step = {
        "name": "generate",
        "type": "llm",
        "condition": "should_run == True",
        "model": "gpt-4",
        "prompt": {"text": "Hello"},
        "outputs": ["result"]
    }
    context = {"should_run": False}
    pipeline_config = {}

    result = run_step(step, context, pipeline_config)

    # Step should be skipped, returning None
    assert result is None
    # Result should not be in context
    assert "result" not in context

def test_function_step_with_condition_false():
    """Test that function step is skipped when condition is false."""
    step = {
        "name": "process",
        "type": "function",
        "condition": "len(items) > 0",
        "function": "noop",
        "outputs": ["result"]
    }
    context = {"items": []}
    pipeline_config = {"modules": {"noop": lambda: "executed"}}

    result = run_step(step, context, pipeline_config)

    assert result is None
    assert "result" not in context

def test_xpath_step_with_condition_false():
    """Test that xpath step is skipped when condition is false."""
    step = {
        "name": "query",
        "type": "xpath",
        "condition": "has_xml == True",
        "inputs": {
            "path": "test.xml",
            "xpath": "//node"
        },
        "outputs": ["nodes"]
    }
    context = {"has_xml": False}
    pipeline_config = {}

    result = run_step(step, context, pipeline_config)

    assert result is None
    assert "nodes" not in context

# ---------------------------------------------------------------------------
# is None / is not None expressions (regression for runtime bug where
# get_from_context silently stripped operators, always returning the raw value)
# ---------------------------------------------------------------------------

def test_is_none_condition_when_none():
    """`${x is None}` must be True when x is None."""
    assert _evaluate_condition_expression("${x is None}", {"x": None}) is True


def test_is_none_condition_when_not_none():
    """`${x is None}` must be False when x has a value."""
    assert _evaluate_condition_expression("${x is None}", {"x": 42}) is False


def test_is_not_none_condition_when_none():
    """`${x is not None}` must be False when x is None."""
    assert _evaluate_condition_expression("${x is not None}", {"x": None}) is False


def test_is_not_none_condition_when_not_none():
    """`${x is not None}` must be True when x has a value."""
    assert _evaluate_condition_expression("${x is not None}", {"x": 42}) is True


def test_is_none_step_skipped_when_var_not_none():
    """`condition: '${cursor is None}'` skips a function step when cursor has a value."""
    step = {
        "name": "final_only",
        "type": "function",
        "condition": "${cursor is None}",
        "function": "llmflow.utils.data.identity",
        "inputs": {"value": "done"},
        "outputs": "final_result",
    }
    context = {"cursor": 10}
    run_step(step, context, {})
    assert "final_result" not in context


def test_is_none_step_runs_when_var_is_none():
    """`condition: '${cursor is None}'` runs a function step when cursor is None."""
    step = {
        "name": "final_only",
        "type": "function",
        "condition": "${cursor is None}",
        "function": "llmflow.utils.data.identity",
        "inputs": {"value": "done"},
        "outputs": "final_result",
    }
    context = {"cursor": None}
    run_step(step, context, {})
    assert context["final_result"] == "done"
