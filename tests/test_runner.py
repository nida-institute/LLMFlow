import pytest
from llmflow import runner

def test_run_function_step(monkeypatch):
    monkeypatch.setattr(runner, "resolve", lambda v, c: c.get(v.strip("${}"), v))
    import importlib
    monkeypatch.setattr(runner, "importlib", importlib)
    import inspect
    monkeypatch.setattr(runner, "inspect", inspect)

    def dummy_debug_context(**kwargs):
        print("[DEBUG CONTEXT]", kwargs)
        return {"_": True}

    rule = {
        "type": "function",
        "name": "test_function",
        "function": "llmflow.utils.echo.debug_context",
        "inputs": {"context": "${context}"},
        "outputs": ["_"]
    }
    context = {
        "context": {
            "exegetical_culture": "western",
            "exegetical_wordstudy": True,
            "exegetical_emotionalarc": "flat"
        }
    }

    runner.run_function_step(rule, context)
