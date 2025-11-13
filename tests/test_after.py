import pytest

class DummyContext(dict):
    pass

def dummy_run_step(step, context, pipeline_config=None):
    context.setdefault("steps_run", []).append(step["name"])

def test_after_continue_runs_all():
    steps = [
        {"name": "step1", "type": "llm", "after": "continue"},
        {"name": "step2", "type": "llm", "after": "continue"},
        {"name": "step3", "type": "llm"}
    ]
    context = DummyContext()
    run_pipeline_steps(steps, context)
    assert context["steps_run"] == ["step1", "step2", "step3"]

def test_after_exit_stops():
    steps = [
        {"name": "step1", "type": "llm", "after": "continue"},
        {"name": "step2", "type": "llm", "after": "exit"},
        {"name": "step3", "type": "llm"}
    ]
    context = DummyContext()
    run_pipeline_steps(steps, context)
    assert context["steps_run"] == ["step1", "step2"]

def run_pipeline_steps(steps, context):
    for rule in steps:
        dummy_run_step(rule, context)
        after_action = rule.get("after")
        if after_action:
            if after_action == "continue":
                continue
            elif after_action == "exit":
                break