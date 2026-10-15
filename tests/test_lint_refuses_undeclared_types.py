"""`sp lint` refuses a step type that nothing declares.

A step type is valid when the public API lists it — `docs/cli-api.json`, which holds the types
the pipeline schema declares and the ones built-in plugins provide. A project's own plugin is
named by `plugin:` instead, so a step carrying that key is not checked here. Anything else would
fail only at run time, with `Unknown step type` — after every step before it has run and been paid
for.

Driven through `sp lint`, per `docs/ai-context/project/rules.md` rule 1.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from llmflow.cli import main

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_TYPES = sorted(
    json.loads((REPO_ROOT / "docs" / "cli-api.json").read_text(encoding="utf-8"))["step_types"]
)

#: Logged when the phase holding the type check starts. That phase reports every error it finds,
#: so once it has run, the absence of an undeclared-type error means the type was accepted. A
#: bare step fails other checks — `load_json` lacks `path`, `llm` a prompt — so neither `valid`
#: nor the phase passing can say it.
KEYWORDS_PHASE = "Validating step keywords"
UNDECLARED = "which sp does not declare"


def lint(tmp_path, monkeypatch, capsys, step: str) -> dict:
    """`sp lint --json` on a one-step pipeline; its JSON answer."""
    pipeline = tmp_path / "pipeline.yaml"
    pipeline.write_text(f"name: under-test\nsteps:\n  - name: s\n{step}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    try:
        main(["lint", "--json", "--pipeline", str(pipeline)])
    except SystemExit:
        pass
    out = capsys.readouterr().out
    return json.loads(out[out.index("{\n"):])


def test_an_undeclared_type_is_refused(tmp_path, monkeypatch, capsys):
    result = lint(tmp_path, monkeypatch, capsys, "    type: no_such_step_type\n")
    assert not result["valid"]
    assert any(
        UNDECLARED in error and "'no_such_step_type'" in error for error in result["errors"]
    ), result["errors"]


def test_a_misspelt_type_names_the_nearest_declared_one(tmp_path, monkeypatch, capsys):
    result = lint(tmp_path, monkeypatch, capsys, "    type: scriptur\n")
    assert any("'scripture'" in error for error in result["errors"]), result["errors"]


@pytest.mark.parametrize("step_type", PUBLIC_TYPES)
def test_every_type_the_public_api_lists_is_accepted(
    step_type, tmp_path, monkeypatch, capsys, caplog
):
    with caplog.at_level(logging.INFO):
        result = lint(tmp_path, monkeypatch, capsys, f"    type: {step_type}\n")
    assert any(KEYWORDS_PHASE in r.getMessage() for r in caplog.records), (
        "lint stopped before the type check ran", result["errors"]
    )
    assert not [error for error in result["errors"] if UNDECLARED in error]


def test_a_project_plugin_is_named_by_plugin_and_not_checked(tmp_path, monkeypatch, capsys):
    result = lint(
        tmp_path,
        monkeypatch,
        capsys,
        "    type: my_own_step\n    plugin: my_project.plugins.thing\n",
    )
    assert result["valid"], result["errors"]
