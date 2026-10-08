"""The local commit gate must cover every suite CI runs (#206), in any project.

`gui/frontend/` is a TypeScript project with its own Vitest tests, and CI runs them. The
`commit-ready` skill named only `hatch run pytest`, so a contributor who edited
`gui/frontend/src/App.tsx`, followed the skill to the letter, and saw the Python tests pass had
run none of the TypeScript tests. The first fix named this repository's frontend commands in the
skill, and these tests derived them from `.github/workflows/test.yml`.

**Then the skill became the workshop's first lesson** (Captain's ruling, 2026-10-07): *"it must
fit any project."* A gate naming `hatch`, `gui/frontend` and `pyproject.toml` instructs a mentee
about tools their project does not have — the same defect #206 was, inverted: a check that reads
as complete while checking nothing. So the general form of the #206 fix ships instead: **read
every suite from the CI workflow and run what CI runs.** That covers this repository's frontend
and any other project's second suite alike, and no list of commands in the skill can drift from
the workflow because there is no list.

The Captain ruled the extra suite **conditional** (2026-08-19): *"only when the change touches
gui/frontend"*. Generalised, the condition survives: a change that touches no part of a suite
does not need its toolchain installed.

The same ruling also moved the commit, the push and the pull request to the human (rule
`commit-authority`), which the old gates contradicted — they had the agent committing, pushing,
merging and deleting branches.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


def _skill_text() -> str:
    import llmflow

    path = (
        Path(llmflow.__file__).parent
        / "templates"
        / "sp" / "skills"
        / "commit-ready"
        / "SKILL.md"
    )
    return path.read_text(encoding="utf-8")


def test_the_gate_reads_its_suites_from_the_ci_workflow():
    """#206, generalised: the reader learns what to run from CI, not from this page."""
    text = _skill_text()
    assert ".github/workflows/" in text
    assert "Run what CI runs" in text


def test_a_suite_the_change_does_not_touch_is_not_required():
    """Captain's ruling, 2026-08-19: conditional, so one part's change needs no other toolchain."""
    text = _skill_text()
    assert "If the change touches" in text
    assert "If the change touches none of it" in text


# Tokens that tie the gate to one project's toolchain. Each was in the skill before the ruling.
PROJECT_SPECIFIC = {
    "hatch": re.compile(r"\bhatch\b"),
    "pytest invocation": re.compile(r"\bpytest\b"),
    "pytest.ini": re.compile(r"pytest\.ini"),
    "pyproject.toml": re.compile(r"pyproject\.toml"),
    "gui/frontend": re.compile(r"gui/frontend"),
    "npm": re.compile(r"\bnpm\b"),
    "npx": re.compile(r"\bnpx\b"),
    "logging.basicConfig": re.compile(r"basicConfig"),
    "Python-only glob": re.compile(r"\*\*/\*\.py"),
}


@pytest.mark.parametrize("label", sorted(PROJECT_SPECIFIC))
def test_the_gate_names_no_single_projects_toolchain(label: str):
    """Captain's ruling, 2026-10-07: commit-ready is taught first, so it must fit any project."""
    match = PROJECT_SPECIFIC[label].search(_skill_text())
    assert match is None, (
        f"commit-ready names {label} ({match.group(0)!r}); a project without it would be "
        "told to run a command it does not have. Point at the project's CLAUDE.md or CI instead."
    )


@pytest.mark.parametrize(
    "command",
    ["git commit", "git push", "git merge", "gh pr create", "gh pr merge", "git branch -d", "-X DELETE"],
)
def test_the_gate_never_has_the_agent_commit_push_merge_or_delete(command: str):
    """Rule `commit-authority`: the agent hands over; the human runs these.

    A command in a fenced block is one the reader is told to run, so none of these may be in one.
    """
    blocks = re.findall(r"```[a-z]*\n(.*?)```", _skill_text(), flags=re.DOTALL)
    offending = [b for b in blocks if command in b]
    assert not offending, f"commit-ready gives the agent {command!r} to run: {offending[0]!r}"


def test_the_gate_says_the_human_commits_and_pushes():
    text = _skill_text()
    assert "The human commits, pushes, opens the pull request and merges" in text.replace("\n", " ")
    assert "The human opens it" in text
    assert "commit-authority" in text


def test_the_gate_files_a_missing_issue_from_a_body_file():
    """Rule `agent-may-file-issues`: the agent files it, with the body in a file."""
    text = _skill_text()
    assert "--body-file tmp/issue.md" in text
    assert "agent-may-file-issues" in text
