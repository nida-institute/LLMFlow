"""Guardrail: one statement of the prompt section order, and nothing restating it.

`project/plans/design-one-prompt-order.md` §3 rules the order and states it as a grammar.
Several documents then described it and most disagreed with the ruling — reported by
`nida-institute/discourse-flow`, and verified against the files:

- `data/prompt-structure.yaml` — the declaration (new; the only statement)
- `templates/sp/disciplines/llmflow-prompt-organization.md` — an eleven-position pattern
  called "The 8-Section Pattern", with `CORE PRINCIPLES` no prompt has ever carried
- `templates/sp/skills/audit-prompts/SKILL.md` — a third structure naming
  `# OUTPUT FORMAT`, `# CRITICAL REMINDERS` and `## Rules Specific to This Output Type`,
  none of which the grammar admits

The skill is the one that mattered: it is what a session is pointed at, so an agent drafted
to it, then ran `/audit-prompts`, which checked the prompt against the same wrong text and
passed it. The enforcement path certified what the ruling refuses.

These tests are the reason that cannot recur. The order is data; the discipline renders
from it; the skill names neither.
"""

from pathlib import Path

import pytest


def _repo() -> Path:
    return Path(__file__).resolve().parent.parent


DISCIPLINE = "src/llmflow/templates/sp/disciplines/llmflow-prompt-organization.md"

#: The source of the skill. This is the copy under version control, so it is the one every
#: check below must hold.
SKILL = "src/llmflow/templates/sp/skills/audit-prompts/SKILL.md"

#: The installed copy in this repository. `.claude/*` is gitignored here, so it is absent
#: from a fresh clone: `sp init` writes it from the template. Checked when it happens to be
#: present, never required — a test that reads it unconditionally passes locally and fails
#: in CI on a file that was never meant to be committed.
INSTALLED = ".claude/skills/audit-prompts/SKILL.md"

#: Headings a prompt written to the old skill text would carry, each refused by the grammar.
#: Named individually so a failure says which trap is still set (design §5).
REFUSED = {
    "# OUTPUT FORMAT": "the production is `# OUTPUT SCHEMA`",
    "# CRITICAL REMINDERS": "not one of the `quality-controls` alternatives",
    "## Rules Specific to This Output Type": "the task subsection is `## Guardrails`",
    "CORE PRINCIPLES": "removed from the standard — 0 of 5 prompts carried one",
}


def test_the_declaration_exists_and_states_the_order():
    from llmflow import prompt_structure

    positions = prompt_structure.positions()
    assert positions, "the declaration lists no positions; it is the only statement of the order"
    assert [p.n for p in positions] == list(range(1, len(positions) + 1)), (
        "positions must be numbered 1..n without a gap, because the document cites them by number"
    )
    assert prompt_structure.conditions(), "C1-C5 are what the grammar cannot express; none declared"


@pytest.mark.parametrize("heading", sorted(REFUSED))
def test_the_skill_states_no_refused_heading(heading: str):
    """The skill must not teach a structure the grammar rejects.

    Four failures came from one document, none of them the author's fault (design §5).
    """
    text = (_repo() / SKILL).read_text(encoding="utf-8")
    assert heading not in text, (
        f"{SKILL} still names {heading!r} — {REFUSED[heading]}. A session drafting to this "
        "produces a prompt the ruling refuses, and /audit-prompts then passes it."
    )


def test_the_skill_points_at_the_discipline_rather_than_restating_it():
    text = (_repo() / SKILL).read_text(encoding="utf-8")
    assert "llmflow-prompt-organization.md" in text, (
        f"{SKILL} must name the discipline as the authority for the order"
    )


def test_an_installed_copy_has_not_drifted_from_the_template():
    """Where this repository has the skill installed, it must match what ships.

    Skipped rather than failed when absent: `.claude/*` is gitignored here, so a fresh clone
    has none and `sp init` writes it. The check is worth keeping for a working tree, because a
    stale installed copy is what a session in this repository actually reads.
    """
    installed = _repo() / INSTALLED
    if not installed.is_file():
        pytest.skip(f"{INSTALLED} is not installed in this working tree")
    assert installed.read_bytes() == (_repo() / SKILL).read_bytes(), (
        f"{INSTALLED} has drifted from {SKILL}. Run `sp init --update` or `sp doctor` to "
        "refresh it; editing it in place is lost on the next run."
    )


def test_the_discipline_renders_the_declared_order_verbatim():
    from llmflow import prompt_structure

    text = (_repo() / DISCIPLINE).read_text(encoding="utf-8")
    rendered = prompt_structure.render_markdown()
    assert rendered.strip(), "the renderer produced nothing; this guard would check nothing"
    assert rendered in text, (
        "the discipline does not carry the rendered order verbatim, so the prose and the "
        "declaration can disagree. Regenerate it from `data/prompt-structure.yaml`."
    )


def test_no_shipped_document_names_a_section_count():
    """A count in the prose goes stale the moment a position is added or removed.

    "The 8-Section Pattern" headed a list of eleven.
    """
    offences = []
    for path in sorted((_repo() / "src" / "llmflow" / "templates").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            low = line.lower()
            if "8-section" in low or "eight-section" in low or "eight section" in low:
                offences.append(f"{path.relative_to(_repo())}:{number}: {line.strip()[:80]}")
    assert not offences, "a section count is named in shipped prose:\n  " + "\n  ".join(offences)
