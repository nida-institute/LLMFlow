"""A quotation is a span of words, and the reference that names it carries both ends.

`OT_quotes.xml` gives every quotation a word-level span — `Mark.1.2!9-Mark.1.2!15`. `OSIS_REF`
had no end-capture, so it matched, consumed `Mark.1.2!9`, and discarded `!15`; `Citation` carried
one `index` and no end, and `resolve_verse` returned one id per item. All 691 quotations therefore
loaded with their opening word and their Greek intact, and their extent gone.

That is correct for a *feature*, which anchors at one word, and wrong for a *quotation*, which is
a span — and both live in the same corpus and pass through the same loader. `discourse-flow`
reported it against their issue #92, having measured 47 quotations in Mark carrying 0 spans, and
having assumed the loss was their own.

The end is optional: a single-word reference has none, and `end_index` stays `None` rather than
repeating the opening. That keeps `id` a scalar for every existing consumer and says which kind
of nothing it means — there is no closing word, as against one that could not be found.
"""

from llmflow.utils.discourse import (
    Citation,
    Outcome,
    OSIS_REF,
    parse_osis_ref,
    resolve_verse,
)

#: Mark 1:2 as Macula Greek holds it — one row per word, ids `BBCCCVVVWWW`.
MARK_1_2 = [
    {"ref": f"MRK 1:2!{n}", "xml:id": f"n4100100200{n}" if n < 10 else f"n410010020{n}",
     "text": text}
    for n, text in enumerate(
        ["Καθὼς", "γέγραπται", "ἐν", "τῷ", "Ἠσαΐᾳ", "τῷ", "προφήτῃ", "Ἰδοὺ",
         "ἀποστέλλω", "τὸν", "ἄγγελόν", "μου", "πρὸ", "προσώπου", "σου"],
        start=1,
    )
]


def test_the_pattern_captures_the_closing_index_of_a_span():
    """`Mark.1.2!9-Mark.1.2!15` names words 9 through 15."""
    match = OSIS_REF.match("Mark.1.2!9-Mark.1.2!15")

    assert match is not None
    assert match.group("index") == "9"
    assert match.group("end_index") == "15", (
        "the closing index was matched and then discarded, so a quotation's extent was lost "
        "before any consumer could see it"
    )


def test_a_single_word_reference_has_no_closing_index():
    """A feature anchors at one word. `end_index` is None, not a repeat of the opening."""
    match = OSIS_REF.match("Mark.1.14!3")

    assert match is not None
    assert match.group("index") == "3"
    assert match.group("end_index") is None


def test_parse_osis_ref_returns_the_span():
    book, chapter, verse, index, end = parse_osis_ref("Mark.1.2!9-Mark.1.2!15")

    assert (book, chapter, verse, index) == ("MRK", 1, 2, 9)
    assert end == ("MRK", 1, 2, 15), "the closing end is a reference, stated in full"


def test_parse_osis_ref_leaves_a_single_word_without_an_end():
    assert parse_osis_ref("Mark.1.14!3") == ("MRK", 1, 14, 3, None)


def test_a_spanning_citation_reports_both_word_ids():
    """The payload carries the closing id beside the opening, so the extent survives."""
    quotation = Citation(
        feature="OT quotes", kind="feature", book="MRK", chapter=1, verse=2,
        index=9, text="ἀποστέλλω τὸν ἄγγελόν μου", end_index=15,
    )
    items = resolve_verse([quotation], MARK_1_2)

    assert len(items) == 1
    item = items[0]
    assert item["id"] == MARK_1_2[8]["xml:id"], "the opening is word 9"
    assert item["id_end"] == MARK_1_2[14]["xml:id"], (
        f"expected the id of word 15, got {item.get('id_end')!r}"
    )


def test_a_single_word_citation_carries_no_closing_id():
    """`say-which-kind-of-nothing`: absent because there is no span, not because none was found."""
    feature = Citation(
        feature="Highlighter", kind="feature", book="MRK", chapter=1, verse=2,
        index=8, text="Ἰδοὺ",
    )
    items = resolve_verse([feature], MARK_1_2)

    assert items[0]["outcome"] == Outcome.VERIFIED.value
    assert "id_end" not in items[0], (
        "a feature anchors at one word, so a closing id would assert a span that does not exist"
    )


def test_a_span_across_verses_keeps_both_ends():
    """657 of LGNTDF's spans close in a later verse, and some cross three.

    An earlier version dropped the closing end here, reasoning that a citation resolves against
    one verse's words — which describes a limit on what the resolver can give an id for, not a
    reason for the citation to forget where it ends.
    """
    book, chapter, verse, index, end = parse_osis_ref("Matt.6.9!5-Matt.6.13!61")

    assert (book, chapter, verse, index) == ("MAT", 6, 9, 5)
    assert end == ("MAT", 6, 13, 61), (
        f"the Lord's Prayer closes at 6:13 word 61; got {end!r}"
    )


def test_a_same_verse_span_reports_its_closing_verse_too():
    """The closing reference is stated in full whether or not it is the opening verse.

    Uniform on purpose: `end` being present means there is a span, and nothing has to read the
    absence of a verse as "the same one".
    """
    assert parse_osis_ref("Mark.1.2!9-Mark.1.2!15")[4] == ("MRK", 1, 2, 15)


def test_a_span_across_three_verses_keeps_its_far_end():
    assert parse_osis_ref("Acts.26.16!14-Acts.26.18!71")[4] == ("ACT", 26, 18, 71)


def test_a_cross_verse_citation_reports_the_closing_reference_even_without_its_id():
    """`resolve_verse` holds one verse's rows, so it cannot address a word in another verse.

    It reports the reference regardless. Withholding it would lose the extent, which is the
    defect this whole change is about; inventing an id from the wrong verse's rows would be
    worse. The id is filled by whoever holds the other verse.
    """
    quotation = Citation(
        feature="OT quotes", kind="feature", book="MRK", chapter=1, verse=2,
        index=9, text="ἀποστέλλω", end_book="MRK", end_chapter=1, end_verse=3, end_index=4,
    )
    item = resolve_verse([quotation], MARK_1_2)[0]

    assert item["end_index"] == 4
    assert item["end_verse"] == 3, "the closing verse must be reported"
    assert "id_end" not in item, (
        "word 4 of verse 3 is not in this verse's rows, so no id can be given for it"
    )


def test_a_closing_index_past_the_verse_is_reported_not_invented():
    """Word 99 of a 15-word verse does not exist; the opening still resolves."""
    quotation = Citation(
        feature="OT quotes", kind="feature", book="MRK", chapter=1, verse=2,
        index=8, text="Ἰδοὺ", end_index=99,
    )
    items = resolve_verse([quotation], MARK_1_2)

    assert items[0]["id"] is not None, "the opening word is in range and must still resolve"
    assert items[0].get("id_end") is None, (
        "an out-of-range closing index must not be given an id"
    )
