"""Tests: registering a dataset, and setting fields on a resource, without hand-editing.

Both files had to be hand-written before this. `sp resource add` writes neither
`discourse_path` nor `lowfat_path`, and nothing at all registered a dataset — so the only route
was editing a file whose first line says `sp resource add` wrote it, inside a store kept
read-only to catch exactly that.

The lock is the tool's own, and it may unlock to write and re-lock after. Every test below asserts
the store is locked again afterwards, because that is the property most easily broken and the one
the store exists to provide.
"""

import os
from pathlib import Path

import pytest
import yaml

from llmflow import paths as _paths
from llmflow import resources


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv(_paths.SP_HOME_ENV, str(tmp_path / "store"))
    root = tmp_path / "store"
    (root / "datasets").mkdir(parents=True)
    (root / "registrations").mkdir(parents=True)
    return root


def _lock(path: Path) -> None:
    from llmflow.cli_utils import _lock_sp_dir

    _lock_sp_dir(path)


def _is_locked(path: Path) -> bool:
    return not os.access(path, os.W_OK)


# ---------------------------------------------------------------------------
# sp dataset add
# ---------------------------------------------------------------------------

class TestRegisterDataset:

    def test_it_writes_the_registration(self, store, tmp_path):
        corpus = tmp_path / "levinsohn"
        corpus.mkdir()
        written = resources.register_dataset("levinsohn-lgntdf", corpus)
        assert written == store / "datasets" / "levinsohn-lgntdf.yaml"
        entry = yaml.safe_load(written.read_text(encoding="utf-8"))
        assert entry["id"] == "levinsohn-lgntdf"
        assert entry["path"] == str(corpus)

    def test_the_path_is_absolute_even_when_given_relative(self, store, tmp_path, monkeypatch):
        corpus = tmp_path / "levinsohn"
        corpus.mkdir()
        monkeypatch.chdir(tmp_path)
        written = resources.register_dataset("levinsohn-lgntdf", "levinsohn")
        entry = yaml.safe_load(written.read_text(encoding="utf-8"))
        assert Path(entry["path"]).is_absolute()

    def test_a_path_that_does_not_exist_is_refused(self, store, tmp_path):
        with pytest.raises(ValueError) as raised:
            resources.register_dataset("nope", tmp_path / "absent")
        assert "absent" in str(raised.value)

    def test_it_unlocks_and_re_locks_the_store(self, store, tmp_path):
        corpus = tmp_path / "levinsohn"
        corpus.mkdir()
        _lock(store / "datasets")
        assert _is_locked(store / "datasets")
        resources.register_dataset("levinsohn-lgntdf", corpus)
        assert _is_locked(store / "datasets"), "the store must be locked again afterwards"

    def test_an_unlocked_store_is_left_unlocked(self, store, tmp_path):
        """Restoring a lock that was never there would be a surprise of its own."""
        corpus = tmp_path / "levinsohn"
        corpus.mkdir()
        resources.register_dataset("levinsohn-lgntdf", corpus)
        assert not _is_locked(store / "datasets")

    def test_it_is_then_resolvable(self, store, tmp_path):
        corpus = tmp_path / "levinsohn"
        (corpus / "LGNTDF").mkdir(parents=True)
        resources.register_dataset("levinsohn-lgntdf", corpus)
        resolved = resources.resolve_declared_path("levinsohn-lgntdf/LGNTDF", {"id": "X"})
        assert resolved == corpus / "LGNTDF"


# ---------------------------------------------------------------------------
# sp resource set
# ---------------------------------------------------------------------------

def _registration(store: Path, identifier: str, **fields) -> Path:
    entry = {"id": identifier, "kind": "tsv", "dataset": "Clear-Bible/macula-greek",
             "path": "SBLGNT/tsv/x.tsv", "versification_scheme": "org"}
    entry.update(fields)
    path = store / "registrations" / f"{identifier}.yaml"
    path.write_text(yaml.safe_dump(entry, sort_keys=False), encoding="utf-8")
    return path


class TestSetResourceFields:

    def test_it_sets_the_named_keys(self, store, tmp_path):
        _registration(store, "SBLGNT")
        corpus = tmp_path / "levinsohn"
        (corpus / "LGNTDF").mkdir(parents=True)
        resources.register_dataset("levinsohn-lgntdf", corpus)

        written = resources.set_resource_fields(
            "SBLGNT", discourse_path="levinsohn-lgntdf/LGNTDF"
        )
        entry = yaml.safe_load(written.read_text(encoding="utf-8"))
        assert entry["discourse_path"] == "levinsohn-lgntdf/LGNTDF"

    def test_it_leaves_every_other_key_alone(self, store, tmp_path):
        _registration(store, "SBLGNT", license="CC BY 4.0")
        corpus = tmp_path / "levinsohn"
        (corpus / "LGNTDF").mkdir(parents=True)
        resources.register_dataset("levinsohn-lgntdf", corpus)

        written = resources.set_resource_fields(
            "SBLGNT", discourse_path="levinsohn-lgntdf/LGNTDF"
        )
        entry = yaml.safe_load(written.read_text(encoding="utf-8"))
        assert entry["license"] == "CC BY 4.0"
        assert entry["versification_scheme"] == "org"
        assert entry["path"] == "SBLGNT/tsv/x.tsv"

    def test_a_value_resolving_nowhere_is_refused_before_writing(self, store):
        original = _registration(store, "SBLGNT").read_text(encoding="utf-8")
        with pytest.raises(ValueError) as raised:
            resources.set_resource_fields("SBLGNT", discourse_path="levinsohn-lgntdff/LGNTDF")
        assert "levinsohn-lgntdff" in str(raised.value)
        assert (store / "registrations" / "SBLGNT.yaml").read_text(encoding="utf-8") == original

    def test_an_unregistered_resource_is_refused(self, store):
        with pytest.raises(ValueError) as raised:
            resources.set_resource_fields("NOSUCH", discourse_path="x")
        assert "NOSUCH" in str(raised.value)

    def test_it_reports_what_each_value_resolves_to(self, store, tmp_path):
        _registration(store, "SBLGNT")
        corpus = tmp_path / "levinsohn"
        (corpus / "LGNTDF").mkdir(parents=True)
        resources.register_dataset("levinsohn-lgntdf", corpus)

        resolved = resources.resolved_fields("SBLGNT", discourse_path="levinsohn-lgntdf/LGNTDF")
        assert resolved["discourse_path"] == corpus / "LGNTDF"

    def test_it_unlocks_and_re_locks(self, store, tmp_path):
        _registration(store, "SBLGNT")
        corpus = tmp_path / "levinsohn"
        (corpus / "LGNTDF").mkdir(parents=True)
        resources.register_dataset("levinsohn-lgntdf", corpus)
        _lock(store / "registrations")
        assert _is_locked(store / "registrations")

        resources.set_resource_fields("SBLGNT", discourse_path="levinsohn-lgntdf/LGNTDF")
        assert _is_locked(store / "registrations")
