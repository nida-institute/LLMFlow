"""Guardrail: `sp doctor`'s help must not claim to be read-only, because it is not.

2026-08-25. The help string read *"Check that this machine is set up correctly (read-only;
reports, never repairs)"*. An assistant read it, concluded the command was safe to run against a
repository whose `HANDOFF.md` said not to, and `sp doctor` restored eight tracked files from the
shipped version — deleting `output_file_directory` declarations from two pipelines and thirteen
lines of rationale from a context document. All were recoverable because they were tracked and
uncommitted.

The command does exactly what `policy: generated` says it may: `managed_by_doctor()` returns
every generated entry and `_restore` overwrites it. The defect was the description, not the
behaviour — an R8 case, a claim in code that nothing checked.

This test is the check. It is deliberately about the *claim*, not the wording: any future help
text is free to say anything except that this command does not write.
"""
import re

import pytest

from llmflow.cli import build_parser


def _doctor_help() -> str:
    for action in build_parser()._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict) and "doctor" in choices:
            for name, parser in choices.items():
                if name == "doctor":
                    return next(
                        a.help for a in action._get_subactions() if a.dest == "doctor"
                    )
    pytest.fail("no `doctor` subcommand found on the parser")


#: Claims that would be false. Each is negation-aware: "not read-only" is an accurate warning
#: and must pass, while "read-only" as an assertion must fail. Caught by this test against its
#: own first fix, which opened with "Not read-only:".
FALSE_CLAIMS = (
    re.compile(r"(?<!not )(?<!isn't )(?<!is not )read[- ]only", re.I),
    re.compile(r"\bnever (repairs|writes|restores|modifies)\b", re.I),
    re.compile(r"\bdoes not (repair|write|restore|modify)\b", re.I),
    re.compile(r"\bwithout (changing|modifying|writing)\b", re.I),
)


def test_doctor_help_does_not_claim_to_be_read_only():
    help_text = _doctor_help()
    lying = [p.pattern for p in FALSE_CLAIMS if p.search(help_text)]
    assert not lying, (
        f"`sp doctor` help claims it does not write: {lying}\n"
        f"  help: {help_text!r}\n"
        "It restores every `policy: generated` file that is missing or has diverged."
    )


def test_doctor_help_says_it_writes():
    help_text = _doctor_help().lower()
    assert any(w in help_text for w in ("restore", "overwrit", "repair")), (
        f"`sp doctor` help does not say it writes files: {help_text!r}. "
        "A user deciding whether to run it needs that on the first line."
    )
