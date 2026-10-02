"""`sp lint` reads a prompt's mixins the way a run does.

A run expands every `{{mixin:path}}` before it checks the prompt contract, so a variable inside
a mixin must be declared in `requires:` and a mixin file that does not exist is an error. Lint
must reach the same verdict before the run, or a pipeline lints clean and fails at the prompt
step after every earlier step has run and been paid for.
"""
import json

import pytest

from llmflow import load_pipeline

HEADER = "---\nprompt:\n  requires:\n{requires}---\n"


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    """A one-step llm pipeline over `prompts/p.gpt` and `prompts/mixins/*.md`."""
    monkeypatch.chdir(tmp_path)

    def _build(requires, body, mixins, inputs):
        prompts = tmp_path / "prompts"
        (prompts / "mixins").mkdir(parents=True, exist_ok=True)
        for name, text in mixins.items():
            (prompts / "mixins" / name).write_text(text, encoding="utf-8")
        listed = "".join(f"    - {name}\n" for name in requires)
        (prompts / "p.gpt").write_text(HEADER.format(requires=listed) + body, encoding="utf-8")
        cfg = {
            "name": "p",
            "variables": {name: "x" for name in inputs},
            "steps": [{
                "name": "s", "type": "llm",
                "prompt": {"file": "prompts/p.gpt", "inputs": {n: f"${{{n}}}" for n in inputs}},
                "output": "r",
            }],
        }
        path = tmp_path / "p.yaml"
        path.write_text(json.dumps(cfg), encoding="utf-8")
        return load_pipeline(str(path))

    return _build


def test_an_undeclared_variable_inside_a_mixin_fails_lint(pipeline):
    result = pipeline(
        requires=["passage"],
        body="Summarise {{passage}}.\n{{mixin:mixins/lang.md}}\n",
        mixins={"lang.md": "Answer in {{language}}.\n"},
        inputs=["passage"],
    ).lint()

    assert not result.valid, "a mixin's undeclared {{language}} passed lint"
    assert any("language" in error for error in result.errors), result.errors


def test_a_missing_mixin_file_fails_lint(pipeline):
    result = pipeline(
        requires=["passage"],
        body="Summarise {{passage}}.\n{{mixin:mixins/missing.md}}\n",
        mixins={},
        inputs=["passage"],
    ).lint()

    assert not result.valid, "a mixin naming no file passed lint"
    assert any("missing.md" in error for error in result.errors), result.errors


def test_a_declared_variable_used_only_in_a_mixin_is_clean(pipeline):
    result = pipeline(
        requires=["passage", "language"],
        body="Summarise {{passage}}.\n{{mixin:mixins/lang.md}}\n",
        mixins={"lang.md": "Answer in {{language}}.\n"},
        inputs=["passage", "language"],
    ).lint()

    assert result.valid, result.errors
    assert not any("language" in warning for warning in result.warnings), result.warnings
