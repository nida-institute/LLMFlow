"""`docs/cli-api.json` — the map of what this engine actually offers.

`docs/index.json` maps the implementation and says in its own `about` that it is not an API.
That leaves a gap: having said what the surface is *not*, nothing declared what it *is*. This is
that declaration — the `sp` command line and the pipeline language, in one machine-readable file.

**Generated, for the reason everything here is generated.** A hand-kept list of commands and step
types is a second encoding of the parser and the schema; it agrees with them until it silently
does not. `docs/index.json` sat stale for seven months while appearing maintained, and the
shipped quick reference told every project a false thing about `include:` for months after it was
corrected elsewhere. So this derives from `build_parser()` and `PIPELINE_SCHEMA`, and a test
asserts it is current rather than trusting that someone re-ran the generator.

**Why it is worth having at all**, when both sources can be read directly: a consumer — a person,
a model, an editor — should not have to import the engine to find out what the engine offers.
Reading `PIPELINE_SCHEMA` means importing `llmflow`, which is the surface a project is told not to
build against. A JSON file on disk is the form that answer can take without contradicting itself.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAP = REPO_ROOT / "docs" / "cli-api.json"
GENERATOR = REPO_ROOT / "tools" / "index_cli_api.py"


def generated() -> dict:
    """What the generator produces now, from the parser and the schema."""
    result = subprocess.run(
        [sys.executable, str(GENERATOR)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=True,
    )
    return json.loads(result.stdout)


def committed() -> dict:
    return json.loads(MAP.read_text(encoding="utf-8"))


def test_the_map_is_current_with_its_generator():
    """The staleness check. Without it the file looks maintained while drifting."""
    assert committed() == generated(), (
        f"{MAP.relative_to(REPO_ROOT)} is out of date with its generator.\n"
        f"Regenerate it: hatch run python tools/index_cli_api.py > docs/cli-api.json"
    )


def test_it_declares_that_it_is_the_public_surface():
    """The counterpart to index.json's `not_an_api`: this one says it *is*."""
    about = " ".join(str(v) for v in committed().get("about", {}).values()).lower()
    assert about, "cli-api.json carries no `about` field"
    assert "public" in about, "`about` must say this is the public surface"
    assert "sp" in about and "pipeline" in about, (
        "`about` must name both halves of the surface — the command line and the language"
    )


def test_every_command_the_parser_offers_is_in_the_map():
    """Derived from `build_parser()`, so a new command cannot be missed."""
    import argparse

    from llmflow.cli import build_parser

    found: set[str] = set()

    def walk(parser: argparse.ArgumentParser, prefix: str) -> None:
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name, sub in action.choices.items():
                    found.add(f"{prefix} {name}")
                    walk(sub, f"{prefix} {name}")

    walk(build_parser(), "sp")
    assert found, "no commands discovered — the walk found nothing to check"
    assert set(committed()["commands"]) == found


def test_every_step_type_the_schema_declares_is_in_the_map():
    """Derived from the schema, so a new step type cannot be missed."""
    from llmflow.pipeline_schema import PIPELINE_SCHEMA

    declared: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            kind = node.get("properties", {}).get("type", {})
            if kind.get("const"):
                declared.add(kind["const"])
            declared.update(kind.get("enum", []))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(PIPELINE_SCHEMA)
    assert declared, "no step types discovered — the walk found nothing to check"
    assert set(committed()["step_types"]) == declared


def test_a_step_type_with_members_reports_them_and_which_is_primary():
    """`scripture` is the worked case: `text` primary, `reference` beside it."""
    scripture = committed()["step_types"]["scripture"]
    assert scripture["members"] == ["text", "reference"]
    assert scripture["primary_member"] == "text"


def test_a_step_type_without_members_says_so_rather_than_omitting_the_key():
    """`say-which-kind-of-nothing`: an empty list is 'asked, and there are none'."""
    llm = committed()["step_types"]["llm"]
    assert llm["members"] == []
    assert llm["primary_member"] is None
