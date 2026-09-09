"""Tests: `discourse_path` and `lowfat_path` resolve without an absolute path.

`path` has always been resolvable against the store, so a registration means the same thing on
every machine. These two keys reached `Path()` raw, so absolute was the only form that worked —
and a registration therefore contradicted its own header comment.

Three forms are accepted, in this order:

  absolute            honoured unchanged, as `path` honours it
  a registered id     the `path` of that entry in the datasets store
  dataset-relative    resolved against the resource's `dataset`, exactly as `path` is

The order matters for one case only: a bare value that is both a registered dataset id and the
name of a directory inside the resource's dataset resolves as the id, because a declaration beats
a coincidence of naming.
"""

from pathlib import Path

import pytest
import yaml

from llmflow import paths as _paths
from llmflow import resources
from llmflow.utils.scripture import load_registry_resources


@pytest.fixture
def store(tmp_path, monkeypatch):
    """An `$SP_HOME` store, so the datasets directory and the corpora both land in tmp."""
    monkeypatch.setenv(_paths.SP_HOME_ENV, str(tmp_path / "store"))
    (tmp_path / "store" / "datasets").mkdir(parents=True)
    (tmp_path / "store" / "registrations").mkdir(parents=True)
    return tmp_path / "store"


def _register_dataset(store: Path, identifier: str, path: str) -> None:
    (store / "datasets" / f"{identifier}.yaml").write_text(
        yaml.safe_dump({"id": identifier, "name": identifier, "path": path, "format": "xml"}),
        encoding="utf-8",
    )


def _edition(store: Path, identifier: str, **keys) -> None:
    entry = {"id": identifier, "kind": "tsv", "dataset": "Clear-Bible/macula-greek"}
    entry.update(keys)
    (store / "registrations" / f"{identifier}.yaml").write_text(
        yaml.safe_dump(entry), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# The three forms
# ---------------------------------------------------------------------------

class TestPathKeyTakesTheSameForms:
    """`path` resolves the same three ways, so a registration can name clones throughout.

    Until it did, the dataset-relative form obliged the *text* to come from the store — so a
    machine whose corpora are working clones had to keep a redundant download alive purely to
    satisfy `path`, and could not delete it.
    """

    def test_a_dataset_id_with_a_subpath(self, store):
        _register_dataset(store, "macula-greek-lowfat", "/srv/macula-greek")
        definition = {
            "id": "SBLGNT",
            "dataset": "Clear-Bible/macula-greek",
            "path": "macula-greek-lowfat/SBLGNT/tsv/macula-greek-SBLGNT.tsv",
        }
        assert resources.resolve_path(definition) == Path(
            "/srv/macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv"
        )

    def test_a_dataset_relative_value_still_resolves_against_the_store(self, store):
        definition = {
            "id": "SBLGNT",
            "dataset": "Clear-Bible/macula-greek",
            "path": "SBLGNT/tsv/macula-greek-SBLGNT.tsv",
        }
        assert resources.resolve_path(definition) == (
            resources.data_dir()
            / "Clear-Bible/macula-greek"
            / "SBLGNT/tsv/macula-greek-SBLGNT.tsv"
        )

    def test_an_absolute_path_still_wins(self, store):
        definition = {"id": "WLC", "dataset": "Clear-Bible/macula-hebrew", "path": "/srv/x.tsv"}
        assert resources.resolve_path(definition) == Path("/srv/x.tsv")

    def test_a_definition_with_no_path_is_refused(self, store):
        with pytest.raises(ValueError):
            resources.resolve_path({"id": "SBLGNT"})


class TestResolveDeclaredPath:

    def test_an_absolute_value_is_honoured_unchanged(self, store):
        definition = {"id": "SBLGNT", "dataset": "Clear-Bible/macula-greek"}
        resolved = resources.resolve_declared_path("/opt/corpora/LGNTDF", definition)
        assert resolved == Path("/opt/corpora/LGNTDF")

    def test_a_home_relative_value_is_expanded(self, store):
        definition = {"id": "SBLGNT", "dataset": "Clear-Bible/macula-greek"}
        resolved = resources.resolve_declared_path("~/corpora/LGNTDF", definition)
        assert resolved == Path.home() / "corpora/LGNTDF"

    def test_a_dataset_relative_value_resolves_against_the_dataset(self, store):
        definition = {"id": "SBLGNT", "dataset": "Clear-Bible/macula-greek"}
        resolved = resources.resolve_declared_path("SBLGNT/lowfat", definition)
        assert resolved == resources.data_dir() / "Clear-Bible/macula-greek" / "SBLGNT/lowfat"

    def test_a_registered_dataset_id_resolves_through_the_store(self, store):
        _register_dataset(store, "levinsohn-lgntdf", "/srv/levinsohn")
        definition = {"id": "SBLGNT", "dataset": "Clear-Bible/macula-greek"}
        resolved = resources.resolve_declared_path("levinsohn-lgntdf", definition)
        assert resolved == Path("/srv/levinsohn")

    def test_an_unregistered_bare_value_falls_through_to_dataset_relative(self, store):
        definition = {"id": "SBLGNT", "dataset": "Clear-Bible/macula-greek"}
        resolved = resources.resolve_declared_path("lowfat", definition)
        assert resolved == resources.data_dir() / "Clear-Bible/macula-greek" / "lowfat"

    def test_a_declaration_beats_a_coincidence_of_naming(self, store):
        _register_dataset(store, "lowfat", "/srv/somewhere-else")
        definition = {"id": "SBLGNT", "dataset": "Clear-Bible/macula-greek"}
        resolved = resources.resolve_declared_path("lowfat", definition)
        assert resolved == Path("/srv/somewhere-else")

    def test_a_dataset_id_may_carry_a_subpath(self, store):
        # The data rarely sits at a repository root: LGNTDF lives in a subdirectory of the
        # levinsohn clone, and lowfat in a subdirectory of macula-greek.
        _register_dataset(store, "levinsohn-lgntdf", "/srv/levinsohn")
        definition = {"id": "SBLGNT", "dataset": "Clear-Bible/macula-greek"}
        resolved = resources.resolve_declared_path("levinsohn-lgntdf/LGNTDF", definition)
        assert resolved == Path("/srv/levinsohn/LGNTDF")

    def test_a_subpath_may_be_several_segments_deep(self, store):
        _register_dataset(store, "macula-greek-lowfat", "/srv/macula-greek")
        definition = {"id": "SBLGNT", "dataset": "Clear-Bible/macula-greek"}
        resolved = resources.resolve_declared_path(
            "macula-greek-lowfat/SBLGNT/lowfat", definition
        )
        assert resolved == Path("/srv/macula-greek/SBLGNT/lowfat")

    def test_an_unregistered_first_segment_stays_dataset_relative(self, store):
        definition = {"id": "SBLGNT", "dataset": "Clear-Bible/macula-greek"}
        resolved = resources.resolve_declared_path("SBLGNT/lowfat", definition)
        assert resolved == resources.data_dir() / "Clear-Bible/macula-greek" / "SBLGNT/lowfat"

    def test_a_subpath_cannot_escape_its_dataset(self, store):
        _register_dataset(store, "levinsohn-lgntdf", "/srv/levinsohn")
        definition = {"id": "SBLGNT", "dataset": "Clear-Bible/macula-greek"}
        with pytest.raises(ValueError):
            resources.resolve_declared_path("levinsohn-lgntdf/../../etc", definition)

    def test_no_dataset_and_a_relative_value_is_returned_as_written(self, store):
        # Matches `resolve_path`: with nothing to resolve against, the value stands.
        resolved = resources.resolve_declared_path("LGNTDF", {"id": "X"})
        assert resolved == Path("LGNTDF")

    def test_an_empty_value_is_refused(self, store):
        with pytest.raises(ValueError):
            resources.resolve_declared_path("", {"id": "SBLGNT"})


# ---------------------------------------------------------------------------
# The datasets store reader
# ---------------------------------------------------------------------------

class TestDatasetRegistration:

    def test_an_absent_id_is_none(self, store):
        assert resources.dataset_registration("nothing-here") is None

    def test_a_registered_id_returns_its_entry(self, store):
        _register_dataset(store, "gbi-lowfat", "/srv/lowfat")
        entry = resources.dataset_registration("gbi-lowfat")
        assert entry is not None
        assert entry["path"] == "/srv/lowfat"

    def test_reading_never_creates_the_directory(self, tmp_path, monkeypatch):
        """The store is read-only by design, so a lookup must not try to make anything."""
        monkeypatch.setenv(_paths.SP_HOME_ENV, str(tmp_path / "absent-store"))
        assert resources.dataset_registration("anything") is None
        assert not (tmp_path / "absent-store").exists()

    def test_a_path_separator_is_never_a_dataset_id(self, store):
        assert resources.dataset_registration("SBLGNT/lowfat") is None
        assert resources.dataset_registration("../escape") is None


# ---------------------------------------------------------------------------
# Through the loader a pipeline actually goes through
# ---------------------------------------------------------------------------

class TestLoadRegistryEditions:

    def test_both_keys_are_resolved(self, store):
        _register_dataset(store, "levinsohn-lgntdf", "/srv/levinsohn")
        _edition(
            store,
            "SBLGNT",
            path="SBLGNT/tsv/macula-greek-SBLGNT.tsv",
            discourse_path="levinsohn-lgntdf",
            lowfat_path="SBLGNT/lowfat",
        )
        loaded = load_registry_resources(store / "registrations")["SBLGNT"]
        assert loaded["discourse_path"] == "/srv/levinsohn"
        assert loaded["lowfat_path"] == str(
            resources.data_dir() / "Clear-Bible/macula-greek" / "SBLGNT/lowfat"
        )

    def test_the_text_path_still_resolves(self, store):
        _edition(store, "SBLGNT", path="SBLGNT/tsv/macula-greek-SBLGNT.tsv")
        loaded = load_registry_resources(store / "registrations")["SBLGNT"]
        assert loaded["path"] == str(
            resources.data_dir()
            / "Clear-Bible/macula-greek"
            / "SBLGNT/tsv/macula-greek-SBLGNT.tsv"
        )

    def test_an_edition_naming_neither_key_is_untouched(self, store):
        _edition(store, "SBLGNT", path="x.tsv")
        loaded = load_registry_resources(store / "registrations")["SBLGNT"]
        assert "discourse_path" not in loaded
        assert "lowfat_path" not in loaded

    def test_an_absolute_annotation_path_survives(self, store):
        _edition(store, "SBLGNT", path="x.tsv", lowfat_path="/opt/lowfat")
        loaded = load_registry_resources(store / "registrations")["SBLGNT"]
        assert loaded["lowfat_path"] == "/opt/lowfat"
