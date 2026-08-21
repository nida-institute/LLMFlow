"""The cursor guidance we ship must not teach the form that silently drops content.

Reported 2026-08-21 by an AI session in `nida-institute/discourse-flow`:
`collab/sp/windowing-semantics-gap.md`. The engine behaved correctly throughout — what was
wrong was our own worked example.

**The defect.** `LANGUAGE_QUICKREF_DOC` showed the cursor being set from the *dropped* last
unit's own opening:

    verse_sid: "${window_result.pericopes[-1].opening_verse_sid}"

In a non-final window the last logical unit is untrustworthy — the physical cut may have
truncated it — so a consumer discards it and lets the next window re-adjudicate. But if the
model leaves a **gap** (last kept unit closes at X, dropped unit opens at Y, and X..Y is
covered by nothing), a cursor set to Y skips X..Y and no later window ever sees it. Measured
twice in John by the reporting repo: 4:43–4:54 and 16:25–16:33 lost.

The two forms name the same position whenever the model's output has no gaps, which is why
the wrong one survives testing. The rule that holds: **resume from the trailing edge of what
you kept, never from the leading edge of what you dropped.**

**Why this is a shipped defect rather than a doc nit.** `sp init` writes
`LANGUAGE_QUICKREF_DOC` to `docs/llmflow-language-quickref.md` in every project
(`cli_utils.py:1885`), and four of the shipped AI-context documents direct assistants to
that file as the reference for writing pipeline YAML. A consumer copying it inherits the
data loss.

**What these tests do not do.** They cannot verify that a consumer discards the last unit —
that is pipeline-side discipline the engine cannot enforce. They check only that what we
*ship* teaches the safe form and says so.
"""

from __future__ import annotations

import re
from pathlib import Path

from llmflow.cli_utils import LANGUAGE_QUICKREF_DOC

REPO_ROOT = Path(__file__).resolve().parent.parent
LANGUAGE_SPEC = REPO_ROOT / "docs" / "llmflow-language.md"


def _window_section(text: str) -> str:
    """The `type: window` section, up to the next heading of the same level."""
    start = text.index("type: `window`")
    rest = text[start:]
    end = re.search(r"\n#{2,3} ", rest)
    return rest[: end.start()] if end else rest


def test_the_shipped_example_does_not_resume_from_the_dropped_unit():
    """`pericopes[-1]` is the unit being discarded; resuming from it skips any gap.

    The safe form indexes the last *kept* unit and takes its trailing edge.
    """
    section = _window_section(LANGUAGE_QUICKREF_DOC)

    assert "pericopes[-1]" not in section, (
        "the shipped cursor example resumes from the dropped last unit "
        "(`pericopes[-1]`), which silently loses any region the model left uncovered "
        "between the last kept unit and the dropped one. Resume from the trailing edge of "
        "the last kept unit instead."
    )


def test_the_shipped_example_says_the_cursor_is_a_list_index():
    """A domain identifier is the intuitive wrong answer, and costs a debugging session.

    `window.py:276-280` requires a non-negative integer and raises otherwise, so the
    engine is clear; the example was not.
    """
    section = _window_section(LANGUAGE_QUICKREF_DOC).lower()

    assert "index" in section, (
        "the cursor example never says the cursor is a list index into `in:` rather than a "
        "domain identifier such as a verse id"
    )


def test_the_language_spec_explains_physical_versus_logical():
    """The mechanics were in the spec; the semantics were nowhere in it.

    Grepping the spec for `cursor`, `logical`, `physical` or `resume` returned zero hits at
    the time this was reported — so a reader met `stride` in full, and `!window_advance`
    only as a parenthetical "Alternative to", and had no way to learn that a fixed stride
    asserts knowledge they do not have.
    """
    section = _window_section(LANGUAGE_SPEC.read_text(encoding="utf-8"))

    for term in ("physical", "logical", "cursor"):
        assert term in section.lower(), (
            f"docs/llmflow-language.md never mentions '{term}'. The distinction between a "
            "physical window and the logical units found inside it is the reason the cursor "
            "exists, and a field table cannot carry it."
        )


def test_the_language_spec_states_the_discard_obligation():
    """Half the pattern is worse than none.

    Cursor without discard accumulates a unit and re-processes it — duplicates. Discard
    without cursor loses it. Both halves have to appear together wherever either appears.
    """
    section = _window_section(LANGUAGE_SPEC.read_text(encoding="utf-8")).lower()

    assert "discard" in section, (
        "the spec does not tell a reader to discard the last logical unit of a non-final "
        "window. A cursor without that discard produces duplicates; the discard without a "
        "cursor loses content."
    )
