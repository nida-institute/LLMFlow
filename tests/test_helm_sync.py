"""The shared set must not diverge from Human at the Helm without a ruling.

Plan: `project/plans/design-helm-parity.md` §7 step 6, ruling H3-B — *"a sync script …
run deliberately, with a test that fails when the two sides diverge unexpectedly."*

`test_portable_skills.py` and `test_portable_disciplines.py` make the *classification*
falsifiable: which skills and disciplines are shared at all. Neither of them looks at what
Human at the Helm actually contains, so both pass while the two copies say different
things. That is the drift this file exists to catch (§2 of the plan: the copies had already
diverged, with nothing watching them).

**These tests check this repository against its own record, and nothing about Helm.**
`data/helm-sync.yaml` holds one entry per shared file with its hash and a status: `identical`,
`differs` with the ruling that permits it, or `pending` — changed here, not yet adopted by
Helm. Editing a shared file here without re-running `tools/sync_helm.py --refresh-record`
fails the build, so a change arrives as a reviewable diff.

**Helm's state is never a failure here** — `failure-lands-where-the-fix-belongs`, and
`project/plans/design-helm-coordination.md` (#271). Whether Helm has adopted a change, kept a
ruled copy free of engine vocabulary, or shipped something unrecorded is what
`tools/sync_helm.py` reports, and what Helm's own check turns red.

**What the record is not.** It is not a second list of what is shared. The shared set is
derived here from the classification constants in the two portable-guard modules, and the
record is asserted to cover exactly that — so a record that disagrees with the shipped set
fails rather than silently becoming the truth. A hand-kept list disagreeing with what the
package contains is how three disciplines went unshipped for months (#204).
"""

from __future__ import annotations

import datetime
import hashlib
import os
from pathlib import Path

import pytest
import yaml

from tests.test_portable_disciplines import (
    SHARED_WITH_HELM as SHARED_DISCIPLINES,
)
from tests.test_portable_skills import (
    FORKED as FORKED_SKILLS,
)
from tests.test_portable_skills import (
    SHARED_WITH_HELM as SHARED_SKILLS,
)

# The sp mirror's root ships one file today and it is shared. Classified explicitly rather than
# globbed, so adding a second root file is a decision somebody takes instead of a file
# that silently starts syncing.
SHARED_ROOT_FILES = ("drift-patterns.md",)

REPO_ROOT = Path(__file__).resolve().parent.parent
RECORD_PATH = REPO_ROOT / "data" / "helm-sync.yaml"

# Where the clone lives, when the record does not say. Defined here rather than in the
# script so the two cannot disagree about it; `$HELM_REPO` is for a clone kept elsewhere.
HELM_ENV_VAR = "HELM_REPO"
DEFAULT_HELM_CLONE = "~/github/nida-institute/human-at-the-helm"


def _templates_dir() -> Path:
    import llmflow

    return Path(llmflow.__file__).parent / "templates"


def _load_record() -> dict:
    """The record, or an empty one when it does not exist yet.

    A missing file fails `test_the_record_covers_exactly_the_shared_set` with a message
    naming what is unrecorded, which is more use than an error during collection.
    """
    if not RECORD_PATH.is_file():
        return {}
    return yaml.safe_load(RECORD_PATH.read_text(encoding="utf-8")) or {}


def _record_entries() -> dict[str, dict]:
    """Entries keyed by `<set>/<name>`, the identity used in failure messages."""
    return {f"{e['set']}/{e['name']}": e for e in (_load_record().get("files") or ())}


def _derived_shared_set() -> set[str]:
    return (
        {f"skills/{name}" for name in SHARED_SKILLS}
        | {f"disciplines/{name}" for name in SHARED_DISCIPLINES}
        | {f"root/{name}" for name in SHARED_ROOT_FILES}
    )


def _source_path(entry: dict) -> Path:
    layout = {
        "skills": "sp/skills/{name}/SKILL.md",
        "disciplines": "sp/disciplines/{name}",
        "root": "sp/{name}",
    }
    return _templates_dir() / layout[entry["set"]].format(name=entry["name"])


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _helm_root() -> Path | None:
    """The clone, or None. Identified by its `manifest.yaml` — that file *is* its installer."""
    configured = os.environ.get(HELM_ENV_VAR) or _load_record().get(
        "helm_clone_default", DEFAULT_HELM_CLONE
    )
    candidate = Path(configured).expanduser()
    return candidate if (candidate / "manifest.yaml").is_file() else None


def _target_path(entry: dict, helm: Path) -> Path:
    layout = {
        "skills": "skills/{name}/SKILL.md",
        "disciplines": "disciplines/{name}",
        "root": "{name}",
    }
    return helm / layout[entry["set"]].format(name=entry["name"])


RECORD = _record_entries()

#: The statuses an entry may carry. `pending` is the normal state between a change here and its
#: adoption in Helm, so it is not a failure.
STATUSES = frozenset({"identical", "differs", "pending"})

#: Whose move a `pending` entry waits on. Only Helm: a change Helm makes and this repository has
#: not is Helm's divergence (D-C), so it is never recorded here as this repository's to adopt.
OWNERS = frozenset({"helm"})


def test_the_record_covers_exactly_the_shared_set():
    """Every shared file is accounted for, and nothing else is.

    Derived from the classification, not restated. A file that becomes shared without an
    entry here would be synced by nobody and watched by nothing.
    """
    assert set(RECORD) == _derived_shared_set(), (
        "data/helm-sync.yaml must hold one entry per shared file.\n"
        f"  shared but unrecorded: {sorted(_derived_shared_set() - set(RECORD))}\n"
        f"  recorded but not shared: {sorted(set(RECORD) - _derived_shared_set())}\n"
        "Re-run tools/sync_helm.py, or record the ruling that explains the difference."
    )


@pytest.mark.parametrize("key", sorted(RECORD))
def test_the_recorded_hash_matches_the_shipped_file(key: str):
    """Editing a shared file here without re-running the script fails the build.

    This is the whole reason the record exists off the Captain's machine: it turns "someone
    changed a shared skill and forgot Helm" into a failing test on CI.
    """
    entry = RECORD[key]
    path = _source_path(entry)
    assert path.is_file(), f"{key} is recorded but no longer shipped at {path}"

    assert _sha256(path) == entry["sha256"], (
        f"{key} has changed since the record was written.\n"
        f"  recorded: {entry['sha256']}\n"
        f"  shipped:  {_sha256(path)}\n"
        "Run `hatch run python tools/sync_helm.py --refresh-record`, then write the "
        "entry's `note`: why Helm should adopt the change."
    )


@pytest.mark.parametrize("key", sorted(RECORD))
def test_every_divergence_carries_a_ruling(key: str):
    """A file allowed to differ must say who allowed it and why.

    Without this the record degrades into a list of exceptions, and the next session cannot
    tell a ruling from an accident. `commit-ready` differing is a decision; a shared skill
    quietly differing is the bug.
    """
    entry = RECORD[key]
    assert entry["status"] in STATUSES, (
        f"{key} has status {entry['status']!r}; expected one of {sorted(STATUSES)}"
    )

    if entry["status"] == "differs":
        ruling = (entry.get("ruling") or "").strip()
        assert ruling, (
            f"{key} is recorded as differing from Helm with no ruling. Either it is a change "
            "Helm has yet to adopt — record it as pending — or a decision was taken and its "
            "words belong here."
        )


@pytest.mark.parametrize("key", sorted(RECORD))
def test_a_pending_change_says_whose_move_since_when_and_why(key: str):
    """`pending` is a promise that someone will act, so it names who, from when, and why.

    `note` is left empty by `--refresh-record` on purpose: it is what Helm's session reads to
    decide how to adopt the change, and only the person who made the change can write it.
    """
    entry = RECORD[key]
    if entry["status"] != "pending":
        return

    assert entry.get("owner") in OWNERS, f"{key}: owner {entry.get('owner')!r}, expected {OWNERS}"
    since = str(entry.get("since") or "")
    assert datetime.date.fromisoformat(since), f"{key}: `since` must be an ISO date, got {since!r}"
    assert (entry.get("note") or "").strip(), (
        f"{key} is pending with no note. Say what changed and why Helm should adopt it — "
        "the note travels to Helm with `tools/sync_helm.py --note`."
    )


@pytest.mark.parametrize("skill", FORKED_SKILLS)
def test_a_forked_skill_is_absent_from_the_record(skill: str):
    """`audit-code` is forked (H4-A): Helm has no counterpart at all.

    Recording it would invite a sync that creates one. Its absence here is the ruling.
    """
    assert f"skills/{skill}" not in RECORD, (
        f"{skill} is forked, not shared — H4-A gives Helm no counterpart. An entry here "
        "would make the script create one."
    )


def test_drift_patterns_must_be_byte_identical():
    """§8: `drift-patterns.md` byte-identical, or the vendoring of the sp mirror's root starts drifting.

    This is the one file with no permission to differ, so it is pinned by name rather than
    left to the generic rule above.
    """
    assert "root/drift-patterns.md" in RECORD, "drift-patterns.md is not recorded at all"
    entry = RECORD["root/drift-patterns.md"]
    assert entry["status"] != "differs", (
        "drift-patterns.md is recorded as differing from Helm. Plan §8 requires it to be "
        "byte-identical both sides — this is the exact failure the parity work exists to "
        "end, and it is not a divergence a ruling can permit. `pending` is allowed: it is "
        "the same text on its way to Helm."
    )
