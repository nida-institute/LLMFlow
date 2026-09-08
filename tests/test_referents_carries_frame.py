"""`frame` is participant reference, so it rides with `referents`.

`frame` carries the predicate's semantic roles as participant ids — `A0:080010010042;` — and it
was in no `include:` family, so there was no declarative way to ask for it.
`data/include-families.json` had it under `not_carried`, filed as *"syntactic frame, belongs with
`syntax`"*.

That filing was made before `include: [syntax]` was ruled standoff. As ruled in
`design-scripture-representations.md` §4.5, the `syntax` payload is the constituency tree with
leaves carrying **only references** — no text and no attributes. In Lowfat terms `syntax` is the
`wg` node tree while `frame` is an `m` leaf attribute, so `frame` cannot ride there in the shape
that was ruled. The families are organised by form, and per-word data belongs in a per-word family.

Why `referents` rather than its own: `frame` is the semantic-role counterpart to `subjref`'s
grammatical one, and the two come apart exactly where a discourse boundary criterion bites. A
passive whose subject is the undergoer reads to `subjref` as "same participant, still the subject",
and the role reversal is invisible; `A0` against `A1` states it. Reported by `discourse-flow`, who
found it correcting a Psalm 23 division: vv. 2-3 have one participant as `A0` and another as `A1`,
v4 reverses them, and v6 introduces a participant absent from the earlier cast as `A0`.
"""

from llmflow.utils.scripture import (
    CONTAINER_KEY,
    family_columns,
    family_is_per_word,
    rows_to_usj,
)

#: A Hebrew word carrying a frame, as Macula holds it.
HEBREW = [
    {
        "book": "PSA", "chapter": 23, "verse": 2, "text": "יַרְבִּיצֵנִי",
        "xml:id": "o190230020011", "ref": "PSA 23:2!1",
        "frame": "AA:190230010031; A0:190230010031; A1:190230010022",
        "subjref": "190230010031", "participantref": "",
    }
]

#: A Greek word carrying a frame. Both corpora have the column.
GREEK = [
    {
        "book": "MRK", "chapter": 1, "verse": 1, "text": "Ἀρχὴ",
        "xml:id": "n41001001001", "ref": "MRK 1:1!1",
        "frame": "A0:n41001001002;", "subjref": "", "referent": "n41001001001",
    }
]


def test_frame_is_a_declared_column_of_referents():
    assert "frame" in family_columns("referents"), (
        "`frame` was in no family, so no pipeline could ask for it declaratively"
    )


def test_referents_stays_per_word():
    """`frame` is an attribute of a word, like the three columns already there."""
    assert family_is_per_word("referents") is True


def test_frame_is_no_longer_listed_as_not_carried():
    """The declaration may not both carry a column and say it is not carried."""
    import json
    from pathlib import Path

    text = Path("data/include-families.json").read_text(encoding="utf-8")
    declared = json.loads(text)
    not_carried = declared.get("notes", {}).get("not_carried", "")

    assert "`frame`" not in not_carried, (
        "`not_carried` still names `frame`, so the file contradicts itself"
    )


def test_a_hebrew_frame_reaches_the_payload():
    doc = rows_to_usj(HEBREW, "PSA", include=["ids", "referents"])
    referents = doc[CONTAINER_KEY]["referents"]

    assert referents, "the family was requested and the row carries a frame"
    entry = referents["o190230020011"]
    assert entry["frame"] == "AA:190230010031; A0:190230010031; A1:190230010022", (
        "the raw column value is carried; splitting `A0:`/`A1:` is the consumer's business"
    )


def test_a_greek_frame_reaches_the_payload():
    """Both corpora carry `frame`, so the family stays symmetric across languages."""
    doc = rows_to_usj(GREEK, "MRK", include=["ids", "referents"])
    entry = doc[CONTAINER_KEY]["referents"]["n41001001001"]

    assert entry["frame"] == "A0:n41001001002;"


def test_an_empty_frame_is_not_carried_as_an_empty_string():
    """A word without a frame says nothing about one, rather than carrying a blank."""
    rows = [dict(GREEK[0], frame="")]
    doc = rows_to_usj(rows, "MRK", include=["ids", "referents"])
    entry = doc[CONTAINER_KEY]["referents"].get("n41001001001", {})

    assert "frame" not in entry, (
        "an empty column is absent from the payload, as the other columns already are"
    )


# --- a Hebrew pronominal suffix is a referring expression with no word of its own ----------------

#: One Hebrew word written as two morphemes, the second a pronominal suffix carrying its own
#: participant. Both share the word index `!1`; only the suffix names a participant.
SUFFIXED = [
    {
        "book": "RUT", "chapter": 1, "verse": 8, "text": "עִמָּ", "pos": "preposition",
        "xml:id": "o080010080071", "ref": "RUT 1:8!7", "participantref": "",
    },
    {
        "book": "RUT", "chapter": 1, "verse": 8, "text": "כֶם", "pos": "suffix",
        "xml:id": "o080010080072", "ref": "RUT 1:8!7", "participantref": "o080010010051",
    },
]


def test_a_hebrew_suffix_keeps_its_own_participant():
    """A pronominal suffix is a referring expression with no word of its own, and in Hebrew
    narrative a large share of references are suffixed. **45,336 of the corpus's 47,442 suffix
    morphemes — 95.6% — carry their own `participantref`**, and the value is genuinely theirs: of
    200 suffixes carrying none, exactly one had a same-word morpheme that did.

    So a consumer must key on the morpheme, not the word. This asserts the engine does not
    collapse the two: were rows merged per word, every suffixed reference would vanish silently,
    which is the failure mode `discourse-flow` asked about.
    """
    doc = rows_to_usj(SUFFIXED, "RUT", include=["ids", "referents"])
    referents = doc[CONTAINER_KEY]["referents"]

    assert referents["o080010080072"]["participantref"] == "o080010010051"
    assert "o080010080071" not in referents, "the host morpheme names no participant"


def _notes():
    import json
    from pathlib import Path

    return json.loads(Path("data/include-families.json").read_text(encoding="utf-8"))["notes"]


def test_the_declaration_says_hebrew_participant_ids_are_bare():
    """The prefix rule was discoverable only by querying the corpus, which is the actual defect.

    Every Greek `referent` value — all 18,213 — begins with `n`, matching the ids beside it. Every
    Hebrew `participantref` value — all 59,227 — is bare digits, while every Hebrew id carries a
    leading `o`. Of 50 sampled, 50 resolve prefixed and 0 as written, so a chain built by joining
    the column onto the ids returns nothing and does not raise.

    Declared rather than transformed: `frame` and `subjref` carry the same bare ids, and repairing
    `frame` would mean parsing `A0:`/`A1:`, which is the consumer's business by ruling. Fixing one
    column and leaving two is worse than fixing none, because it teaches a rule that then fails.
    """
    note = _notes().get("participant_ids", "")

    assert note, "the file consumers read must carry the rule, not a collab thread"
    assert "o" in note and "participantref" in note
    assert "frame" in note and "subjref" in note, "the rule covers all three columns or it misleads"


def test_the_declaration_says_the_two_corpora_use_different_columns():
    """`referent` is Greek-only, `participantref` Hebrew-only, and `referents` declares the union.
    A consumer reading one language would otherwise take its column list for the family's."""
    note = _notes().get("participant_ids", "")

    assert "referent" in note


def test_the_two_corpora_name_participants_differently():
    """Greek states `referent`, Hebrew `participantref`; neither has the other's column. The family
    declares the union and emits whichever the resource actually has, so a Hebrew payload lacks
    `referent` and a Greek one lacks `participantref`. Recorded because a consumer reading one
    language would otherwise take its column list for the family's.
    """
    hebrew = rows_to_usj(SUFFIXED, "RUT", include=["ids", "referents"])[CONTAINER_KEY]["referents"]
    greek = rows_to_usj(GREEK, "MRK", include=["ids", "referents"])[CONTAINER_KEY]["referents"]

    assert "referent" not in hebrew["o080010080072"]
    assert "participantref" not in greek["n41001001001"]
    assert greek["n41001001001"]["referent"] == "n41001001001"
