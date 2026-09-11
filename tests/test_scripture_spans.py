"""Cutting a passage into spans named by word id.

A unit of analysis does not always start where a verse does: in Hebrew versification a psalm's
superscription is part of verse 1, and a clause boundary can fall anywhere. So a consumer that
has decided where its units begin names them by word id, and asks for the text of each.

Verse ranges remain the way to ask for a passage; spans are how to cut one up.
"""
from llmflow.utils.scripture import rows_in_span, text_for_spans

#: Two verses of Psalm 23 as Macula Hebrew has them, trimmed to what a span cut needs.
#: Word 2 of verse 1 is written as two morphemes, so a span boundary at word 3 does not fall
#: on a morpheme index — which is the case a positional cut would get wrong.
ROWS = [
    {"xml:id": "o190230010011", "ref": "PSA 23:1!1", "text": "מִזְמ֥וֹר", "after": " "},
    {"xml:id": "o190230010021", "ref": "PSA 23:1!2", "text": "לְ", "after": ""},
    {"xml:id": "o190230010022", "ref": "PSA 23:1!2", "text": "דָוִ֑ד", "after": " "},
    {"xml:id": "o190230010031", "ref": "PSA 23:1!3", "text": "יְהוָ֥ה", "after": " "},
    {"xml:id": "o190230010041", "ref": "PSA 23:1!4", "text": "רֹ֝עִ֗", "after": ""},
    {"xml:id": "o190230010042", "ref": "PSA 23:1!4", "text": "י", "after": " "},
    {"xml:id": "o190230010051", "ref": "PSA 23:1!5", "text": "לֹ֣א", "after": " "},
    {"xml:id": "o190230010061", "ref": "PSA 23:1!6", "text": "אֶחְסָֽר", "after": "׃"},
    {"xml:id": "o190230020011", "ref": "PSA 23:2!1", "text": "בִּ", "after": ""},
    {"xml:id": "o190230020012", "ref": "PSA 23:2!1", "text": "נְא֣וֹת", "after": " "},
    {"xml:id": "o190230020021", "ref": "PSA 23:2!2", "text": "דֶּ֭שֶׁא", "after": " "},
]


def test_a_span_cuts_where_the_word_ids_say_not_where_the_verse_does():
    cut = rows_in_span(ROWS, "o19023001003", "o19023001006")

    assert [row["xml:id"] for row in cut] == [
        "o190230010031",
        "o190230010041",
        "o190230010042",
        "o190230010051",
        "o190230010061",
    ]


def test_a_span_takes_every_morpheme_of_the_words_at_its_edges():
    """A boundary names a word; a word may be written in several morphemes."""
    cut = rows_in_span(ROWS, "o19023001002", "o19023001004")

    assert [row["text"] for row in cut] == ["לְ", "דָוִ֑ד", "יְהוָ֥ה", "רֹ֝עִ֗", "י"]


def test_a_span_may_cross_a_verse_boundary():
    cut = rows_in_span(ROWS, "o19023001006", "o19023002001")

    assert [row["xml:id"] for row in cut] == [
        "o190230010061",
        "o190230020011",
        "o190230020012",
    ]


def test_text_for_spans_returns_one_result_per_span_in_the_order_asked():
    results = text_for_spans(
        ROWS,
        spans=[
            {"from": "o19023001001", "to": "o19023001002"},
            {"from": "o19023001003", "to": "o19023001006"},
        ],
        fmt="milestones",
        book="PSA",
    )

    assert len(results) == 2
    assert results[0]["text"] == "⌊23:1⌋ מִזְמ֥וֹר לְדָוִ֑ד"
    assert results[1]["text"].startswith("⌊23:1⌋ יְהוָ֥ה")
    assert results[0]["from"] == "o19023001001"


def test_a_span_carries_the_annotation_of_its_own_words_only():
    results = text_for_spans(
        ROWS,
        spans=[{"from": "o19023001003", "to": "o19023001004"}],
        fmt="milestones",
        book="PSA",
        include=["ids"],
    )
    words = results[0]["scripture_pipelines"]["ids"]

    assert set(words) == {"o19023001003", "o19023001004"}


def test_a_span_naming_a_word_that_is_not_there_says_so():
    """Silence would yield a shorter text that looks complete."""
    try:
        rows_in_span(ROWS, "o19023001003", "o19023009099")
    except ValueError as exc:
        assert "o19023009099" in str(exc)
    else:
        raise AssertionError("a span naming an absent word should raise")
