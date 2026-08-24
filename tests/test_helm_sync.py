"""The shared set must not diverge from Human at the Helm without a ruling.

Plan: `project/plans/design-helm-parity.md` §7 step 6, ruling H3-B — *"a sync script …
run deliberately, with a test that fails when the two sides diverge unexpectedly."*

`test_portable_skills.py` and `test_portable_disciplines.py` make the *classification*
falsifiable: which skills and disciplines are shared at all. Neither of them looks at what
Human at the Helm actually contains, so both pass while the two copies say different
things. That is the drift this file exists to catch (§2 of the plan: the copies had already
diverged, with nothing watching them).

Two halves, ruled D7-C:

1. **The record** — `data/helm-sync.yaml` holds one entry per shared file with its hash and
   either `identical` or the ruling that permits it to differ. These tests run everywhere,
   including CI, where no clone of Helm exists. Editing a shared file in this repo without
   re-running `tools/sync_helm.py` fails the build, so divergence arrives as a reviewable
   diff rather than as a machine-local surprise.
2. **The live comparison** — when a clone is present, the same entries are checked against
   Helm's actual files. This is what catches an edit made over there. It skips when the
   clone is absent, which is why half 1 is not optional.

**What the record is not.** It is not a second list of what is shared. The shared set is
derived here from the classification constants in the two portable-guard modules, and the
record is asserted to cover exactly that — so a record that disagrees with the shipped set
fails rather than silently becoming the truth. A hand-kept list disagreeing with what the
package contains is how three disciplines went unshipped for months (#204).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest
import yaml

from tests.test_portable_disciplines import (
    SHARED_WITH_HELM as SHARED_DISCIPLINES,
)
from tests.test_portable_skills import ENGINE_VOCABULARY, _offenders
from tests.test_portable_skills import (
    FORKED as FORKED_SKILLS,
)
from tests.test_portable_skills import (
    SHARED_WITH_HELM as SHARED_SKILLS,
)

# `sp-root/` ships one file today and it is shared. Classified explicitly rather than
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
        "skills": "sp-skills/{name}/SKILL.md",
        "disciplines": "sp-disciplines/{name}",
        "root": "sp-root/{name}",
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


RECORD = _record_entries()
NEEDS_CLONE = pytest.mark.skipif(
    _helm_root() is None,
    reason=(
        f"no Human at the Helm clone found — set ${HELM_ENV_VAR} to run the live half. "
        "The recorded half above still ran."
    ),
)


# ---------------------------------------------------------------------------
# The record — runs everywhere, including CI
# ---------------------------------------------------------------------------


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
        "Run `hatch run python tools/sync_helm.py` to see what differs, then "
        "`--apply` to copy it to Helm and refresh the record."
    )


@pytest.mark.parametrize("key", sorted(RECORD))
def test_every_divergence_carries_a_ruling(key: str):
    """A file allowed to differ must say who allowed it and why.

    Without this the record degrades into a list of exceptions, and the next session cannot
    tell a ruling from an accident. `commit-ready` differing is a decision; a shared skill
    quietly differing is the bug.
    """
    entry = RECORD[key]
    assert entry["status"] in {"identical", "differs"}, (
        f"{key} has status {entry['status']!r}; expected 'identical' or 'differs'"
    )

    if entry["status"] == "identical":
        return

    ruling = (entry.get("ruling") or "").strip()
    assert ruling, (
        f"{key} is recorded as differing from Helm with no ruling. Either it is drift — "
        "sync it — or a decision was taken and its words belong here."
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
    """§8: `drift-patterns.md` byte-identical, or the `sp-root/` vendoring starts drifting.

    This is the one file with no permission to differ, so it is pinned by name rather than
    left to the generic rule above.
    """
    assert "root/drift-patterns.md" in RECORD, "drift-patterns.md is not recorded at all"
    entry = RECORD["root/drift-patterns.md"]
    assert entry["status"] == "identical", (
        "drift-patterns.md is recorded as differing from Helm. Plan §8 requires it to be "
        "byte-identical both sides — this is the exact failure the parity work exists to "
        "end, and it is not a divergence a ruling can permit."
    )


# ---------------------------------------------------------------------------
# The live comparison — only where a clone exists
# ---------------------------------------------------------------------------


def _target_path(entry: dict, helm: Path) -> Path:
    layout = {
        "skills": "skills/{name}/SKILL.md",
        "disciplines": "disciplines/{name}",
        "root": "{name}",
    }
    return helm / layout[entry["set"]].format(name=entry["name"])


@NEEDS_CLONE
@pytest.mark.parametrize("key", sorted(RECORD))
def test_the_shared_file_is_present_in_helm(key: str):
    """A recorded file missing over there is the silent failure `/helm-check` was built for."""
    target = _target_path(RECORD[key], _helm_root())
    assert target.is_file(), f"{key} is recorded as shared but absent from Helm at {target}"


@NEEDS_CLONE
@pytest.mark.parametrize("key", sorted(RECORD))
def test_the_two_sides_agree_where_the_record_says_they_do(key: str):
    """`identical` must mean identical in fact, not in intention."""
    entry = RECORD[key]
    if entry["status"] != "identical":
        return

    source, target = _source_path(entry), _target_path(entry, _helm_root())
    assert _sha256(target) == _sha256(source), (
        f"{key} is recorded as identical but the two copies differ.\n"
        f"  this repo: {source}\n"
        f"  Helm:      {target}\n"
        "Run tools/sync_helm.py to see the difference. If the difference is deliberate, it "
        "needs a ruling in the record; if not, --apply copies this repo's copy over."
    )


@NEEDS_CLONE
@pytest.mark.parametrize("key", sorted(RECORD))
def test_a_recorded_divergence_still_diverges(key: str):
    """A stale exception is as bad as an unrecorded one.

    If the two copies have become identical, the ruling that permitted the difference has
    been overtaken and should be removed rather than left standing as a licence.
    """
    entry = RECORD[key]
    if entry["status"] != "differs":
        return

    source, target = _source_path(entry), _target_path(entry, _helm_root())
    assert _sha256(target) != _sha256(source), (
        f"{key} is recorded as deliberately differing, but the two copies are now "
        "identical. Drop the entry's ruling and record it as identical."
    )


@NEEDS_CLONE
@pytest.mark.parametrize("key", sorted(RECORD))
def test_a_divergent_copy_in_helm_still_carries_no_engine_vocabulary(key: str):
    """A permitted difference is not a licence to ship `sp` vocabulary to a mentee.

    `commit-ready` differs precisely because this repo's copy names `gui/frontend`,
    `pytest.ini` and the Logger rule. The guard that matters is that Helm's copy names
    none of it — and only the live half can check the file that actually shipped.
    """
    entry = RECORD[key]
    if entry["status"] != "differs":
        return

    target = _target_path(entry, _helm_root())
    offenders = _offenders(target.read_text(encoding="utf-8"), ENGINE_VOCABULARY)
    assert not offenders, (
        f"Helm's copy of {key} names this engine:\n  " + "\n  ".join(offenders)
    )


@NEEDS_CLONE
def test_helm_ships_nothing_the_record_cannot_explain():
    """Helm's own material is listed; anything else is unexplained.

    Helm is not a mirror — it has skills and essays of its own (`helm-check`, and the five
    essays its README calls the disciplines proper). Those are declared in the record's
    `helm_only` section. A file in neither section is one nobody has classified, which is
    the state this whole plan was called in to fix.
    """
    helm = _helm_root()
    record = _load_record()

    present = {
        f"skills/{p.name}" for p in (helm / "skills").iterdir() if (p / "SKILL.md").is_file()
    } | {f"disciplines/{p.name}" for p in (helm / "disciplines").glob("*.md")}

    accounted = set(RECORD) | {e["path"] for e in (record.get("helm_only") or ())}

    assert present <= accounted, (
        "Helm ships files the record does not explain: "
        f"{sorted(present - accounted)}\n"
        "Either they are shared — record them — or they are Helm's own, and belong in the "
        "record's helm_only section with a line saying what they are."
    )
