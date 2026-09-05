"""Resolving a Levinsohn citation against SBLGNT — #200 step 9.

His word indices are NA28-family; the text is SBLGNT. Where they disagree the index does not
fail, it names a different word. See §5 step 9 of plan-scripture-step.md.
"""
from pathlib import Path

import pytest

from llmflow.utils.discourse import (
    Outcome,
    normalize_greek,
    osis_to_usfm,
    parse_osis_ref,
    resolve_citation,
)

LGNTDF = Path.home() / "github/biblicalhumanities/levinsohn/LGNTDF"
real_data = pytest.mark.skipif(
    not (LGNTDF / "Main_clauses.xml").is_file(), reason="LGNTDF is not on this machine"
)


def rows(*words) -> list:
    """Macula-shaped rows for one verse."""
    return [
        {"ref": f"MRK 1:1!{i}", "xml:id": f"n{i:03d}", "text": w}
        for i, w in enumerate(words, start=1)
    ]


# --- normalisation --------------------------------------------------------------------


def test_case_is_folded():
    assert normalize_greek("Βίβλος") == normalize_greek("βίβλος")


def test_the_two_encodings_of_the_acute_compare_equal():
    """Both corpora are uniformly tonos today, so this guards against re-encoding.

    Macula was re-normalised once already. A comparison that depends on which code point a
    source picked would break silently the next time either side changes.
    """
    tonos = "\u03af"  # GREEK SMALL LETTER IOTA WITH TONOS
    oxia = "\u1f77"  # GREEK SMALL LETTER IOTA WITH OXIA — renders identically
    assert tonos != oxia, "the two code points are distinct"
    assert normalize_greek(tonos) == normalize_greek(oxia)


def test_edge_punctuation_is_trimmed():
    assert normalize_greek("χριστοῦ.") == normalize_greek("χριστοῦ")
    assert normalize_greek("σου,") == normalize_greek("σου")


def test_an_empty_word_normalises_to_empty():
    assert normalize_greek("") == ""
    assert normalize_greek(None) == ""


# --- OSIS references -----------------------------------------------------------------


@pytest.mark.parametrize(
    "osis, expected",
    [("Matt", "MAT"), ("Mark", "MRK"), ("John", "JHN"), ("1John", "1JN"), ("Rev", "REV")],
)
def test_osis_book_codes_map_to_usfm(osis, expected):
    assert osis_to_usfm(osis) == expected


def test_an_unknown_osis_book_is_reported():
    with pytest.raises(ValueError, match="Klingon"):
        osis_to_usfm("Klingon")


def test_a_citation_reference_is_split_into_its_parts():
    """A single-word reference has no closing index, and reports None rather than its opening."""
    assert parse_osis_ref("Mark.1.14!3") == ("MRK", 1, 14, 3, None)


def test_a_span_within_one_verse_keeps_both_ends():
    """A quarter of LGNTDF's citations name a span, and the extent is part of the citation."""
    assert parse_osis_ref("Mark.1.2!9-Mark.1.2!15") == ("MRK", 1, 2, 9, ("MRK", 1, 2, 15))


def test_a_span_across_verses_keeps_both_ends_too():
    """`Matt.6.9!5-Matt.6.13!61` is the Lord's Prayer, opening in 6:9 and closing in 6:13.

    The closing end is a reference in its own right, not an index into the opening verse. That
    the resolver holds one verse's rows and so cannot address a word in another is a limit on
    what it can give an id for — not a reason for the citation to forget where it ends.
    """
    assert parse_osis_ref("Matt.6.9!5-Matt.6.13!61") == ("MAT", 6, 9, 5, ("MAT", 6, 13, 61))


def test_a_malformed_reference_is_rejected():
    with pytest.raises(ValueError, match="not a Levinsohn reference"):
        parse_osis_ref("somewhere in Mark")


# --- the six outcomes ----------------------------------------------------------------


def test_a_matching_quote_verifies():
    got = resolve_citation(rows("Ἀρχὴ", "τοῦ", "εὐαγγελίου"), 2, "τοῦ")
    assert got.outcome is Outcome.VERIFIED
    assert got.word_id == "n002"
    assert got.index == 2


def test_a_multi_word_quote_verifies_across_words():
    got = resolve_citation(rows("Ἀρχὴ", "τοῦ", "εὐαγγελίου"), 2, "τοῦ εὐαγγελίου")
    assert got.outcome is Outcome.VERIFIED
    assert got.word_id == "n002"


def test_an_unambiguous_quote_decides_and_the_index_is_still_reported():
    """Step 2 of the chain: the index did not match, the quote matched once, so the quote decides.

    Mark 1:14 is the case that argues both ways. `Main clauses` index the clause onset and quote a
    constituent inside it, so there the index is the word to trust — and nothing in the corpus
    says which features behave that way, so the engine reports both rather than guessing:
    `word_id` from the quote, `index` unchanged, `quote_found_at` saying where it landed.

    Against it: wherever two editions count words differently the index names the neighbour, which
    was 86 of 124 disagreements across six Hebrew passages. The engine cannot tell those apart, so
    it states what each source said and leaves the choice to whoever knows the feature.
    """
    got = resolve_citation(rows("Καὶ", "μετὰ", "τὸ"), 1, "μετὰ")
    assert got.outcome is Outcome.DISAGREES
    assert got.word_id == "n002", "the word the quote names"
    assert got.index == 1, "the citation's own index, unchanged"
    assert got.resolved_index == 2
    assert got.quote_found_at == 2, "where the quote is, as information"


def test_an_impossible_index_is_rescued_when_the_quote_is_unique():
    got = resolve_citation(rows("Ἀρχὴ", "τοῦ", "εὐαγγελίου"), 99, "εὐαγγελίου")
    assert got.outcome is Outcome.RESCUED
    assert got.word_id == "n003"
    assert got.index == 99 and got.resolved_index == 3


def test_an_impossible_index_with_a_repeated_quote_is_ambiguous():
    got = resolve_citation(rows("καὶ", "τοῦ", "καὶ"), 99, "καὶ")
    assert got.outcome is Outcome.AMBIGUOUS
    assert got.word_id is None
    assert got.candidates == 2


def test_an_impossible_index_with_no_match_is_not_found():
    got = resolve_citation(rows("Ἀρχὴ", "τοῦ"), 99, "Ἰησοῦ")
    assert got.outcome is Outcome.NOT_FOUND
    assert got.word_id is None


def test_an_empty_quote_at_a_usable_index_is_unverifiable():
    """Honest about having nothing to check the index against."""
    got = resolve_citation(rows("Ἀρχὴ", "τοῦ"), 1, "")
    assert got.outcome is Outcome.UNVERIFIABLE
    assert got.word_id == "n001"


def test_an_empty_quote_at_an_impossible_index_is_out_of_range():
    got = resolve_citation(rows("Ἀρχὴ"), 99, "")
    assert got.outcome is Outcome.OUT_OF_RANGE
    assert got.word_id is None


def test_nothing_is_ever_guessed():
    """Every outcome either carries a verified id or carries none."""
    cases = [
        (rows("α", "β"), 1, "α"),
        (rows("α", "β"), 1, "β"),
        (rows("α", "β"), 9, "β"),
        (rows("α", "α"), 9, "α"),
        (rows("α"), 9, "ω"),
    ]
    for verse, index, quote in cases:
        got = resolve_citation(verse, index, quote)
        if got.word_id is not None:
            assert got.outcome in {
                Outcome.VERIFIED,
                Outcome.DISAGREES,
                Outcome.RESCUED,
                Outcome.UNVERIFIABLE,
            }


# --- a quote running past the verse end ----------------------------------------------


def test_a_quote_longer_than_the_verse_matches_on_its_prefix():
    """A range ref quotes across verses; only the opening verse is available here."""
    got = resolve_citation(rows("πάτερ", "ἡμῶν", "ὁ"), 1, "πάτερ ἡμῶν ὁ ἐν τοῖς οὐρανοῖς")
    assert got.outcome is Outcome.VERIFIED


def test_a_one_word_overlap_is_not_enough_to_claim_a_truncated_match():
    """Otherwise any verse ending in a common word would 'verify' a long quote."""
    got = resolve_citation(rows("Ἀρχὴ", "τοῦ", "καὶ"), 3, "καὶ πολλὰ ἕτερα λέγων")
    assert got.outcome is not Outcome.VERIFIED
