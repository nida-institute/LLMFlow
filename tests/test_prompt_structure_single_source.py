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

import re
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


def _refused_names() -> dict[str, str]:
    """The refused headings as bare names, read from the declaration.

    The declaration keys them with their `#` prefix, because that is how a prompt carries
    one. A document can *name* a refused heading without carrying it, and matching on the
    prefix misses that: the worked example read `✅ Has OUTPUT FORMAT (line 32-107)` and this
    guard stayed green. Naming one in an approving example is the more dangerous of the two,
    because it models the verdict as well as the shape.

    Read rather than restated. A hand-kept copy of this set had already drifted from
    `data/prompt-structure.yaml` in a key and in a reason's wording within a week of being
    written — the same defect this module exists to catch, one layer down.
    """
    from llmflow import prompt_structure

    return {name.lstrip("#").strip(): why for name, why in prompt_structure.refused().items()}


#: Headings a prompt written to the old skill text would carry, each refused by the grammar.
#: Named individually so a failure says which trap is still set (design §5).
REFUSED = _refused_names()


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
        "produces a prompt the ruling refuses, and /audit-prompts then passes it. This holds "
        "for naming the heading as well as carrying it, so a report rejecting one says what "
        "the grammar refuses rather than quoting it."
    )


def _fenced_blocks(text: str) -> list[tuple[int, list[str]]]:
    """Every ``` fenced block, as (first line number, lines).

    The worked examples are fenced, so this is what "check the examples" can read. It is the
    one derivation step in this module, and `rule check-the-source-not-the-rendering` applies
    to it: the caller asserts the result is non-empty, so the guard cannot quietly reduce to
    nothing if the skill's formatting changes.
    """
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] | None = None
    start = 0
    for number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("```"):
            if current is None:
                current, start = [], number
            else:
                blocks.append((start, current))
                current = None
        elif current is not None:
            current.append(line)
    return blocks


def _inside_a_longer_caps_phrase(line: str, match: re.Match[str]) -> bool:
    """True where the match is one word of a longer capitalised phrase.

    `AI-GENERATED EXAMPLES DETECTED` is a finding's label, not a reference to the `EXAMPLES`
    section, and reading it as one made this guard report an order the example never stated.
    A heading named in a report is followed and preceded by ordinary prose.
    """
    before = line[: match.start()].split()
    after = line[match.end() :].split()
    neighbours = ([before[-1]] if before else []) + ([after[0]] if after else [])
    return any(len(word) > 1 and word.isupper() for word in neighbours)


def _declared_order() -> dict[str, int]:
    """Bare heading name -> declared position number, from the grammar."""
    from llmflow import prompt_structure

    return {
        heading.lstrip("#").strip(): position.n
        for position in prompt_structure.positions()
        for heading in position.headings
    }


def test_an_example_never_exhibits_an_order_the_grammar_refuses():
    """A worked example instantiates the order, so it states one whether it means to or not.

    The example that prompted this ticked the sections of a compliant prompt in the
    superseded order, with line numbers and a ✅ against each — so it modelled the verdict as
    well as the shape, which is worse than prose restating the order. Checked against the
    declaration rather than a copy of it: the expectations here are the grammar's.
    """
    text = (_repo() / SKILL).read_text(encoding="utf-8")
    blocks = _fenced_blocks(text)
    assert blocks, (
        f"{SKILL} has no fenced blocks, so this guard checked nothing. The examples moved or "
        "the fencing changed; fix the scan rather than deleting the check."
    )

    declared = _declared_order()
    assert declared, "the grammar declares no headings; this guard would check nothing"

    offences: list[str] = []
    for start, lines in blocks:
        seen: list[tuple[int, str, int]] = []
        for offset, line in enumerate(lines):
            found = [
                (match.start(), name, position)
                for name, position in declared.items()
                for match in re.finditer(rf"\b{re.escape(name)}\b", line)
                if not _inside_a_longer_caps_phrase(line, match)
            ]
            seen += [(start + offset + 1, name, position) for _, name, position in sorted(found)]
        for (_, earlier, earlier_n), (number, later, later_n) in zip(seen, seen[1:]):
            if later_n < earlier_n:
                offences.append(
                    f"{SKILL}:{number}: {later!r} (position {later_n}) follows {earlier!r} (position {earlier_n})"
                )
    assert not offences, (
        "an example names the declared sections out of order, so a reader copying it drafts "
        "what the grammar refuses:\n  " + "\n  ".join(offences)
    )


def test_the_skill_points_at_the_discipline_rather_than_restating_it():
    text = (_repo() / SKILL).read_text(encoding="utf-8")
    assert "llmflow-prompt-organization.md" in text, f"{SKILL} must name the discipline as the authority for the order"


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
