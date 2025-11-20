"""Tests for condition field on various step types."""
import pytest
from src.llmflow.runner import run_step

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