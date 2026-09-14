"""`data/alignment-pairs.json` — the declaration of which alignments the engine supports.

R2 in `project/plans/design-scripture-alignments.md` rules that the engine reads its own
declaration rather than `Clear/Alignments/data/catalog.tsv`, which describes a different tree
and arrives as a Git LFS pointer on a fresh clone.

The declaration names files relative to one repository; the datasets store says where that
repository is. These tests hold both halves: that the file itself is well formed, and that a
row resolves to real paths through a registered dataset.
"""
import pytest

from llmflow.steps.alignment import declared_pairs, pairs_path, resolve_pair

REQUIRED_KEYS = {
    "source",
    "target",
    "language",
    "scope",
    "process",
    "alignment_file",
    "source_file",
    "target_file",
}

#: Eighteen of the corpus's twenty-one alignment files. The declaration's own comment names
#: the three that are omitted and the measurement behind each.
EXPECTED_PAIR_COUNT = 18


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """A throwaway `$SP_HOME` registering `clear-alignments` at an empty directory."""
    home = tmp_path / "sp"
    (home / "datasets").mkdir(parents=True)
    root = tmp_path / "corpus"
    root.mkdir()
    (home / "datasets" / "clear-alignments.yaml").write_text(
        f"id: clear-alignments\nname: clear-alignments\npath: {root}\nformat: json\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SP_HOME", str(home))
    return root


# --- the declaration itself ----------------------------------------------------------------

def test_the_declaration_is_readable_where_it_ships():
    assert pairs_path().is_file(), f"no declaration at {pairs_path()}"


def test_the_declaration_names_the_dataset_its_paths_are_relative_to():
    assert declared_pairs()["dataset"] == "clear-alignments"


def test_every_pair_declares_the_keys_the_step_needs():
    missing = {
        f"{p.get('source')}->{p.get('target')}": sorted(REQUIRED_KEYS - set(p))
        for p in declared_pairs()["pairs"]
        if REQUIRED_KEYS - set(p)
    }
    assert not missing, f"pairs missing required keys: {missing}"


def test_no_pair_is_declared_twice():
    seen = [(p["source"], p["target"]) for p in declared_pairs()["pairs"]]
    duplicates = sorted({key for key in seen if seen.count(key) > 1})
    assert not duplicates, f"declared more than once: {duplicates}"


def test_every_declared_pair_is_present():
    assert len(declared_pairs()["pairs"]) == EXPECTED_PAIR_COUNT


def test_no_declared_path_is_absolute():
    """A path in the declaration is relative to the dataset, so it works on any machine."""
    absolute = [
        p[key]
        for p in declared_pairs()["pairs"]
        for key in ("alignment_file", "source_file", "target_file")
        if p[key].startswith("/") or p[key][1:3] == ":\\"
    ]
    assert not absolute, f"absolute paths in the declaration: {absolute}"


# --- resolution through the datasets store -------------------------------------------------

def test_a_declared_pair_resolves_under_the_registered_dataset(corpus):
    resolved = resolve_pair("SBLGNT", "BSB")
    for key in ("alignment_file", "source_file", "target_file"):
        assert str(resolved[key]).startswith(str(corpus)), f"{key} left the dataset: {resolved[key]}"


def test_resolution_keeps_the_relative_path_the_declaration_states(corpus):
    row = next(
        p for p in declared_pairs()["pairs"] if (p["source"], p["target"]) == ("SBLGNT", "BSB")
    )
    assert str(resolve_pair("SBLGNT", "BSB")["alignment_file"]) == str(
        corpus / row["alignment_file"]
    )


def test_an_undeclared_pair_is_refused_naming_what_is_declared(corpus):
    with pytest.raises(ValueError) as caught:
        resolve_pair("SBLGNT", "NOSUCH")
    message = str(caught.value)
    assert "SBLGNT" in message and "NOSUCH" in message
    assert "BSB" in message, "the error should name what is declared, not only what was asked"


def test_an_unregistered_dataset_is_refused_rather_than_guessed(tmp_path, monkeypatch):
    """With nothing registered, resolution must fail loudly rather than invent a root."""
    home = tmp_path / "sp"
    (home / "datasets").mkdir(parents=True)
    monkeypatch.setenv("SP_HOME", str(home))
    with pytest.raises(ValueError) as caught:
        resolve_pair("SBLGNT", "BSB")
    assert "clear-alignments" in str(caught.value)
