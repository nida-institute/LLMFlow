"""`/load-context` reads `project/HANDOFF.md`.

`/handoff` writes the file for the next session, and its own text calls `/load-context` the
bookend that reads it. The shipped `load-context` never did: it read CLAUDE.md, both indexes,
the rules and the disciplines, and mentioned the handoff only in its Related Skills list. So the
one document written for the next session was the one the next session skipped.

Reading it is not enough on its own. A handoff names the commit it was written against, and one
left behind by a session that then committed describes a tree that no longer exists — which is
why the skill compares it with `HEAD` before treating its next action as one.
"""

from __future__ import annotations

from pathlib import Path


def _skill_text() -> str:
    import llmflow

    path = Path(llmflow.__file__).parent / "templates" / "sp" / "skills" / "load-context" / "SKILL.md"
    return path.read_text(encoding="utf-8")


def _workflow_text() -> str:
    """The steps a session follows — not Related Skills, where the handoff already was."""
    text = _skill_text()
    return text[text.index("## Workflow"):text.index("## What NOT to Do")]


def test_the_workflow_reads_the_handoff():
    assert "project/HANDOFF.md" in _workflow_text()


def test_the_handoff_is_checked_against_head():
    workflow = _workflow_text()
    assert "git rev-parse HEAD" in workflow


def test_the_orientation_summary_reports_the_handoff():
    workflow = _workflow_text()
    summary = workflow[workflow.index("Report Orientation Summary"):]
    assert "handoff" in summary.lower()


def test_a_project_without_a_handoff_is_not_an_error():
    assert "skips this in silence" in _workflow_text()
