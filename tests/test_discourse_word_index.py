"""A citation's index counts words, and Macula Hebrew rows are morphemes.

`resolve_citation` matched Levinsohn's 1-based index against *row position*. That is correct for
Macula Greek, where there is exactly one row per word, and wrong for Macula Hebrew, where a word
written with a prefix or suffix occupies several rows. Measured by `discourse-flow`: 94-100% of
Greek citations resolved `verified` against 1-15% of Hebrew, and the rate tracked rows per word
rather than anything about the text.

Ruth 1:1 is the smallest complete statement of it. 33 rows over 19 words; HOTDF-LS cites `Kings`
at index 4, quoting `הַשֹּׁפְטִ֔ים`, which is word 4 and rows 6-7. Matching on position looked at
row 4 — the second morpheme of word 2 — and reported `disagrees`.

The `ref` column carries the word index in both corpora, so `RUT 1:1!4` *is* word 4. Reading it
removes an assumption rather than adding a per-edition flag.

The word-level id follows the format the Macula Hebrew documentation declares for `n`, in
*MACULA Hebrew Treebank for OSHB* §2.1: `BBCCCVVVWWWP`, where `WWW` is the word index within the
verse and `P` is the word part. Dropping `P` addresses the word, and leaves the same
`BBCCCVVVWWW` shape Greek already uses.
"""

from llmflow.utils.discourse import resolve_citation, Outcome

#: Ruth 1:1 as Macula Hebrew holds it — morphemes, with `ref` carrying the word index and
#: `xml:id` carrying the word part as its final digit.
RUTH_1_1 = [
    {"ref": "RUT 1:1!1", "xml:id": "o080010010011", "text": "וַ"},
    {"ref": "RUT 1:1!1", "xml:id": "o080010010012", "text": "יְהִ֗י"},
    {"ref": "RUT 1:1!2", "xml:id": "o080010010021", "text": "בִּ"},
    {"ref": "RUT 1:1!2", "xml:id": "o080010010022", "text": "ימֵי֙"},
    {"ref": "RUT 1:1!3", "xml:id": "o080010010031", "text": "שְׁפֹ֣ט"},
    {"ref": "RUT 1:1!4", "xml:id": "o080010010041", "text": "הַ"},
    {"ref": "RUT 1:1!4", "xml:id": "o080010010042", "text": "שֹּׁפְטִ֔ים"},
    {"ref": "RUT 1:1!5", "xml:id": "o080010010051", "text": "וַ"},
]

#: Mark 1:1 as Macula Greek holds it — one row per word, and no word part in the id.
MARK_1_1 = [
    {"ref": "MRK 1:1!1", "xml:id": "n41001001001", "text": "Ἀρχὴ"},
    {"ref": "MRK 1:1!2", "xml:id": "n41001001002", "text": "τοῦ"},
    {"ref": "MRK 1:1!3", "xml:id": "n41001001003", "text": "εὐαγγελίου"},
]


def test_a_hebrew_citation_resolves_against_the_word_not_the_row():
    """`Kings` at index 4 quoting `הַשֹּׁפְטִ֔ים` is word 4, which begins at row 6."""
    resolution = resolve_citation(RUTH_1_1, 4, "הַשֹּׁפְטִ֔ים")

    assert resolution.outcome is Outcome.VERIFIED, (
        f"expected the quote at word 4 to verify, got {resolution.outcome.value}. Matching the "
        f"index against row position lands on row 4, the second morpheme of word 2."
    )


def test_the_id_addresses_the_word_and_not_one_of_its_morphemes():
    """`BBCCCVVVWWWP` minus `P` is the word; the morpheme ids are `…0041` and `…0042`."""
    resolution = resolve_citation(RUTH_1_1, 4, "הַשֹּׁפְטִ֔ים")

    assert resolution.word_id == "o08001001004", (
        f"expected the word-level id, got {resolution.word_id!r}. A consumer highlighting a "
        f"morpheme id shows only part of the word."
    )


def test_a_hebrew_word_spanning_two_rows_still_resolves_from_its_first_morpheme():
    """Word 1 is `וַ` + `יְהִ֗י`; the quote is the whole word, written as the source writes it."""
    resolution = resolve_citation(RUTH_1_1, 1, "וַיְהִ֗י")

    assert resolution.outcome in (Outcome.VERIFIED, Outcome.UNVERIFIABLE), (
        f"a quote covering a whole multi-morpheme word should not report "
        f"{resolution.outcome.value}"
    )
    assert resolution.word_id == "o08001001001"


def test_greek_is_unchanged():
    """Greek has one row per word and no word part, so reading `ref` must be a no-op there."""
    resolution = resolve_citation(MARK_1_1, 3, "εὐαγγελίου")

    assert resolution.outcome is Outcome.VERIFIED
    assert resolution.word_id == "n41001001003", (
        "a Greek id carries no word part, so nothing may be trimmed from it"
    )


def test_a_maqqef_separates_words_in_a_quote_as_it_does_in_the_edition():
    """Hebrew joins words with a maqqef, and Macula holds the mark in `after`, not in `text`.

    A citation writes it attached — `בֶן־ אֲמִתַּ֖י` — so a quote comparing `בן־` against Macula's
    `בן` fails on every maqqef-joined word. Splitting the quote there reads the edition's own
    model: the WLC registration states that `after` carries the space, maqqef and sof pasuq, so
    word joining is data rather than logic.

    Measured on Jonah 1: every one of its fifteen unresolved citations was this, and the passage
    goes to 100%.
    """
    rows = [
        {"ref": "JON 1:1!5", "xml:id": "o320010010051", "text": "יוֹנָ֥ה"},
        {"ref": "JON 1:1!6", "xml:id": "o320010010061", "text": "בֶן"},
        {"ref": "JON 1:1!7", "xml:id": "o320010010071", "text": "אֲמִתַּ֖י"},
    ]
    resolution = resolve_citation(rows, 2, "בֶן־ אֲמִתַּ֖י")

    assert resolution.outcome is Outcome.VERIFIED, (
        f"the quote names words 6-7 with a maqqef between them, got {resolution.outcome.value}"
    )
    assert resolution.word_id == "o32001001006", "the word, with the part digit dropped"


def test_a_maqqef_with_no_space_after_it_also_separates():
    """`כל־הארץ` is two words in the edition, written as one string in a quote."""
    rows = [
        {"ref": "GEN 1:1!1", "xml:id": "o01001001011", "text": "כָּל"},
        {"ref": "GEN 1:1!2", "xml:id": "o01001001021", "text": "הָאֶָרֶץ"},
    ]
    resolution = resolve_citation(rows, 1, "כָּל־הָאֶָרֶץ")

    assert resolution.outcome is Outcome.VERIFIED


def test_a_note_anchors_to_a_word_too():
    """A note carries no quote, so it is anchored at its index — which counts words.

    `resolve_verse` had its own indexing for this path, straight into `rows`, so a Hebrew note
    anchored to whichever morpheme happened to sit at that row number.
    """
    from llmflow.utils.discourse import Citation, resolve_verse, NOTE_KIND

    note = Citation(
        feature="Discourse note", kind=NOTE_KIND, book="RUT",
        chapter=1, verse=1, index=4, text="a note about the judges",
    )
    items = resolve_verse([note], RUTH_1_1)

    assert len(items) == 1
    assert items[0]["outcome"] == "anchored"
    assert items[0]["id"] == "o08001001004", (
        f"a note at index 4 should anchor to word 4, got {items[0]['id']!r}"
    )


def test_an_index_past_the_last_word_is_out_of_range_by_words_not_rows():
    """Ruth 1:1 has 19 words over 33 rows in full; this fixture has 5 words over 8 rows.

    Index 6 is past the end. Counting rows would have called it in range, which is how a
    citation could be anchored to a morpheme of a word that is not the one cited.
    """
    resolution = resolve_citation(RUTH_1_1, 6, None)

    assert resolution.outcome is Outcome.OUT_OF_RANGE, (
        f"index 6 of 5 words should be out of range, got {resolution.outcome.value}"
    )
