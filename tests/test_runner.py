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
