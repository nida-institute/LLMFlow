"""A run reports the optimization suggestions it derived, rather than computing them and
discarding them (#247).

`generate_optimization_suggestions` had no caller anywhere in the tree: the runner computed
a telemetry summary and left the suggestions switched off behind a comment. A suggestion
nobody is shown is indistinguishable from a suggestion never made.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from llmflow import load_pipeline


class _FakeUsage:
    def __init__(self, prompt_tokens, completion_tokens):
        self.input = prompt_tokens
        self.output = completion_tokens


class _FakeLLMResponse:
    def __init__(self, text, prompt_tokens, completion_tokens):
        self._text = text
        self.response_json = {"choices": [{"finish_reason": "stop"}]}
        self._usage = _FakeUsage(prompt_tokens, completion_tokens)

    def text(self):
        return self._text

    def usage(self):
        return self._usage


class _FakeModel:
    def __init__(self, response):
        self._response = response

    def prompt(self, prompt, **options):
        return self._response


def _run(tmpdir, model, prompt_tokens, completion_tokens):
    prompt_file = Path(tmpdir) / "suggestions.gpt"
    prompt_file.write_text("---\nprompt:\n  requires: []\n---\nSay something")

    path = Path(tmpdir) / "suggestions.yaml"
    path.write_text(yaml.safe_dump({
        "name": "suggestions-test",
        "steps": [{
            "name": "expensive_step",
            "type": "llm",
            "prompt": {"file": str(prompt_file)},
            "output": "payload",
            "model": model,
            "max_tokens": 4000,
        }],
    }))

    response = _FakeLLMResponse("some text", prompt_tokens, completion_tokens)
    with patch("llmflow.utils.llm_runner.get_model", return_value=_FakeModel(response)):
        load_pipeline(str(path)).run(skip_lint=True)


def test_a_run_reports_the_suggestions_it_derived(caplog):
    """A cheaper model for the same work is worth saying out loud."""
    with tempfile.TemporaryDirectory() as tmpdir:
        _run(tmpdir, model="gpt-5", prompt_tokens=500_000, completion_tokens=500_000)

    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert "gpt-4o" in logged, "the model-downgrade suggestion never reached the operator"


def test_a_run_with_nothing_to_suggest_says_so_rather_than_nothing(caplog):
    """Silence cannot be told from a check that did not run — so the run says which."""
    with tempfile.TemporaryDirectory() as tmpdir:
        _run(tmpdir, model="gpt-4o", prompt_tokens=100, completion_tokens=200)

    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert "No optimization suggestions" in logged
