import pytest
from llmflow.utils.linter import lint_pipeline_steps, ALLOWED_STEP_KEYS

def test_disallowed_keyword_fails():
    steps = [
        {"name": "bad-step", "type": "llm", "foo": "bar"}  # 'foo' is not allowed
    ]
    errors = lint_pipeline_steps(steps)
    assert errors, "Should fail for unknown keyword"
    assert "unknown keyword 'foo'" in errors[0]

def test_after_continue_allowed():
    steps = [
        {"name": "step1", "type": "llm", "after": "continue"}
    ]
    errors = lint_pipeline_steps(steps)
    assert not errors, "Should pass for after: continue"

def test_after_exit_allowed():
    steps = [
        {"name": "step2", "type": "llm", "after": "exit"}
    ]
    errors = lint_pipeline_steps(steps)
    assert not errors, "Should pass for after: exit"