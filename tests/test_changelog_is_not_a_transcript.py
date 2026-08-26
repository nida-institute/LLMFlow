"""Guardrail: the unreleased section of `CHANGELOG.md` tells a user what changed.

The failure it catches is a changelog written as a record of the session that produced it —
conversational voice, process commentary, quoted direction, commit hashes, and free prose
where a reader expects a list of changes. Format: `docs/ai-context/sp/github-workflow.md`.

Only the unreleased section is checked. A released entry describes what users actually got,
so it is a record and is not rewritten; the time to fix the wording is before it ships.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"

UNRELEASED = "Unreleased"

#: Keep-a-Changelog, plus the headings this project's guidance and history use.
SECTIONS = frozenset({
    "Added", "Changed", "Deprecated", "Removed", "Fixed", "Security",
    "New Features", "Test Coverage", "Documentation",
})

FORBIDDEN = {
    "conversational voice": re.compile(
        r"(?<![\w`/-])(I|I'm|I'll|I've|we|we'll|we've|my|our|let's|you asked|"
        r"as (?:you )?(?:asked|requested|discussed)|per your)(?![\w`-])",
        re.I,
    ),
    # Skill names such as `handoff` and `stand-down` are shipped features, so they are absent
    # here; `TODO` is excluded when it is part of a path or a filename. "Captain" is caught
    # only where he is the agent of the change — a shipped rule may be *about* him.
    "session commentary": re.compile(
        r"\b(this session|this conversation|in conversation|next step|"
        r"as (?:noted|discussed) above|for now|WIP)\b"
        r"|(?<![/`\w])TODO\b(?!\.md)"
        r"|\b(?:at|per|by|on|from) (?:the )?Captain'?s?\b"
        r"|\bthe Captain (?:ruled|asked|said|directed|decided|requested|wanted|emptied)\b"
        r"|\bCaptain's (?:direction|ruling|request|instruction|decision|choice)\b",
        re.I,
    ),
    # A changelog cites a version or an issue. A hash names a commit no reader has.
    "a commit hash": re.compile(
        r"\b(?=[0-9a-f]{7,40}\b)(?=[0-9a-f]{0,39}[0-9])(?=[0-9a-f]{0,39}[a-f])[0-9a-f]{7,40}\b"
    ),
}

VERSION_HEADING = re.compile(r"^## (?P<name>.+?)\s*$")
SECTION_HEADING = re.compile(r"^### (?P<name>.+?)\s*$")


def unreleased_lines() -> list[tuple[int, str]]:
    """Numbered lines of the unreleased section, empty if the section is absent."""
    collected, inside = [], False
    for number, text in enumerate(CHANGELOG.read_text(encoding="utf-8").splitlines(), start=1):
        if match := VERSION_HEADING.match(text):
            inside = match.group("name").strip().lower() == UNRELEASED.lower()
        elif inside:
            collected.append((number, text))
    return collected


def test_the_changelog_has_an_unreleased_section():
    """Absent, every check below would pass by having nothing to read."""
    assert any(
        VERSION_HEADING.match(line) and VERSION_HEADING.match(line).group("name").strip().lower()
        == UNRELEASED.lower()
        for line in CHANGELOG.read_text(encoding="utf-8").splitlines()
    ), f"No `## {UNRELEASED}` heading — nothing to check, which is not the same as passing."


@pytest.mark.parametrize("kind", sorted(FORBIDDEN))
def test_no_transcript_voice(kind: str):
    pattern = FORBIDDEN[kind]
    offences = [
        f"CHANGELOG.md:{number}: {match.group()!r} — {text.strip()[:90]}"
        for number, text in unreleased_lines()
        if (match := pattern.search(text))
    ]
    assert not offences, (
        f"A changelog is read by someone who was not here. Remove the {kind}:\n  "
        + "\n  ".join(offences)
    )


def test_every_change_sits_under_a_known_section():
    """A bullet with no section above it has no category, so a reader cannot skim by kind."""
    section, orphans = None, []
    for number, text in unreleased_lines():
        if match := SECTION_HEADING.match(text):
            section = match.group("name")
        elif text.startswith(("- ", "* ")) and section is None:
            orphans.append(f"CHANGELOG.md:{number}: {text.strip()[:90]}")
    assert not orphans, "Bullets with no `###` section above them:\n  " + "\n  ".join(orphans)


def test_section_headings_are_from_the_known_set():
    unknown = [
        f"CHANGELOG.md:{number}: '### {match.group('name')}'"
        for number, text in unreleased_lines()
        if (match := SECTION_HEADING.match(text)) and match.group("name") not in SECTIONS
    ]
    assert not unknown, (
        "Unrecognised section. Add it to SECTIONS if it is intended:\n  " + "\n  ".join(unknown)
    )


def test_no_prose_before_the_first_section():
    """Process commentary lands here — a note to the next writer, not a change for a reader."""
    prose = []
    for number, text in unreleased_lines():
        if SECTION_HEADING.match(text):
            break
        if text.strip() and not text.startswith("#"):
            prose.append(f"CHANGELOG.md:{number}: {text.strip()[:90]}")
    assert not prose, (
        f"Prose under `## {UNRELEASED}`, before any section:\n  " + "\n  ".join(prose)
    )
