"""Guardrail: the shipped CLI reference names every command the CLI defines.

A reference listing commands by hand falls behind the program silently, and the reader
who trusts it never finds out — the same failure that left three disciplines unshipped
behind a hand-kept list (#204, #181). So the list is checked against `build_parser()`,
which is the program itself.

Both sides are derived: the expected set comes from the parser, and the documented set is
read out of the shipped markdown. `check-the-source-not-the-rendering` requires that a
derivation from prose can never quietly reduce to nothing, so the documented set is
asserted non-empty before it is compared.
"""

import argparse
import re
from pathlib import Path


def _shipped_reference() -> Path:
    import llmflow

    return (
        Path(llmflow.__file__).parent
        / "templates"
        / "project"
        / "docs"
        / "ai-context"
        / "sp"
        / "command-line.md"
    )


def _commands() -> set[str]:
    """Every `sp …` command the parser defines, including subcommands."""
    from llmflow.cli import build_parser

    found: set[str] = set()

    def walk(parser: argparse.ArgumentParser, prefix: str) -> None:
        for action in parser._actions:
            if not isinstance(action, argparse._SubParsersAction):
                continue
            for name, sub in action.choices.items():
                line = f"{prefix} {name}"
                # A group such as `sp resource` is a namespace, not a command: it does
                # nothing without a subcommand, so the reference documents its members.
                if any(isinstance(a, argparse._SubParsersAction) for a in sub._actions):
                    walk(sub, line)
                else:
                    found.add(line)

    walk(build_parser(), "sp")
    return found


def _documented() -> set[str]:
    text = _shipped_reference().read_text(encoding="utf-8")
    return {m.replace("`", "") for m in re.findall(r"`sp [a-z][a-z-]*(?: [a-z][a-z-]*)?`", text)}


def test_the_reference_names_every_command():
    documented = _documented()
    assert documented, (
        f"no `sp …` commands were found in {_shipped_reference().name}; the pattern that "
        "reads them has stopped matching, so this guard was checking nothing"
    )

    missing = sorted(_commands() - documented)
    assert not missing, (
        "the CLI defines commands the shipped reference does not name:\n     "
        + "\n     ".join(missing)
        + f"\n   Add them to {_shipped_reference().name}, which is what a session reads "
        "to find out what sp can do."
    )


def test_the_reference_invents_no_commands():
    """The other direction: a documented command that no longer exists is worse than an
    undocumented one, because a reader tries it."""
    real = _commands()
    groups = {c.rsplit(" ", 1)[0] for c in real if " " in c.removeprefix("sp ")}
    invented = sorted(_documented() - real - groups - {"sp"})
    assert not invented, (
        "the shipped reference names commands the CLI does not have:\n     "
        + "\n     ".join(invented)
    )
