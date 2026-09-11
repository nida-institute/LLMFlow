"""The `scripture_pipelines` container and `include: [ids]` — #200 step 4."""
from pathlib import Path

import pytest

from llmflow.utils.scripture import (
    CONTAINER_KEY,
    INCLUDE_FAMILIES,
    MILESTONE_TEMPLATE,
    resource_text,
    words_by_id,
)

MACULA = Path("/Users/jonathan/github/Clear/macula-greek/SBLGNT")
EDITIONS = {
    "SBLGNT": {
        "kind": "tsv",
        "path": str(MACULA / "tsv/macula-greek-SBLGNT.tsv"),
        "versification_scheme": "org",
    },
    "SBLGNT-TEI": {
        "kind": "tei",
        "path": str(MACULA / "tei"),
        "versification_scheme": "org",
    },
    "NO-SCHEME": {"kind": "tsv", "path": str(MACULA / "tsv/macula-greek-SBLGNT.tsv")},
}

WLC = Path("/Users/jonathan/github/Clear/macula-hebrew/WLC/tsv/macula-hebrew.tsv")
EDITIONS["WLC"] = {"kind": "tsv", "path": str(WLC), "versification_scheme": "org"}

real_data = pytest.mark.skipif(
    not (MACULA / "tsv/macula-greek-SBLGNT.tsv").is_file(),
    reason="Macula Greek is not on this machine",
)

hebrew_data = pytest.mark.skipif(not WLC.is_file(), reason="Macula Hebrew is not on this machine")


def words(usj: dict) -> list:
    """Every `w` char node in the document, in order."""
    found = []
    for node in usj["content"]:
        if node["type"] != "para":
            continue
        for item in node["content"]:
            if isinstance(item, dict) and item.get("marker") == "w":
                found.append(item)
    return found


def flatten(usj: dict) -> str:
    """Text as a consumer would rebuild it: milestones for verses, content for words."""
    parts, chapter = [], None
    for node in usj["content"]:
        if node["type"] == "chapter":
            chapter = node["number"]
        elif node["type"] == "para":
            for item in node["content"]:
                if isinstance(item, str):
                    parts.append(item)
                elif item["type"] == "verse":
                    parts.append(
                        MILESTONE_TEMPLATE.format(chapter=chapter, verse=item["number"]) + " "
                    )
                elif item.get("marker") == "w":
                    parts.append("".join(c for c in item["content"] if isinstance(c, str)))
    return "".join(parts).strip()


# --- the vocabulary -------------------------------------------------------------------


def test_the_seven_families_are_declared():
    assert INCLUDE_FAMILIES == (
        "ids",
        "morphology",
        "senses",
        "glosses",
        "referents",
        "discourse",
        "syntax",
    )


# --- the container appears only when asked for ----------------------------------------


@real_data
def test_no_include_means_no_container():
    """A payload nobody asked for is a payload nobody checked."""
    usj = resource_text("SBLGNT", "MRK 1:1", fmt="usj", resources=EDITIONS)
    assert CONTAINER_KEY not in usj


@real_data
def test_an_empty_include_means_no_container():
    usj = resource_text("SBLGNT", "MRK 1:1", fmt="usj", resources=EDITIONS, include=[])
    assert CONTAINER_KEY not in usj


@real_data
def test_the_container_carries_the_versification_scheme():
    usj = resource_text("SBLGNT", "MRK 1:1", fmt="usj", resources=EDITIONS, include=["ids"])
    assert usj[CONTAINER_KEY]["versification"] == "org"


@real_data
def test_an_unknown_edition_scheme_is_reported_rather_than_invented(caplog):
    with caplog.at_level("WARNING"):
        usj = resource_text("NO-SCHEME", "MRK 1:1", fmt="usj", resources=EDITIONS, include=["ids"])
    # Stated as `null` rather than omitted: the warning does not travel with the payload, so a
    # later reader could not tell an undeclared scheme from a key nobody asked for. Still not
    # invented, which is what this test is for. Rule `say-which-kind-of-nothing`.
    assert usj[CONTAINER_KEY]["versification"] is None
    assert "versification" in caplog.text.lower()


@real_data
def test_nothing_is_added_outside_the_container():
    """An extension anywhere else is an extension nobody can find or strip."""
    usj = resource_text("SBLGNT", "MRK 1:1", fmt="usj", resources=EDITIONS, include=["ids"])
    assert set(usj) == {"type", "version", "content", CONTAINER_KEY}
    stripped = {k: v for k, v in usj.items() if k != CONTAINER_KEY}
    assert set(stripped) == {"type", "version", "content"}


# --- include: [ids] -------------------------------------------------------------------


@real_data
def test_ids_arrive_as_srcloc_on_each_word():
    """`ids` is spec-defined, so it belongs on the word, not in the container."""
    usj = resource_text("SBLGNT", "MRK 1:1", fmt="usj", resources=EDITIONS, include=["ids"])
    first = words(usj)[0]
    assert first["type"] == "char" and first["marker"] == "w"
    assert first["srcloc"] == "n41001001001"
    assert first["content"] == ["Ἀρχὴ"]


@real_data
def test_every_word_carries_an_id():
    usj = resource_text("SBLGNT", "MRK 1", fmt="usj", resources=EDITIONS, include=["ids"])
    got = words(usj)
    assert got, "no word nodes emitted"
    assert all(w.get("srcloc") for w in got)


@real_data
def test_without_ids_words_stay_plain_text():
    """The cheap form stays cheap: no per-word node when nothing consumes one."""
    usj = resource_text("SBLGNT", "MRK 1:1", fmt="usj", resources=EDITIONS)
    assert words(usj) == []


@real_data
@pytest.mark.parametrize("resource", ["SBLGNT", "SBLGNT-TEI"])
def test_both_backends_give_the_same_ids(resource):
    usj = resource_text(resource, "MRK 1:1", fmt="usj", resources=EDITIONS, include=["ids"])
    assert [w["srcloc"] for w in words(usj)][:3] == [
        "n41001001001",
        "n41001001002",
        "n41001001003",
    ]


# --- the oracle still holds with words wrapped ----------------------------------------


@real_data
@pytest.mark.parametrize("passage", ["MRK 1:1", "MRK 1:1-3", "MRK 1", "MRK 1:45-2:3"])
def test_flattening_still_reproduces_milestones_with_ids(passage):
    usj = resource_text("SBLGNT", passage, fmt="usj", resources=EDITIONS, include=["ids"])
    assert flatten(usj) == resource_text("SBLGNT", passage, fmt="milestones", resources=EDITIONS)


# --- lint rules, as errors at the call ------------------------------------------------


# --- annotation travels beside the text, whatever form the text takes ------------------


@real_data
@pytest.mark.parametrize("fmt", ["plain", "milestones"])
def test_include_with_any_format_returns_the_text_beside_the_container(fmt):
    """Choosing annotation no longer chooses a text form.

    The payload is standoff — it needs nothing from the shape of the text — so a step that
    reads Levinsohn features is not thereby committed to a word-object document.
    """
    result = resource_text("SBLGNT", "MRK 1:1", fmt=fmt, resources=EDITIONS, include=["ids"])

    assert isinstance(result, dict)
    assert isinstance(result["text"], str)
    assert CONTAINER_KEY in result


@real_data
@pytest.mark.parametrize("fmt", ["plain", "milestones"])
def test_asking_for_annotation_does_not_change_the_text(fmt):
    """The text is the same text; the container is beside it, not inside it."""
    plain = resource_text("SBLGNT", "MRK 1:1-3", fmt=fmt, resources=EDITIONS)
    annotated = resource_text(
        "SBLGNT", "MRK 1:1-3", fmt=fmt, resources=EDITIONS, include=["ids"]
    )

    assert annotated["text"] == plain


@real_data
@pytest.mark.parametrize("fmt", ["plain", "milestones"])
def test_no_include_still_returns_a_bare_string(fmt):
    """The dict appears because annotation was asked for. Nothing that exists today changes."""
    assert isinstance(resource_text("SBLGNT", "MRK 1:1", fmt=fmt, resources=EDITIONS), str)


@real_data
def test_the_words_arrive_keyed_by_the_id_that_names_them():
    """`ids` has nowhere to write `srcloc` without a document, so it returns the words keyed.

    Keyed rather than positional: an id counts words within its verse while the text runs on,
    so a position would have to be derived from where each verse starts.
    """
    result = resource_text(
        "SBLGNT", "MRK 1:1", fmt="milestones", resources=EDITIONS, include=["ids"]
    )
    words = result[CONTAINER_KEY]["ids"]

    assert words["n41001001001"] == "Ἀρχὴ"
    assert all(word in result["text"] for word in words.values())


#: Psalm 23:1 as Macula Hebrew has it, copied from the corpus so the test needs no clone.
#: Re-derive with:
#:     resource_text("WLC", "PSA 23:1", fmt="usj", resources=..., include=["ids"])
#: In Hebrew versification the superscription is part of verse 1, and word 2 is written as two
#: morphemes — which is the property under test. Whether a superscription is its own unit is a
#: discourse-analysis judgement belonging to the analysts, and nothing here asserts it.
PSALM_23_1_ROWS = [
    {"xml:id": "o190230010011", "text": "מִזְמ֥וֹר", "after": " "},
    {"xml:id": "o190230010021", "text": "לְ", "after": ""},
    {"xml:id": "o190230010022", "text": "דָוִ֑ד", "after": " "},
    {"xml:id": "o190230010031", "text": "יְהוָ֥ה", "after": " "},
    {"xml:id": "o190230010041", "text": "רֹ֝עִ֗", "after": ""},
    {"xml:id": "o190230010042", "text": "י", "after": " "},
    {"xml:id": "o190230010051", "text": "לֹ֣א", "after": " "},
    {"xml:id": "o190230010061", "text": "אֶחְסָֽר", "after": "׃"},
]


def test_a_word_id_resolves_by_lookup_because_word_index_is_not_morpheme_index():
    """Why the map is keyed rather than positional, on a verse where the two differ.

    Word 2 of this verse is written as two morphemes, so word 3 is the *fourth* entry in
    morpheme order. Anything that resolved an id by counting would have to know that, and know
    where the verse began. Keyed, `o19023001003` is a lookup.
    """
    words = words_by_id(PSALM_23_1_ROWS)

    assert words["o19023001001"] == "מִזְמ֥וֹר"
    assert words["o19023001002"] == ["לְ", "דָוִ֑ד"]
    assert words["o19023001003"] == "יְהוָ֥ה"
    assert words["o19023001004"] == ["רֹ֝עִ֗", "י"]
    assert list(words) == [f"o19023001{n:03d}" for n in range(1, 7)]


def test_a_word_number_the_text_does_not_render_is_null():
    """The source reserves a slot; keeping it keeps every later id derivable."""
    rows = [row for row in PSALM_23_1_ROWS if not row["xml:id"].startswith("o19023001003")]

    words = words_by_id(rows)

    assert words["o19023001003"] is None
    assert words["o19023001004"] == ["רֹ֝עִ֗", "י"]


@hebrew_data
def test_the_fixture_above_still_matches_the_corpus():
    """The synthetic rows are a copy, so something must notice when the copy goes stale."""
    result = resource_text("WLC", "PSA 23:1", fmt="milestones", resources=EDITIONS, include=["ids"])

    assert result[CONTAINER_KEY]["ids"] == words_by_id(PSALM_23_1_ROWS)


@real_data
def test_a_requested_family_the_resource_cannot_supply_is_null_here_too():
    """The mirror of the usj guard in test_say_which_kind_of_nothing.py.

    A reader must be able to tell "this resource names no discourse source" from "discourse was
    never requested", in whichever form the text came back.
    """
    result = resource_text(
        "SBLGNT", "MRK 1:1", fmt="milestones", resources=EDITIONS, include=["ids", "discourse"]
    )

    assert "discourse" in result[CONTAINER_KEY]
    assert result[CONTAINER_KEY]["discourse"] is None


@real_data
def test_an_unknown_family_names_the_known_ones():
    with pytest.raises(ValueError, match="morphology"):
        resource_text("SBLGNT", "MRK 1:1", fmt="usj", resources=EDITIONS, include=["parsing"])


@real_data
def test_a_family_that_is_not_built_yet_says_so_rather_than_returning_nothing(monkeypatch):
    """Every declared family is built today, so the guard is exercised against a simulated one.

    It used `syntax` as its subject until `syntax` shipped. Deleting the test then would have
    removed the check that an unbuilt family raises rather than returning a document with the
    payload quietly missing — which is the behaviour, not an artefact of one family being
    incomplete. `monkeypatch` keeps it exercised without waiting for the next unbuilt name.
    """
    from llmflow.utils import scripture

    monkeypatch.setattr(
        scripture, "IMPLEMENTED_FAMILIES", scripture.IMPLEMENTED_FAMILIES - {"senses"}
    )

    with pytest.raises(NotImplementedError, match="senses"):
        resource_text("SBLGNT", "MRK 1:1", fmt="usj", resources=EDITIONS, include=["senses"])


def test_every_declared_family_is_built():
    """The state the test above had to simulate: nothing is named-but-missing right now.

    Recorded so that adding a name to `INCLUDE_FAMILIES` without an implementation is a decision
    someone takes deliberately, rather than a gap the suite stays quiet about.
    """
    from llmflow.utils.scripture import IMPLEMENTED_FAMILIES, INCLUDE_FAMILIES

    assert set(INCLUDE_FAMILIES) == set(IMPLEMENTED_FAMILIES)


@real_data
def test_include_must_be_a_list_not_a_word():
    with pytest.raises(ValueError, match="list"):
        resource_text("SBLGNT", "MRK 1:1", fmt="usj", resources=EDITIONS, include="ids")
