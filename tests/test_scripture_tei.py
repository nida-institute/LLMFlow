"""A `kind: tei` edition read into rows (#200 step 1). Design: plan-scripture-step.md §3.0."""
from pathlib import Path

import pytest

from llmflow.utils.scripture import (
    edition_text,
    parse_passage_ref,
    read_tei_rows,
    tei_book_files,
)

MACULA_TEI = Path("/Users/jonathan/github/Clear/macula-greek/SBLGNT/tei")
MACULA_TSV = Path("/Users/jonathan/github/Clear/macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv")
MARK_TEI = MACULA_TEI / "02-mark.xml"

real_data = pytest.mark.skipif(
    not MACULA_TEI.is_dir() or not MACULA_TSV.is_file(),
    reason="Macula Greek is not on this machine",
)

EDITIONS = {
    "SBLGNT-TSV": {"kind": "tsv", "path": str(MACULA_TSV)},
    "SBLGNT-TEI": {"kind": "tei", "path": str(MACULA_TEI)},
}

#: The two serializations differ in these characters and no others. Which are correct, and
#: whether running text should carry editorial punctuation, is Macula Greek's to settle and is
#: tracked there — not compensated for here. This set is the current state, so the test fails
#: both when a new divergence appears and when a known one is fixed.
KNOWN_DIVERGENCES = {";", ";", "⟦", "⟧", "—", "(", ")", "[", "]"}

AGREEING = ["MRK 1:1", "MRK 1:2", "MRK 1:1-3", "MRK 8:35"]
DIVERGING = ["MRK 2", "MRK 16"]


@real_data
def test_book_files_are_indexed_by_the_code_the_file_declares():
    books = tei_book_files(MACULA_TEI)
    assert books["MRK"].name == "02-mark.xml"
    assert len(books) == 27


def test_a_missing_directory_is_not_an_error(tmp_path):
    assert tei_book_files(tmp_path / "absent") == {}


@real_data
def test_rows_carry_ref_text_and_after():
    rows = read_tei_rows(MARK_TEI, parse_passage_ref("MRK 1:1"))
    assert [r["text"] for r in rows][:3] == ["Ἀρχὴ", "τοῦ", "εὐαγγελίου"]
    assert rows[0]["ref"] == "MRK 1:1!1"
    assert all(set(r) >= {"ref", "text", "after"} for r in rows)


@real_data
def test_punctuation_becomes_the_after_of_the_preceding_word():
    rows = {r["ref"]: r for r in read_tei_rows(MARK_TEI, parse_passage_ref("MRK 1:2"))}
    assert rows["MRK 1:2!7"]["text"] == "προφήτῃ"
    assert rows["MRK 1:2!7"]["after"] == "·"


@real_data
def test_a_word_with_no_punctuation_after_it_takes_a_space():
    assert read_tei_rows(MARK_TEI, parse_passage_ref("MRK 1:1"))[0]["after"] == " "


@real_data
def test_an_apparatus_mark_is_not_text_and_does_not_displace_the_space():
    """`Ἰησοῦ ⸀χριστοῦ.` — the mark precedes the word it annotates."""
    rows = {r["ref"]: r for r in read_tei_rows(MARK_TEI, parse_passage_ref("MRK 1:1"))}
    assert rows["MRK 1:1!4"]["after"] == " "
    assert rows["MRK 1:1!5"]["after"] == "."


@real_data
def test_a_word_ending_in_an_elision_mark_is_still_a_separate_word():
    """The elision mark sits inside the `w` element, and a space follows it as for any word."""
    rows = {r["ref"]: r for r in read_tei_rows(MARK_TEI, parse_passage_ref("MRK 8:35"))}
    assert rows["MRK 8:35!12"]["text"] == "δ’"
    assert rows["MRK 8:35!12"]["after"] == " "


def test_several_punctuation_nodes_after_one_word_accumulate(tmp_path):
    """A full stop followed by an editorial bracket must not lose the full stop."""
    book = tmp_path / "book.xml"
    book.write_text(
        '<div xmlns="http://www.tei-c.org/ns/1.0">'
        '<w ref="MRK 1:1!1">Ἀρχὴ</w><pc>.</pc><pc>⟦</pc>'
        '<w ref="MRK 1:1!2">τοῦ</w>'
        "</div>",
        encoding="utf-8",
    )
    rows = read_tei_rows(book, parse_passage_ref("MRK 1:1"))
    assert rows[0]["after"] == ".⟦"


@real_data
def test_a_whole_chapter_and_a_whole_book_are_addressable():
    chapter = read_tei_rows(MARK_TEI, parse_passage_ref("MRK 1"))
    book = read_tei_rows(MARK_TEI, parse_passage_ref("MRK"))
    assert len(chapter) < len(book) == 11286


@real_data
@pytest.mark.parametrize("passage", AGREEING)
@pytest.mark.parametrize("fmt", ["plain", "milestones"])
def test_tei_matches_the_tsv_backend(passage, fmt):
    """The TSV backend is tested and in use, so agreement is evidence, not restatement."""
    assert (edition_text("SBLGNT-TEI", passage, fmt=fmt, editions=EDITIONS)
            == edition_text("SBLGNT-TSV", passage, fmt=fmt, editions=EDITIONS))


@real_data
@pytest.mark.parametrize("passage", AGREEING + DIVERGING)
def test_divergence_from_the_tsv_is_only_in_the_known_characters(passage):
    import difflib

    tsv = edition_text("SBLGNT-TSV", passage, fmt="plain", editions=EDITIONS)
    tei = edition_text("SBLGNT-TEI", passage, fmt="plain", editions=EDITIONS)
    def significant(text: str) -> set[str]:
        return {c for c in text if not c.isspace()}

    unexpected = [
        (tag, tsv[i1:i2], tei[j1:j2])
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, tsv, tei).get_opcodes()
        if tag != "equal"
        and not (significant(tsv[i1:i2]) | significant(tei[j1:j2])) <= KNOWN_DIVERGENCES
    ]
    assert not unexpected


@real_data
def test_a_passage_the_edition_does_not_cover_errors_rather_than_returning_empty():
    with pytest.raises(ValueError, match="No text found"):
        edition_text("SBLGNT-TEI", "GEN 1:1", editions=EDITIONS)


@real_data
def test_an_unknown_book_code_errors():
    with pytest.raises(ValueError, match="No text found"):
        edition_text("SBLGNT-TEI", "XYZ 1:1", editions=EDITIONS)


def test_a_tei_edition_needs_a_path():
    with pytest.raises(ValueError, match="needs a 'path'"):
        edition_text("broken", "MRK 1:1", editions={"broken": {"kind": "tei"}})
