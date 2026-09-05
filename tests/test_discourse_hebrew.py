"""Loading a Hebrew discourse corpus — HOTDF-LS alongside LGNTDF.

`include: [discourse]` promises to read the discourse source an edition declares. It could read
only one corpus: LGNTDF, whose files have a `<feature>` root, whose references are written in
OSIS book names, and which sits in one flat directory.

HOTDF-LS — the Hebrew Old Testament discourse features — differs in three ways, none of them
about meaning:

- its roots are `<markup>` and `<annotations>`, so every file was skipped and the payload came
  back empty, indistinguishable from a passage with no data
- its references are already USFM (`LEV.1.14`, `1SA.2.15`), not OSIS (`Lev`, `1Sam`)
- its files sit in subdirectories

The reference-scheme difference needs no configuration: `llmflow.books.resolve` accepts either
spelling and returns the USFM code, because `data/book-names.json` single-sources book names
(#218). The 27-entry OSIS table this module used to carry was a second encoding of that.

Fixtures are in the shape of the real corpus. It is unpublished, so nothing here reads it.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from llmflow.utils.discourse import (
    FEATURE_KIND,
    NOTE_KIND,
    Outcome,
    load_citations,
    parse_osis_ref,
    resolve_verse,
)

# `<markup>` root, USFM references, a span, and a subdirectory — the real corpus's shape.
HEBREW_MARKUP = """<?xml version="1.0" encoding="utf-8" ?>
<markup>
    <header>
        <product version="1.0">Levinsohn/Samuel Hebrew Old Testament Discourse Features</product>
        <name>DFE 2</name>
        <type name="markup" />
    </header>
    <references>
        <reference osisRef="1SA.2.15!14" type="DFE 2" verse="1SA 2:15" >לִצְלוֹת</reference>
        <reference osisRef="LEV.1.14!1-LEV.1.14!3" type="DFE 2" verse="LEV 1:14" >מִן הַתֹּרִים אוֹ</reference>
    </references>
</markup>
"""

HEBREW_ANNOTATIONS = """<?xml version="1.0" encoding="utf-8" ?>
<annotations>
    <header>
        <name>annotations</name>
        <type name="annotations" />
    </header>
    <references>
        <reference osisRef="1SA.2.15!14" type="note" verse="1SA 2:15" >Marked constituent order.</reference>
    </references>
</annotations>
"""


@pytest.fixture
def hebrew_corpus(tmp_path) -> Path:
    root = tmp_path / "HOTDF-LS"
    (root / "Discourse").mkdir(parents=True)
    (root / "Discourse" / "DFE_2.xml").write_text(HEBREW_MARKUP, encoding="utf-8")
    (root / "Discourse" / "Annotations.xml").write_text(HEBREW_ANNOTATIONS, encoding="utf-8")
    return root


def test_a_usfm_reference_parses_without_a_translation_table():
    """`LEV` is already the USFM code; `books.resolve` accepts it and OSIS's `Lev` alike."""
    assert parse_osis_ref("LEV.1.14!8") == ("LEV", 1, 14, 8, None)
    assert parse_osis_ref("1SA.2.15!14") == ("1SA", 2, 15, 14, None)


def test_an_osis_reference_still_parses():
    """The Greek corpus is unaffected — that spelling must keep working."""
    assert parse_osis_ref("Mark.1.14!3") == ("MRK", 1, 14, 3, None)
    assert parse_osis_ref("1Sam.2.15!14") == ("1SA", 2, 15, 14, None)


def test_an_unknown_book_still_raises():
    """A code in neither scheme is refused rather than guessed at."""
    with pytest.raises(ValueError):
        parse_osis_ref("Nonesuch.1.1!1")


def test_a_markup_root_is_read(hebrew_corpus):
    """`<markup>` and `<annotations>`, not only `<feature>` — else every file is skipped."""
    loaded = load_citations(hebrew_corpus)

    assert loaded, "no citations loaded from a Hebrew corpus"
    assert set(loaded) == {"1SA 2:15", "LEV 1:14"}


def test_files_in_subdirectories_are_found(hebrew_corpus):
    """The corpus nests its files; a flat glob found nothing and said nothing."""
    loaded = load_citations(hebrew_corpus)

    assert "LEV 1:14" in loaded


def test_a_hebrew_note_is_a_note(hebrew_corpus):
    """The kind comes from the declared header type, which the Hebrew corpus also carries."""
    citations = load_citations(hebrew_corpus)["1SA 2:15"]

    assert {c.kind for c in citations} == {FEATURE_KIND, NOTE_KIND}


def test_a_hebrew_feature_resolves_against_its_quote(hebrew_corpus):
    """The reconciliation is script-agnostic: it compares the quote with the words."""
    rows = [
        {"xml:id": f"o{i:03d}", "text": word}
        for i, word in enumerate(["מִן", "הַתֹּרִים", "אוֹ", "בְּנֵי"], start=1)
    ]
    citations = [c for c in load_citations(hebrew_corpus)["LEV 1:14"] if c.kind == FEATURE_KIND]

    resolved = resolve_verse(citations, rows)

    assert resolved[0]["outcome"] == Outcome.VERIFIED.value
    assert resolved[0]["id"] == "o001"
