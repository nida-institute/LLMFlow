"""The public surface, as data: every `sp` command and every step type.

`docs/index.json` maps the engine's implementation and says in its own `about` that it is not an
API. This is the other half — having said what the surface is not, this declares what it is.

**Why it is a file rather than a function to call.** A project has to be able to answer "what
does this engine offer?", and the alternative is importing the package to read `PIPELINE_SCHEMA`
— which is the one thing a project is told not to do. A JSON file on disk is the only form that
answer can take without contradicting itself, so this ships into every project alongside the
documents.

**Why it lives in the package rather than in `tools/`.** `tools/` is not in the wheel, so a
renderer there could not be reached by `sp init` in an installed project. One implementation
here, two callers: `sp init` writes it into a project, and `tools/index_cli_api.py` writes this
repository's own copy from the pre-commit hook.

Everything derives from `build_parser()` and `PIPELINE_SCHEMA`, so nothing here is a second
encoding that can drift from what the program does.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List

from llmflow.pipeline_schema import (
    PIPELINE_SCHEMA,
    allowed_step_keys,
    common_step_keys,
    step_members,
)

ABOUT = {
    "what": "The public surface of Scripture Pipelines: every `sp` command, and every step "
            "type the pipeline language offers with its keys and what it returns.",
    "this_is_the_api": "This IS the public API, and it is the whole of it. A project reaches "
                       "this engine through the sp command line and the pipeline language it "
                       "reads, and needs no Python at all.",
    "not_the_implementation": "docs/index.json is the other file and the opposite thing: it "
                              "maps the engine's modules and functions, carries no "
                              "compatibility promise, and is not a surface for projects or "
                              "for tests.",
    "if_something_is_missing": "Where the language cannot express what you need, that is a "
                               "missing construct worth reporting — not a reason to import the "
                               "package and reach past it.",
    "generated_by": "llmflow.cli_api, from build_parser() and PIPELINE_SCHEMA. Editing this "
                    "file by hand does not survive regeneration.",
}


def commands() -> Dict[str, dict]:
    """Every `sp` command and subcommand, with its help text and options."""
    from llmflow.cli import build_parser

    found: Dict[str, dict] = {}

    def options(parser: argparse.ArgumentParser) -> List[dict]:
        out = []
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction) or not action.option_strings:
                continue
            out.append(
                {
                    "flags": sorted(action.option_strings),
                    "help": action.help or "",
                    "required": bool(action.required),
                }
            )
        return sorted(out, key=lambda o: o["flags"])

    def walk(parser: argparse.ArgumentParser, prefix: str) -> None:
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name, sub in action.choices.items():
                    path = f"{prefix} {name}"
                    found[path] = {"help": sub.description or "", "options": options(sub)}
                    walk(sub, path)

    walk(build_parser(), "sp")
    return dict(sorted(found.items()))


def declared_step_types() -> set:
    """The step types the schema declares, read from the schema itself."""
    declared: set = set()

    def walk(node: Any) -> None:
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
    return declared


def step_types() -> Dict[str, dict]:
    """Every step type, its own keys, and what it returns."""
    common = common_step_keys()
    out: Dict[str, dict] = {}
    for name in sorted(declared_step_types()):
        allowed = allowed_step_keys(name) or set()
        members = list(step_members(name))
        out[name] = {
            # Its own keys, not the ones every step carries. That list is identical for all of
            # them and repeating it per type buries what makes a type different.
            "keys": sorted(allowed - common),
            # An empty list is "asked, and this type has none" — never "not looked at".
            # `say-which-kind-of-nothing`.
            "members": members,
            "primary_member": members[0] if members else None,
        }
    return out


def cli_api_map() -> dict:
    """The whole map, as a dict."""
    cmds = commands()
    types = step_types()
    return {
        "about": ABOUT,
        "commands": cmds,
        "step_types": types,
        "common_step_keys": sorted(common_step_keys()),
        "summary": {"total_commands": len(cmds), "total_step_types": len(types)},
    }


def render_cli_api() -> str:
    """The map as the JSON text that is written to disk."""
    return json.dumps(cli_api_map(), ensure_ascii=False, indent=2) + "\n"
