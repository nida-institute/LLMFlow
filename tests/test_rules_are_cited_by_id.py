"""Guardrail: a rule is cited by its id, never by its position in the list.

`data/ai-rules.yaml` renders as an ordered list, so every rule has a number — and a number is
not an identity. Removing one rule renumbers every rule after it, silently repointing every
citation already written. The `id` field exists to be the stable handle; these tests make it
the only one that works.

The header of `data/ai-rules.yaml` said "Cite this, not the number" for months while nine
numeric citations accumulated, because a documented convention with nothing enforcing it is a
preference. This file is the enforcement.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from llmflow.ai_rules import entries

REPO_ROOT = Path(__file__).resolve().parent.parent
SCANNED_DIRS = ("docs", "project", "src/llmflow", "tests", "tools")
SCANNED_ROOT_FILES = ("CLAUDE.md", "README.md", "CHANGELOG.md")
SUFFIXES = (".md", ".py", ".yaml", ".yml")

#: Dated record, not live reference. A changelog entry and a plan describe what was true when
#: they were written; rewriting either to match today's numbering would falsify the record.
#: Exempt by path rather than by pattern, so the exemption is a decision and not an accident
#: of which directories happen to be scanned.
EXEMPT = (
    "CHANGELOG.md",
    "project/plans/",
    # Its "Rule 1 … Rule 4" is a local list about prompt frontmatter, unrelated to the AI
    # rules. Matching it would teach the next reader that the guard cries wolf.
    "docs/design/optional-parameters.md",
    # This file must name the forbidden pattern in order to forbid it.
    "tests/test_rules_are_cited_by_id.py",
)

#: `rule 29`, `rules 12`, `Rule #7` — a citation by position.
BY_NUMBER = re.compile(r"\brules?\s+#?\d+\b", re.IGNORECASE)

#: `docs/ai-context/project/rules.md` is a second list: hand-written, created once by `sp init`,
#: never generated, and carrying no ids. A citation of it is allowed on the condition that it
#: names the file. This repository has two numbered lists, so an *unqualified* number is the
#: defect — it does not say which list it indexes.
QUALIFIED = re.compile(r"project/rules\.md")

#: A citation and the filename qualifying it are often on adjacent lines, since prose wraps.
QUALIFIER_WINDOW = 1

#: A backticked kebab-case slug, matched only when it is the *entire* backticked span. That
#: exclusion is what keeps `ai-rules.yaml` and `docs/ai-context/` from matching: a filename
#: carries a dot and a path carries a slash, so neither is a bare slug.
SLUG = re.compile(r"`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`")

#: The explicit form: the word "rule" introducing the id. Anything looser would have to treat
#: every kebab-case identifier in the repository as a rule name and be silenced with an
#: allow-list, which is the maintenance burden the id was meant to remove.
CITATION = re.compile(r"\brules?\s+" + SLUG.pattern, re.IGNORECASE)

#: The other form, used where the sentence names the source instead of saying "rule" — as in
#: "Reported by `some-id` in `data/ai-rules.yaml`". On such a line every bare slug is an id.
NAMES_THE_RULES_FILE = re.compile(r"ai-rules\.yaml")


def rule_ids() -> frozenset[str]:
    return frozenset(entry["id"] for entry in entries())


def scanned_files() -> list[Path]:
    found = []
    for directory in SCANNED_DIRS:
        for path in sorted((REPO_ROOT / directory).rglob("*")):
            if path.is_file() and path.suffix in SUFFIXES:
                found.append(path)
    for name in SCANNED_ROOT_FILES:
        path = REPO_ROOT / name
        if path.is_file():
            found.append(path)
    return [p for p in found if not p.relative_to(REPO_ROOT).as_posix().startswith(EXEMPT)]


def _numbered_citations(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    found = []
    for index, line in enumerate(lines):
        window = "\n".join(lines[max(0, index - QUALIFIER_WINDOW): index + QUALIFIER_WINDOW + 1])
        if QUALIFIED.search(window):
            continue
        for match in BY_NUMBER.finditer(line):
            found.append(
                f"{path.relative_to(REPO_ROOT)}:{index + 1}: {match.group()!r} "
                f"— {line.strip()[:90]}"
            )
    return found


def _unresolved_citations(path: Path, known: frozenset[str]) -> list[str]:
    found = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        matches = CITATION.finditer(line)
        if NAMES_THE_RULES_FILE.search(line):
            matches = SLUG.finditer(line)
        for match in matches:
            slug = match.group(1)
            if slug not in known:
                found.append(
                    f"{path.relative_to(REPO_ROOT)}:{number}: `{slug}` is not a rule id "
                    f"— {line.strip()[:90]}"
                )
    return found


@pytest.mark.parametrize("path", scanned_files(), ids=lambda p: p.name)
def test_rules_are_cited_by_id(path: Path):
    offences = _numbered_citations(path)
    assert not offences, (
        "A rule is cited by its id, not its number. Removing or collapsing a rule renumbers "
        "every rule after it, and every citation by number then points somewhere else. The "
        "ids are in `data/ai-rules.yaml`.\n  " + "\n  ".join(offences)
    )


def test_every_cited_id_resolves():
    """A citation of a rule that has been renamed or removed must fail loudly.

    This is the failure the id was introduced to prevent and, until now, did not: an id that
    no longer exists reads exactly like one that does.
    """
    known = rule_ids()
    offences = [
        offence for path in scanned_files() for offence in _unresolved_citations(path, known)
    ]
    assert not offences, "\n  ".join(["Cited rule ids that do not exist:", *offences])


def test_the_ids_are_unique():
    """Two rules sharing an id would make a citation ambiguous, which is what numbers were."""
    ids = [entry["id"] for entry in entries()]
    duplicates = sorted({name for name in ids if ids.count(name) > 1})
    assert not duplicates, f"Duplicate rule ids: {duplicates}"


def test_every_rule_has_an_id():
    """An id-less rule can only be cited by number, which is the practice being removed."""
    missing = [
        index for index, entry in enumerate(entries(), 1) if not (entry.get("id") or "").strip()
    ]
    assert not missing, f"Rules without an id, by position: {missing}"
