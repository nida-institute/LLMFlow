"""Where a citation's index and its quote disagree, the quote decides — if it is unambiguous.

Two independently produced datasets disagree about what a word is. Levinsohn's index counts words
in his text; Macula counts words in its own. `מִבֵּ֧ית לֶ֣חֶם` is one place name to him and two
space-separated words to Macula, so from that point in Ruth 1:1 his numbering runs one behind and
every later citation in the verse lands on the neighbour. Nothing is wrong with either dataset.

That is why an index is not a reliable address across editions and a quote is: the index names a
position in a text this engine does not hold, while the quote is the text itself, matched against
what the edition actually has. Greek reaches 94-100% rather than 100% for the same reason, having
fewer compounds and no morpheme splitting to disagree about.

Previously a usable index was never moved, and only an impossible one was rescued. That kept the
citation's own address and reported the disagreement — but the id pointed at the wrong word, so a
consumer highlighting it highlighted the neighbour. Measured across six Hebrew passages: 86 of 124
disagreements had the quote at exactly one other position.

**The disagreement stays visible.** The outcome is still `disagrees`, not `verified`, and
`resolved_index` says where the quote was found. What changes is only which word the id names.
Ambiguity is not resolved: a quote matching several positions still yields no id, because guessing
between them would be inventing an answer.
"""

from llmflow.utils.discourse import Outcome, resolve_citation

#: Ruth 1:1 words 13-16, as Macula holds them — one row per word here, which is enough to show
#: the index-versus-quote conflict without the morpheme dimension.
VERSE = [
    {"ref": "RUT 1:1!13", "xml:id": "o08001001013", "text": "לָגוּר֙"},
    {"ref": "RUT 1:1!14", "xml:id": "o08001001014", "text": "בִּשְׂדֵ֣י"},
    {"ref": "RUT 1:1!15", "xml:id": "o08001001015", "text": "מוֹאָ֔ב"},
    {"ref": "RUT 1:1!16", "xml:id": "o08001001016", "text": "ה֥וּא"},
]

#: A verse where one word occurs twice, so a quote naming it is ambiguous.
REPEATED = [
    {"ref": "GEN 1:1!1", "xml:id": "o01001001001", "text": "אֶרֶץ"},
    {"ref": "GEN 1:1!2", "xml:id": "o01001001002", "text": "טוֹב"},
    {"ref": "GEN 1:1!3", "xml:id": "o01001001003", "text": "אֶרֶץ"},
]


def test_an_unambiguous_quote_moves_the_id_to_the_word_it_names():
    """Levinsohn says word 13; the quote is `בִּשְׂדֵ֣י`, which Macula has at 14."""
    resolution = resolve_citation(VERSE, 1, "בִּשְׂדֵ֣י")

    assert resolution.word_id == "o08001001014", (
        f"the quote names word 14 unambiguously; got {resolution.word_id!r}, which is the word "
        f"the index pointed at rather than the word cited"
    )


def test_the_disagreement_is_still_reported():
    """Moving the id must not hide that the two sources disagreed."""
    resolution = resolve_citation(VERSE, 1, "בִּשְׂדֵ֣י")

    assert resolution.outcome is Outcome.DISAGREES, (
        "the index and the quote disagree, and that stays visible — the quote deciding where to "
        "point is not the two agreeing"
    )
    assert resolution.resolved_index == 2, "and where the quote was found is reported"


def test_an_agreeing_index_and_quote_still_verify():
    """The common case is untouched: nothing moves when nothing disagrees."""
    resolution = resolve_citation(VERSE, 2, "בִּשְׂדֵ֣י")

    assert resolution.outcome is Outcome.VERIFIED
    assert resolution.word_id == "o08001001014"


def test_an_ambiguous_quote_does_not_move_the_id():
    """Two matches is not evidence. A unique quote outranks the index; an ambiguous one does not.

    The index keeps the word here, because choosing between two matches would be inventing an
    answer and discarding the index would throw away the only address there is. The count is
    reported so a reader knows why nothing moved.
    """
    resolution = resolve_citation(REPEATED, 2, "אֶרֶץ")

    assert resolution.outcome is Outcome.DISAGREES
    assert resolution.word_id == "o01001001002", "the index's word, since the quote cannot decide"
    assert resolution.candidates == 2


def test_a_quote_that_is_nowhere_reports_the_index_and_the_failure():
    """Step 3 of the chain: neither corroborates the other, so both facts are reported.

    The id is the index's word, because it is the only address there is. The outcome is
    `not_found`, because nothing in the verse supports it. Giving the id without the outcome would
    present an unverified word as a resolved one — which is what the previous behaviour did, and
    it is the reason 36 citations across six passages looked resolved and were not.
    """
    resolution = resolve_citation(VERSE, 2, "λόγος")

    assert resolution.outcome is Outcome.NOT_FOUND, (
        "the quote is nowhere in the verse, so nothing here corroborates the index"
    )
    assert resolution.word_id == "o08001001014", "and the index's word is still reported"


def test_a_citation_with_no_quote_is_unchanged():
    """An index with nothing to check it against is unverifiable, not disagreeing."""
    resolution = resolve_citation(VERSE, 3, None)

    assert resolution.outcome is Outcome.UNVERIFIABLE
    assert resolution.word_id == "o08001001015"


def test_an_out_of_range_index_with_a_unique_quote_is_still_rescued():
    """The existing rescue path is the same judgment, and keeps its own outcome."""
    resolution = resolve_citation(VERSE, 99, "ה֥וּא")

    assert resolution.outcome is Outcome.RESCUED
    assert resolution.word_id == "o08001001016"
