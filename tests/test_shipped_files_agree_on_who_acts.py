"""The files `sp init` ships give one answer to who files issues, commits, pushes and opens PRs.

The workshop's second lesson asks participants to read the shipped skills and disciplines and say
who does each. They used to give different answers: the rules said the human commits, while the
`github-authority` discipline and its README entry let the agent push and open pull requests
unasked. Settled: the agent may create an issue in the project it works in (rule
`agent-may-file-issues`); the commit, the push, the pull request and the merge are the human's
(rule `commit-authority`). This file holds every shipped place that states either.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def _template(relative: str) -> str:
    import llmflow

    return (Path(llmflow.__file__).parent / "templates" / relative).read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    return text[text.index(start):text.index(end)]


def _discipline() -> str:
    return _template("sp/disciplines/github-authority.md")


@pytest.mark.parametrize("grant", ["push commits", "Create pull requests"])
def test_the_discipline_no_longer_grants_it(grant: str):
    may_do = _section(_discipline(), "## What AI may do without asking", "## The human's alone")
    assert grant not in may_do


def test_the_discipline_lets_the_agent_create_issues():
    may_do = _section(_discipline(), "## What AI may do without asking", "## The human's alone")
    assert "Create a GitHub issue" in may_do
    assert "agent-may-file-issues" in may_do


@pytest.mark.parametrize("act", ["Commit, push or merge", "Open a pull request"])
def test_the_discipline_reserves_it_for_the_human(act: str):
    assert act in _section(_discipline(), "## The human's alone", "## Hard stop")


def test_issue_creation_is_not_reserved_for_the_human():
    assert "GitHub issue" not in _section(_discipline(), "## The human's alone", "## Hard stop")


def test_the_readme_summary_agrees_with_the_discipline():
    text = _template("sp/disciplines/README.md")
    entry = text[text.index("### github-authority.md"):]
    entry = entry[:entry.index("\n### ")] if "\n### " in entry else entry
    assert "pushing and opening PRs need no" not in entry
    assert "creating issues in the project being worked on" in entry
    assert "opening a pull request and merging are the human's alone" in entry


def test_the_workflow_summary_names_both_rules():
    text = _template("project/docs/ai-context/sp/github-workflow.md")
    summary = text[text.index("## Workflow Summary"):]
    assert "agent-may-file-issues" in summary
    assert "commit-authority" in summary
