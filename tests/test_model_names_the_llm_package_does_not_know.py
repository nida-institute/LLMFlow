"""An OpenAI model name the `llm` package does not list is still callable.

Measured in sil-translator-notes: two steps used a dated gpt-4o snapshot, which OpenAI serves
(`DATED` below). The step with `response_format` went to OpenAI's client and succeeded; the next, without
it, went through `llm.get_model`, which does not list dated snapshots, raised `UnknownModelError`
— and was retried twice more before failing, though no retry can make a name known.

So a name the `llm` package does not know, for an OpenAI model, is called through OpenAI's client
as the structured-output path already is; any other unknown name fails at once, unretried.
"""
import tempfile
from pathlib import Path
from unittest.mock import patch

import llm
import pytest
import yaml

from llmflow import load_pipeline
from llmflow.utils.llm_runner import call_llm

DATED = "gpt-4o-2024-08-06"


def _unknown(name):
    raise llm.UnknownModelError(f"Unknown model: {name}")


def test_a_dated_openai_name_is_called_through_openai_s_client():
    with patch("llmflow.utils.llm_runner.llm.get_model", side_effect=_unknown), \
         patch("llmflow.utils.llm_runner._call_openai_with_response_format",
               return_value={"content": "notes", "usage": {}}) as direct:
        result = call_llm("Render these notes.", config={"model": DATED})
    assert direct.called, "the name OpenAI serves must reach OpenAI"
    assert result == {"content": "notes", "usage": {}}


def test_a_name_the_llm_package_knows_still_goes_through_it():
    with patch("llmflow.utils.llm_runner._call_model",
               return_value={"content": "x", "usage": {}}) as through_llm, \
         patch("llmflow.utils.llm_runner._call_openai_with_response_format") as direct:
        call_llm("Hello.", config={"model": "gpt-4o"})
    assert through_llm.called and not direct.called


def test_an_unknown_name_that_is_not_openai_s_still_fails():
    """Nothing is guessed: only a name the OpenAI path serves is sent there."""
    with patch("llmflow.utils.llm_runner.llm.get_model", side_effect=_unknown), \
         patch("llmflow.utils.llm_runner._call_openai_with_response_format") as direct:
        with pytest.raises(llm.UnknownModelError):
            call_llm("Hello.", config={"model": "claude-9-imaginary"})
    assert not direct.called


def _pipeline(tmpdir, model):
    prompt = Path(tmpdir) / "p.gpt"
    prompt.write_text("---\nprompt:\n  requires: []\n---\nSay hello.\n", encoding="utf-8")
    step = {"name": "hello", "type": "llm", "prompt": {"file": str(prompt)}, "output": "out",
            "model": model}
    path = Path(tmpdir) / "p.yaml"
    path.write_text(yaml.safe_dump({"name": "p", "steps": [step]}), encoding="utf-8")
    return path


def test_an_unknown_model_is_not_retried():
    """A retry cannot make a name known; three attempts spent six seconds learning that."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _pipeline(tmpdir, "claude-9-imaginary")
        with patch("llmflow.steps.llm.call_llm",
                   side_effect=llm.UnknownModelError("Unknown model: claude-9-imaginary")) as calls, \
             patch("time.sleep"):
            with pytest.raises(llm.UnknownModelError):
                load_pipeline(str(path)).run(skip_lint=True)
    assert calls.call_count == 1
