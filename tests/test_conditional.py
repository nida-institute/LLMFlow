"""Tests for conditional step type with after actions."""
from llmflow.runner import run_step

def test_conditional_step_with_continue():
    """Test that if step with condition executes 'after: continue' when condition is true."""
    step = {
        "name": "check-empty",
        "type": "if",
        "condition": "${is_empty}",
        "after": "continue"
    }
    context = {"is_empty": True}
    pipeline_config = {}

    after_action = run_step(step, context, pipeline_config)

    assert after_action == "continue"


def test_conditional_step_condition_false():
    """Test that if step skips when condition is false."""
    step = {
        "name": "check-full",
        "type": "if",
        "condition": "${has_items}",
        "after": "continue"
    }
    context = {"has_items": False}
    pipeline_config = {}

    after_action = run_step(step, context, pipeline_config)

    assert after_action is None  # Skipped, no action


def test_conditional_step_with_break():
    """Test that if step can execute 'after: exit'."""
    step = {
        "name": "check-error",
        "type": "if",
        "condition": "${has_error}",
        "after": "exit"
    }
    context = {"has_error": True}
    pipeline_config = {}

    after_action = run_step(step, context, pipeline_config)

    assert after_action == "exit"


def test_conditional_step_without_after():
    """Test that if step works without after action."""
    step = {
        "name": "log-info",
        "type": "if",
        "condition": "True",
        "steps": []  # No nested steps, just checking condition
    }
    context = {}
    pipeline_config = {}

    after_action = run_step(step, context, pipeline_config)

    assert after_action is None