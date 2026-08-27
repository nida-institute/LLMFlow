"""The `scripture_pipelines` container and `include: [ids]` — #200 step 4."""
from pathlib import Path

import pytest

from llmflow.utils.scripture import (
    CONTAINER_KEY,
    INCLUDE_FAMILIES,
    MILESTONE_TEMPLATE,
    edition_text,
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

real_data = pytest.mark.skipif(
    not (MACULA / "tsv/macula-greek-SBLGNT.tsv").is_file(),
    reason="Macula Greek is not on this machine",
)


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
    usj = edition_text("SBLGNT", "MRK 1:1", fmt="usj", editions=EDITIONS)
    assert CONTAINER_KEY not in usj


@real_data
def test_an_empty_include_means_no_container():
    usj = edition_text("SBLGNT", "MRK 1:1", fmt="usj", editions=EDITIONS, include=[])
    assert CONTAINER_KEY not in usj


@real_data
def test_the_container_carries_the_versification_scheme():
    usj = edition_text("SBLGNT", "MRK 1:1", fmt="usj", editions=EDITIONS, include=["ids"])
    assert usj[CONTAINER_KEY]["versification"] == "org"


@real_data
def test_an_unknown_edition_scheme_is_reported_rather_than_invented(caplog):
    with caplog.at_level("WARNING"):
        usj = edition_text("NO-SCHEME", "MRK 1:1", fmt="usj", editions=EDITIONS, include=["ids"])
    assert "versification" not in usj[CONTAINER_KEY]
    assert "versification" in caplog.text.lower()


@real_data
def test_nothing_is_added_outside_the_container():
    """An extension anywhere else is an extension nobody can find or strip."""
    usj = edition_text("SBLGNT", "MRK 1:1", fmt="usj", editions=EDITIONS, include=["ids"])
    assert set(usj) == {"type", "version", "content", CONTAINER_KEY}
    stripped = {k: v for k, v in usj.items() if k != CONTAINER_KEY}
    assert set(stripped) == {"type", "version", "content"}


# --- include: [ids] -------------------------------------------------------------------


@real_data
def test_ids_arrive_as_srcloc_on_each_word():
    """`ids` is spec-defined, so it belongs on the word, not in the container."""
    usj = edition_text("SBLGNT", "MRK 1:1", fmt="usj", editions=EDITIONS, include=["ids"])
    first = words(usj)[0]
    assert first["type"] == "char" and first["marker"] == "w"
    assert first["srcloc"] == "n41001001001"
    assert first["content"] == ["Ἀρχὴ"]


@real_data
def test_every_word_carries_an_id():
    usj = edition_text("SBLGNT", "MRK 1", fmt="usj", editions=EDITIONS, include=["ids"])
    got = words(usj)
    assert got, "no word nodes emitted"
    assert all(w.get("srcloc") for w in got)


@real_data
def test_without_ids_words_stay_plain_text():
    """The cheap form stays cheap: no per-word node when nothing consumes one."""
    usj = edition_text("SBLGNT", "MRK 1:1", fmt="usj", editions=EDITIONS)
    assert words(usj) == []


@real_data
@pytest.mark.parametrize("edition", ["SBLGNT", "SBLGNT-TEI"])
def test_both_backends_give_the_same_ids(edition):
    usj = edition_text(edition, "MRK 1:1", fmt="usj", editions=EDITIONS, include=["ids"])
    assert [w["srcloc"] for w in words(usj)][:3] == [
        "n41001001001",
        "n41001001002",
        "n41001001003",
    ]


# --- the oracle still holds with words wrapped ----------------------------------------


@real_data
@pytest.mark.parametrize("passage", ["MRK 1:1", "MRK 1:1-3", "MRK 1", "MRK 1:45-2:3"])
def test_flattening_still_reproduces_milestones_with_ids(passage):
    usj = edition_text("SBLGNT", passage, fmt="usj", editions=EDITIONS, include=["ids"])
    assert flatten(usj) == edition_text("SBLGNT", passage, fmt="milestones", editions=EDITIONS)


# --- lint rules, as errors at the call ------------------------------------------------


@real_data
@pytest.mark.parametrize("fmt", ["plain", "milestones"])
def test_include_without_usj_is_an_error(fmt):
    """Nowhere to put a payload — §4."""
    with pytest.raises(ValueError, match="include"):
        edition_text("SBLGNT", "MRK 1:1", fmt=fmt, editions=EDITIONS, include=["ids"])


@real_data
def test_an_unknown_family_names_the_known_ones():
    with pytest.raises(ValueError, match="morphology"):
        edition_text("SBLGNT", "MRK 1:1", fmt="usj", editions=EDITIONS, include=["parsing"])


@real_data
def test_a_family_that_is_not_built_yet_says_so_rather_than_returning_nothing():
    with pytest.raises(NotImplementedError, match="senses"):
        edition_text("SBLGNT", "MRK 1:1", fmt="usj", editions=EDITIONS, include=["senses"])


@real_data
def test_include_must_be_a_list_not_a_word():
    with pytest.raises(ValueError, match="list"):
        edition_text("SBLGNT", "MRK 1:1", fmt="usj", editions=EDITIONS, include="ids")
