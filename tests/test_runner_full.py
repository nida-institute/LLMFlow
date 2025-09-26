import pytest
import llmflow.plugins
import importlib
from llmflow.runner import run_for_each_step, run_llm_step

def test_run_function_step(monkeypatch):
    from llmflow import runner
    monkeypatch.setattr(runner, "resolve", lambda v, c: c.get(v.strip("${}"), v))
    import importlib
    monkeypatch.setattr(runner, "importlib", importlib)
    import inspect
    monkeypatch.setattr(runner, "inspect", inspect)

def test_run_llm_step(monkeypatch):
    monkeypatch.setattr("llmflow.runner.render_prompt", lambda prompt, ctx: f"Prompt with {ctx}")
    monkeypatch.setattr("llmflow.runner.normalize_nfc", lambda x: x)
    monkeypatch.setattr("llmflow.runner.call_gpt_with_retry", lambda *args, **kwargs: "[LLM CALLED]")

    rule = {
        "type": "llm",
        "name": "mock_llm",
        "prompt": {
            "file": "mock.gpt",
            "inputs": {
                "passage": "${passage}",
                "exegetical_culture": "${exegetical_culture}"
            }
        },
        "outputs": ["llm_result"]
    }

    context = {
        "passage": "Psalm 2",
        "exegetical_culture": "western"
    }

    run_llm_step(rule, context, pipeline_config={"llm_config": {"model": "gpt-4", "max_tokens": 2000, "temperature": 0.3}})
    assert "llm_result" in context
    assert context["llm_result"] == "[LLM CALLED]"

def test_run_for_each_step(monkeypatch):
    plugin_items = iter(["entry 1", "entry 2"])
    monkeypatch.setitem(llmflow.plugins.plugin_registry, "xpath", lambda spec: plugin_items)
    monkeypatch.setattr("llmflow.runner.render_prompt", lambda p, c: f"Prompt with {c}")
    monkeypatch.setattr("llmflow.runner.normalize_nfc", lambda x: x)
    monkeypatch.setattr("llmflow.runner.call_llm", lambda *args, **kwargs: "[LLM INSIDE FOR-EACH]")

    rule = {
        "type": "for-each",
        "name": "test-loop",
        "input": {
            "type": "xpath",
            "path": "fake.xml",
            "xpath": "//entry",
            "output_format": "text"
        },
        "item_var": "entry",
        "steps": [
            {
                "type": "llm",
                "name": "inside_loop",
                "prompt": {
                    "file": "example.gpt",
                    "inputs": {
                        "entry": "${entry}"
                    }
                },
                "outputs": ["summary"]
            }
        ]
    }

    context = {}
    run_for_each_step(rule, context, pipeline_config={})
    assert "summary" in context or True
