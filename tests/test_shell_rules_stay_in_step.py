"""The shell rules exist in two places on purpose, so a tripwire holds them together.

`data/ai-rules.yaml` states them declaratively and ships to every project through the rendered
`docs/ai-context/sp/rules.md`. `disciplines/workflow.md` states them as prose and is shared with
Human at the Helm, which has no rules file of its own — so it keeps its own wording by ruling
rather than pointing at ours.

Two encodings of one fact is normally the defect. It is accepted here because the audiences
differ, and this guard is the price: **when either side changes, the test fails**, and whoever
changed it re-reads the other and updates the hash. Nothing here checks that the two *agree* —
no test can compare prose to a declaration — it only guarantees that nobody changes one and
forgets the other.

That is the failure this exists for. The two wordings had already drifted into contradicting each
other about what the machine does: the discipline said the shell readers "require approval", the
project file said a hook refuses them. The hook refuses them.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RULES = REPO_ROOT / "data" / "ai-rules.yaml"
DISCIPLINE = REPO_ROOT / "src" / "llmflow" / "templates" / "sp" / "disciplines" / "workflow.md"

#: The rules whose subject the discipline also covers in prose.
SHELL_RULE_IDS = (
    "file-tools-for-reading",
    "one-command-at-a-time",
    "inline-code-uses-a-heredoc",
    "git-output-is-not-piped",
    "ask-for-the-exception",
)

#: Update both when either side is deliberately reworded — after re-reading the other.
EXPECTED_RULES_DIGEST = "91baa58d0fae0742"
EXPECTED_DISCIPLINE_DIGEST = "be9fe1b2771ac5e0"


def _digest(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()[:16]


def _rules_text() -> str:
    entries = yaml.safe_load(RULES.read_text(encoding="utf-8"))["rules"]
    by_id = {entry["id"]: entry for entry in entries}
    missing = [rid for rid in SHELL_RULE_IDS if rid not in by_id]
    assert not missing, f"shell rules missing from {RULES.name}: {missing}"
    return "\n".join(by_id[rid]["rule"] for rid in SHELL_RULE_IDS)


def _discipline_section() -> str:
    text = DISCIPLINE.read_text(encoding="utf-8")
    match = re.search(r"^## Shell Commands\n(.*?)(?=^---$|^## )", text, re.S | re.M)
    assert match, f"no '## Shell Commands' section in {DISCIPLINE}"
    return match.group(1)


def test_both_sides_are_non_empty():
    """Absent, the digests below would pin two empty strings and check nothing."""
    assert len(_rules_text()) > 500
    assert len(_discipline_section()) > 500


def test_the_shell_rules_have_not_changed_unnoticed():
    assert _digest(_rules_text()) == EXPECTED_RULES_DIGEST, (
        "The shell rules in data/ai-rules.yaml changed.\n"
        "  Re-read the '## Shell Commands' section of the shared discipline and check the two "
        "still say the same thing, then update EXPECTED_RULES_DIGEST to "
        f"{_digest(_rules_text())!r}.\n"
        "  The discipline is shared with Human at the Helm — a change there needs "
        "`tools/sync_helm.py --apply` and a commit in that repository."
    )


def test_the_shared_discipline_has_not_changed_unnoticed():
    assert _digest(_discipline_section()) == EXPECTED_DISCIPLINE_DIGEST, (
        "The '## Shell Commands' section of the shared discipline changed.\n"
        "  Re-read the shell rules in data/ai-rules.yaml and check the two still say the same "
        f"thing, then update EXPECTED_DISCIPLINE_DIGEST to {_digest(_discipline_section())!r}."
    )
