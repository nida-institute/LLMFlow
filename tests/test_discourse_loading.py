"""Loading LGNTDF citations and turning them into a payload — #200 step 9."""
import collections
from pathlib import Path

import pytest

from llmflow.utils.discourse import (
    FEATURE_KIND,
    NOTE_KIND,
    Outcome,
    load_citations,
    resolve_verse,
)

LGNTDF = Path.home() / "github/biblicalhumanities/levinsohn/LGNTDF"
real_data = pytest.mark.skipif(
    not (LGNTDF / "Main_clauses.xml").is_file(), reason="LGNTDF is not on this machine"
)

FEATURE_XML = """<?xml version="1.0" encoding="utf-8"?>
<feature>
  <header><name>Main clauses</name><type name="propositions"/></header>
  <references>
    <reference osisRef="Mark.1.14!1" type="Main clauses" level="0" verse="Mark 1:14">μετὰ</reference>
    <reference osisRef="Mark.1.14!2" type="Main clauses" level="1" verse="Mark 1:14">δὲ</reference>
  </references>
</feature>
"""

NOTE_XML = """<?xml version="1.0" encoding="utf-8"?>
<feature>
  <header><name>annotations</name><type name="annotations"/></header>
  <references>
    <reference osisRef="Mark.1.14!1" type="note" verse="Mark 1:14">Default position.</reference>
  </references>
</feature>
"""


@pytest.fixture
def corpus(tmp_path) -> Path:
    directory = tmp_path / "LGNTDF"
    directory.mkdir()
    (directory / "Main_clauses.xml").write_text(FEATURE_XML, encoding="utf-8")
    (directory / "Annotations.xml").write_text(NOTE_XML, encoding="utf-8")
    return directory


def rows(*words) -> list:
    return [
        {"ref": f"MRK 1:14!{i}", "xml:id": f"n{i:03d}", "text": w}
        for i, w in enumerate(words, start=1)
    ]


# --- loading --------------------------------------------------------------------------


def test_citations_are_indexed_by_verse(corpus):
    loaded = load_citations(corpus)
    assert set(loaded) == {"MRK 1:14"}
    assert len(loaded["MRK 1:14"]) == 3


def test_a_feature_citation_carries_its_name_level_and_quote(corpus):
    feature = [c for c in load_citations(corpus)["MRK 1:14"] if c.kind == FEATURE_KIND][0]
    assert feature.feature == "Main clauses"
    assert feature.level == 0
    assert feature.text == "μετὰ"
    assert feature.index == 1


def test_a_note_is_a_different_kind_and_keeps_its_prose(corpus):
    """Its text is English commentary, so it is not a quote and cannot be verified."""
    note = [c for c in load_citations(corpus)["MRK 1:14"] if c.kind == NOTE_KIND][0]
    assert note.kind == NOTE_KIND
    assert note.text == "Default position."
    assert note.feature == "annotations"


def test_an_absent_directory_yields_nothing_rather_than_failing(tmp_path):
    assert load_citations(tmp_path / "absent") == {}


def test_a_wrapper_file_is_skipped(corpus):
    """`levinsohn.xml` only xi:includes the others, so reading it would double every citation."""
    (corpus / "levinsohn.xml").write_text("<levinsohn/>", encoding="utf-8")
    assert len(load_citations(corpus)["MRK 1:14"]) == 3


def test_a_dangling_lock_file_is_skipped(corpus):
    """The real corpus carries `.#Thematic_Prominence.xml`, a symlink pointing nowhere.

    Removed before the test ends: a dangling link cannot be stat'd, and the fixture that
    proves tmp_path is disposable would fail on it.
    """
    lock = corpus / ".#Main_clauses.xml"
    lock.symlink_to(corpus / "nowhere.xml")
    try:
        assert len(load_citations(corpus)["MRK 1:14"]) == 3
    finally:
        lock.unlink()


# --- resolving a verse ----------------------------------------------------------------


def test_a_feature_is_resolved_against_the_quote(corpus):
    verse = rows("μετὰ", "δὲ", "τὸ")
    resolved = resolve_verse(load_citations(corpus)["MRK 1:14"], verse)
    features = [r for r in resolved if r["kind"] == FEATURE_KIND]
    assert features[0]["outcome"] == Outcome.VERIFIED.value
    assert features[0]["id"] == "n001"


def test_a_note_bypasses_resolution_and_is_anchored(corpus):
    """532 of 535 notes have a usable index; running them through the resolver would
    manufacture 532 false disagreements and bury the real ones."""
    verse = rows("μετὰ", "δὲ", "τὸ")
    resolved = resolve_verse(load_citations(corpus)["MRK 1:14"], verse)
    note = [r for r in resolved if r["kind"] == NOTE_KIND][0]
    assert note["outcome"] == Outcome.ANCHORED.value
    assert note["id"] == "n001"
    assert note["text"] == "Default position."


def test_a_note_whose_index_is_impossible_is_reported_not_dropped(corpus):
    verse = rows("μετὰ")  # index 1 exists, so use a corpus citation beyond it
    resolved = resolve_verse(
        [c for c in load_citations(corpus)["MRK 1:14"] if c.index == 2], verse
    )
    assert resolved and resolved[0]["id"] is None
    assert resolved[0]["outcome"] != Outcome.VERIFIED.value


def test_a_disagreement_keeps_the_index_and_says_where_the_quote_is(corpus):
    verse = rows("Καὶ", "μετὰ", "τὸ")
    citations = [c for c in load_citations(corpus)["MRK 1:14"] if c.text == "μετὰ"]
    resolved = resolve_verse(citations, verse)
    assert resolved[0]["outcome"] == Outcome.DISAGREES.value
    assert resolved[0]["id"] == "n001", "a usable index is never moved"
    assert resolved[0]["quote_found_at"] == 2


# --- against the real corpus ----------------------------------------------------------


@real_data
def test_the_real_corpus_loads_with_both_kinds():
    loaded = load_citations(LGNTDF)
    kinds = collections.Counter(c.kind for cs in loaded.values() for c in cs)
    assert kinds[FEATURE_KIND] == 51722, "the verifiable citations"
    assert kinds[NOTE_KIND] == 535, "Levinsohn's own annotations"


@real_data
def test_every_feature_name_is_carried():
    loaded = load_citations(LGNTDF)
    names = {c.feature for cs in loaded.values() for c in cs}
    assert len(names) == 33
    assert "Main clauses" in names and "annotations" in names


# --- through the step contract, and §4's warning --------------------------------------


@real_data
def test_discourse_attaches_at_word_ids_through_an_edition():
    from llmflow.utils.scripture import edition_text

    editions = {
        "SBLGNT": {
            "kind": "tsv",
            "path": "/Users/jonathan/github/Clear/macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv",
            "versification_scheme": "org",
            "discourse_path": str(LGNTDF),
        }
    }
    usj = edition_text(
        "SBLGNT", "MRK 1:14", fmt="usj", editions=editions, include=["ids", "discourse"]
    )
    items = usj["scripture_pipelines"]["discourse"]
    assert items, "no discourse items attached"
    ids = {w["srcloc"] for n in usj["content"] if n["type"] == "para"
           for w in n["content"] if isinstance(w, dict) and w.get("marker") == "w"}
    assert {i["id"] for i in items if i["id"]} <= ids, "every item must name a word in the passage"


@real_data
def test_the_documented_trap_keeps_its_index():
    """Mark 1:14 indexes the clause onset and quotes the constituent; the index must not move."""
    from llmflow.utils.scripture import edition_text

    editions = {
        "SBLGNT": {
            "kind": "tsv",
            "path": "/Users/jonathan/github/Clear/macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv",
            "discourse_path": str(LGNTDF),
        }
    }
    usj = edition_text("SBLGNT", "MRK 1:14", fmt="usj", editions=editions, include=["discourse"])
    onset = [
        i for i in usj["scripture_pipelines"]["discourse"]
        if i["feature"] == "Main clauses" and i["index"] == 1
    ]
    assert onset, "the Main clauses citation at index 1 is missing"
    assert onset[0]["outcome"] == "disagrees"
    assert onset[0]["id"] == "n41001014001"
    assert onset[0]["quote_found_at"] == 2


def test_an_edition_with_no_discourse_source_warns_rather_than_failing(tmp_path, caplog):
    """§4: a family the edition has no data for is a warning — Levinsohn is Greek-only."""
    from llmflow.utils.scripture import edition_text

    tsv = tmp_path / "hebrew.tsv"
    tsv.write_text("ref\ttext\tafter\nGEN 1:1!1\tבְּרֵאשִׁית\t \n", encoding="utf-8")
    editions = {"WLC": {"kind": "tsv", "path": str(tsv)}}

    with caplog.at_level("WARNING"):
        usj = edition_text("WLC", "GEN 1:1", fmt="usj", editions=editions, include=["discourse"])
    assert "discourse" in caplog.text.lower()
    assert "discourse" not in usj["scripture_pipelines"]
