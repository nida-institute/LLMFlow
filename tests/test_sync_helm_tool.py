"""`tools/sync_helm.py` reports on Human at the Helm and never writes its shared files.

Design: `project/plans/design-helm-coordination.md` (#271). A shared file changes in one
repository per act: a change here is recorded as `pending`, and Helm adopts it in its own
commit, from a note this script leaves in Helm's `collab/scripture-pipelines/` — the one
place in that tree a session here may write.

Each test builds a throwaway Helm clone as a git repository, because the script reads
committed state on both sides.
"""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_TOOL = REPO_ROOT / "tools" / "sync_helm.py"
_spec = importlib.util.spec_from_file_location("sync_helm", _TOOL)
sync_helm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_helm)

TODAY = "2026-10-14"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def helm(tmp_path: Path) -> Path:
    """A Helm clone with one committed shared discipline."""
    root = tmp_path / "helm"
    (root / "disciplines").mkdir(parents=True)
    (root / "manifest.yaml").write_text("files: []\n", encoding="utf-8")
    (root / "disciplines" / "workflow.md").write_text("committed\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "initial")
    return root


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


def _entry(status: str = "identical", sha: str = "a" * 64, **extra) -> dict:
    return {"set": "disciplines", "name": "workflow.md", "sha256": sha, "status": status, **extra}


# ---------------------------------------------------------------------------
# Refreshing the record — the one act a change here needs
# ---------------------------------------------------------------------------


def test_an_unchanged_file_keeps_its_entry():
    prior = _entry()
    assert sync_helm.refreshed(prior, prior["sha256"], TODAY) == prior


def test_a_changed_identical_file_becomes_pending_on_helm():
    entry = sync_helm.refreshed(_entry(), "b" * 64, TODAY)
    assert entry["sha256"] == "b" * 64
    assert entry["status"] == "pending"
    assert entry["owner"] == "helm"
    assert entry["since"] == TODAY
    # Left empty on purpose: the record test refuses it until someone says why Helm should adopt it.
    assert entry["note"] == ""


def test_a_changed_ruled_file_keeps_its_ruling():
    prior = _entry("differs", ruling="the Captain's words")
    entry = sync_helm.refreshed(prior, "b" * 64, TODAY)
    assert entry["status"] == "differs"
    assert entry["ruling"] == "the Captain's words"
    assert entry["sha256"] == "b" * 64


def test_a_pending_file_changed_again_keeps_its_date_and_note():
    prior = _entry("pending", owner="helm", since="2026-10-07", note="why")
    entry = sync_helm.refreshed(prior, "b" * 64, TODAY)
    assert (entry["status"], entry["since"], entry["note"]) == ("pending", "2026-10-07", "why")


def test_a_newly_shared_file_is_pending_on_helm():
    entry = sync_helm.refreshed(None, "b" * 64, TODAY, key="disciplines/workflow.md")
    assert (entry["set"], entry["name"]) == ("disciplines", "workflow.md")
    assert (entry["status"], entry["owner"], entry["since"]) == ("pending", "helm", TODAY)


def test_a_pending_file_helm_has_adopted_becomes_identical():
    prior = _entry("pending", owner="helm", since="2026-10-07", note="why")
    entry = sync_helm.refreshed(prior, prior["sha256"], TODAY, helm_sha=prior["sha256"])
    assert entry == _entry()


# ---------------------------------------------------------------------------
# Reading committed state
# ---------------------------------------------------------------------------


def test_the_committed_copy_is_read_not_the_working_tree(helm: Path):
    (helm / "disciplines" / "workflow.md").write_text("uncommitted\n", encoding="utf-8")
    assert sync_helm.committed_sha256(helm, "disciplines/workflow.md") == _sha("committed\n")


def test_an_uncommitted_change_is_named(helm: Path):
    assert not sync_helm.is_dirty(helm, "disciplines/workflow.md")
    (helm / "disciplines" / "workflow.md").write_text("uncommitted\n", encoding="utf-8")
    assert sync_helm.is_dirty(helm, "disciplines/workflow.md")


def test_a_path_helm_has_never_committed_has_no_hash(helm: Path):
    assert sync_helm.committed_sha256(helm, "disciplines/absent.md") is None


# ---------------------------------------------------------------------------
# The report — what Helm owes, never a failure here
# ---------------------------------------------------------------------------


def _verdict(entry: dict, ours: str, helm: Path) -> str:
    return sync_helm.verdict(entry, ours, helm)


def test_matching_committed_copies_are_the_same(helm: Path):
    ours = _sha("committed\n")
    assert _verdict(_entry(sha=ours), ours, helm) == "same"


def test_helm_changing_a_shared_file_is_helms_divergence(helm: Path):
    """D-C: this repository is upstream, so Helm differing with no ruling is Helm's to fix."""
    ours = _sha("upstream\n")
    assert _verdict(_entry(sha=ours), ours, helm) == "HELM DIVERGED"


def test_a_pending_file_is_reported_as_pending(helm: Path):
    ours = _sha("upstream\n")
    entry = _entry("pending", sha=ours, owner="helm", since="2026-10-07", note="why")
    assert _verdict(entry, ours, helm) == "pending"


def test_a_pending_file_helm_has_adopted_is_reported_as_adopted(helm: Path):
    ours = _sha("committed\n")
    entry = _entry("pending", sha=ours, owner="helm", since="2026-10-07", note="why")
    assert _verdict(entry, ours, helm) == "adopted"


def test_a_dirty_copy_in_helm_is_never_called_same(helm: Path):
    ours = _sha("committed\n")
    (helm / "disciplines" / "workflow.md").write_text("uncommitted\n", encoding="utf-8")
    assert _verdict(_entry(sha=ours), ours, helm) == "uncommitted in Helm"


def test_a_file_helm_lacks_is_missing(helm: Path):
    entry = {"set": "disciplines", "name": "absent.md", "sha256": "a" * 64, "status": "identical"}
    assert sync_helm.verdict(entry, "a" * 64, helm) == "MISSING"


# ---------------------------------------------------------------------------
# Writing — only a note, only into Helm's collab directory
# ---------------------------------------------------------------------------


def test_a_note_is_the_only_thing_written(helm: Path):
    before = _snapshot(helm)
    entry = _entry("pending", sha=_sha("upstream\n"), owner="helm", since="2026-10-07",
                   note="the workshop collab's rulings")

    written = sync_helm.write_notes([(entry, "upstream\n")], helm, TODAY)

    after = _snapshot(helm)
    added = set(after) - set(before)
    assert {k: v for k, v in after.items() if k in before} == before, "an existing file changed"
    assert added == {str(p.relative_to(helm)) for p in written}
    assert all(p.parent == helm / "collab" / "scripture-pipelines" for p in written)


def test_a_note_carries_the_reason_and_the_text(helm: Path):
    entry = _entry("pending", sha=_sha("upstream\n"), owner="helm", since="2026-10-07",
                   note="the workshop collab's rulings")
    [note] = sync_helm.write_notes([(entry, "upstream\n")], helm, TODAY)
    text = note.read_text(encoding="utf-8")
    assert "the workshop collab's rulings" in text
    assert "-committed" in text and "+upstream" in text, "the diff against Helm's copy"
    assert "disciplines/workflow.md" in text


def test_only_pending_files_get_a_note(helm: Path):
    assert sync_helm.write_notes([(_entry(), "committed\n")], helm, TODAY) == []


def test_apply_is_gone(helm: Path, monkeypatch: pytest.MonkeyPatch):
    """Pointed at a throwaway clone, as every call to `main` here must be.

    A test of a write refusal runs first against code that does not refuse yet. With the real
    clone in reach, that first run performs the write it was meant to forbid.
    """
    monkeypatch.setenv("HELM_REPO", str(helm))
    before = _snapshot(helm)
    with pytest.raises(SystemExit) as raised:
        sync_helm.main(["--apply"])
    assert raised.value.code == 2
    assert _snapshot(helm) == before


def test_the_report_writes_nothing(helm: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HELM_REPO", str(helm))
    record = sync_helm.RECORD_PATH.read_bytes()
    before = _snapshot(helm)
    assert sync_helm.main([]) == 0
    assert _snapshot(helm) == before
    assert sync_helm.RECORD_PATH.read_bytes() == record
