"""A ticked box in a working document states how it is known.

`- [x] docs updated` is a completion claim, and a claim without evidence is the failure #229
names: *"a report of completion is a factual claim, and making it without having verified it is a
false statement, not optimism."* The usual cause is not deceit but finishing three quarters of
something and losing track.

So a ticked box carries a test id, a path, a command and its result, a count, or a date — anything
a reader can check in one step.

**What this cannot do, stated plainly.** It checks that evidence is *present*, never that it is
*true*. A determined box-ticker defeats it in one line. It is worth having anyway: it converts an
omission from invisible to loud, which is where this failure actually lives.

It is a pattern over our own declared format rather than over prose someone else wrote, which is
why it is not the anti-pattern `check-the-source-not-the-rendering` names — but the limit above is
the same family, and is why the limit is written down rather than discovered later.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PLANS = REPO_ROOT / "project" / "plans"

#: A ticked box, and whatever the author wrote after it.
TICKED = re.compile(r"^\s*[-*]\s*\[x\]\s*(?P<claim>.+?)\s*$", re.IGNORECASE)

#: What counts as evidence a reader can follow in one step.
EVIDENCE = (
    re.compile(r"::"),                              # a test id
    re.compile(r"[\w./-]+\.(py|md|ya?ml|json|gpt)"),  # a file
    re.compile(r"`[^`]+`"),                          # a command, a symbol, a key
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),            # a date the claim was measured
    re.compile(r"\b\d[\d,]*\s*\w"),                  # a count: "5 keys", "7 pipelines"
    re.compile(r"#\d+"),                             # an issue or PR
)

#: Documents written before the rule. The list may shrink and never grow — the same shape as the
#: docstring backlog, so the rule takes effect now and the past is not rewritten to satisfy it.
NOT_YET_CLEAN = frozenset(
    path.name for path in sorted(PLANS.glob("*.md"))
    if path.name not in {"design-one-working-document.md", "README.md"}
)


def _ticked_without_evidence(path: Path) -> list[str]:
    found = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = TICKED.match(line)
        if not match:
            continue
        claim = match.group("claim")
        if not any(pattern.search(claim) for pattern in EVIDENCE):
            found.append(f"{path.name}:{number}: {claim[:90]}")
    return found


def _governed() -> list[Path]:
    return [p for p in sorted(PLANS.glob("*.md")) if p.name not in NOT_YET_CLEAN]


def test_the_scan_reads_something():
    """Absent, every check below would pass by having nothing to read.

    The failure `check-the-source-not-the-rendering` names: a derived set that quietly becomes
    empty, so the assertion passes while checking nothing.
    """
    assert _governed(), "no working documents are governed — the scan is broken, not the suite"


@pytest.mark.parametrize("path", _governed(), ids=lambda p: p.name)
def test_every_ticked_box_carries_evidence(path: Path):
    offences = _ticked_without_evidence(path)
    assert not offences, (
        "A ticked box is a completion claim, and states how it is known — a test id, a file, a "
        "command, a count, a date.\n  " + "\n  ".join(offences)
    )


def test_the_backlog_only_shrinks():
    """A document written before the rule may be excused; a new one may not be added."""
    present = {path.name for path in PLANS.glob("*.md")}
    stale = sorted(NOT_YET_CLEAN - present)
    assert not stale, (
        "These are excused but no longer exist — remove them from NOT_YET_CLEAN:\n  "
        + "\n  ".join(stale)
    )
