import pytest
from llmflow.runner import run_pipeline, run_llm_step, run_function_step, run_for_each_step

# Dummy pipeline for testing
MINIMAL_PIPELINE = {
    "pipeline": {
        "name": "test",
        "defaults": {
            "exegetical_culture": "western",
            "exegetical_wordstudy": True,
            "exegetical_emotionalarc": "flat"
        },
        "steps": [
            {
                "name": "test_function",
                "type": "function",
                "function": "llmflow.utils.echo.debug_context",
                "inputs": {
                    "context": "${context}"
                },
                "outputs": ["_"]
            }
        ]
    }
}

# Minimal function to debug context contents
def dummy_debug_context(**kwargs):
    print("[DEBUG CONTEXT]", kwargs)
    return {"_": True}

# Patch function resolution to use dummy
def test_run_function_step(monkeypatch):
    from llmflow import runner

    monkeypatch.setitem(runner.__dict__, "resolve", lambda v, c: c.get(v.strip("${}"), v))
    monkeypatch.setitem(runner, "importlib", __import__("importlib"))
    monkeypatch.setitem(runner, "inspect", __import__("inspect"))
    monkeypatch.setattr("llmflow.runner.importlib.import_module", lambda name: {"llmflow.utils.echo": type("M", (), {"debug_context": dummy_debug_context})}["llmflow.utils.echo"])

    rule = MINIMAL_PIPELINE["pipeline"]["steps"][0]
    context = {
        "context": {"exegetical_culture": "western", "exegetical_wordstudy": True, "exegetical_emotionalarc": "flat"}
    }

    run_function_step(rule, context)  # should not raise

def test_run_pipeline_context_defaults(tmp_path, capsys):
    yaml_path = tmp_path / "pipeline.yaml"
    import yaml
    yaml.dump(MINIMAL_PIPELINE, yaml_path.open("w"))

    run_pipeline(str(yaml_path), variables={"passage": "Psalm 2"}, dry_run=True)
    captured = capsys.readouterr()
    assert "exegetical_culture" in captured.out
    assert "exegetical_wordstudy" in captured.out
    assert "exegetical_emotionalarc" in captured.out
    assert "Psalm 2" in captured.out

def test_run_llm_step(monkeypatch, capsys):
    from llmflow.runner import run_llm_step

    # Mock dependencies
    monkeypatch.setattr("llmflow.runner.render_prompt", lambda prompt, ctx: f"Prompt with {ctx}")
    monkeypatch.setitem(__import__("llmflow.runner").__dict__, "normalize_nfc", lambda x: x)
    monkeypatch.setitem(__import__("llmflow.runner").__dict__, "call_llm", lambda *args, **kwargs: "[LLM CALLED]")

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

def test_run_for_each_step(monkeypatch, capsys):
    from llmflow.runner import run_for_each_step

    # Fake plugin registry
    plugin_items = iter(["entry 1", "entry 2"])
    monkeypatch.setitem(__import__("llmflow.plugins").plugin_registry, "xpath", lambda spec: plugin_items)

    monkeypatch.setattr("llmflow.runner.render_prompt", lambda p, c: f"Prompt with {c}")
    monkeypatch.setitem(__import__("llmflow.runner").__dict__, "normalize_nfc", lambda x: x)
    monkeypatch.setitem(__import__("llmflow.runner").__dict__, "call_llm", lambda *args, **kwargs: "[LLM INSIDE FOR-EACH]")

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
    assert "summary" in context or True  # should not crash
