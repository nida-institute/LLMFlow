"""`format: usj` — the text in USJ structure, with no annotation."""
from pathlib import Path

import pytest

from llmflow.utils.scripture import (
    MILESTONE_TEMPLATE,
    edition_text,
    rows_to_usj,
)

MACULA = Path("/Users/jonathan/github/Clear/macula-greek/SBLGNT")
WLC = Path("/Users/jonathan/github/Clear/macula-hebrew/WLC/tsv/macula-hebrew.tsv")

EDITIONS = {
    "SBLGNT-TSV": {"kind": "tsv", "path": str(MACULA / "tsv/macula-greek-SBLGNT.tsv")},
    "SBLGNT-TEI": {"kind": "tei", "path": str(MACULA / "tei")},
    "WLC": {"kind": "tsv", "path": str(WLC)},
}

real_data = pytest.mark.skipif(
    not (MACULA / "tsv/macula-greek-SBLGNT.tsv").is_file(),
    reason="Macula Greek is not on this machine",
)
hebrew_data = pytest.mark.skipif(not WLC.is_file(), reason="Macula Hebrew is not on this machine")

GREEK_ROWS = [
    {"ref": "MRK 1:1!1", "text": "Ἀρχὴ", "after": " "},
    {"ref": "MRK 1:1!2", "text": "χριστοῦ", "after": "."},
    {"ref": "MRK 1:2!1", "text": "Καθὼς", "after": " "},
    {"ref": "MRK 1:2!2", "text": "προφήτῃ", "after": "·"},
    {"ref": "MRK 2:1!1", "text": "Καὶ", "after": " "},
    {"ref": "MRK 2:1!2", "text": "ἡμερῶν", "after": "."},
]


def flatten(usj: dict) -> str:
    """A verse node becomes its milestone; text nodes follow. The oracle for `milestones`.

    The chapter comes from the preceding `chapter` node, which is where USJ puts it — a
    consumer reads it the same way, and nothing outside the document is needed.
    """
    parts: list[str] = []
    chapter = None
    for node in usj["content"]:
        if node["type"] == "chapter":
            chapter = node["number"]
        elif node["type"] == "para":
            for item in node["content"]:
                if isinstance(item, str):
                    parts.append(item)
                elif item["type"] == "verse":
                    parts.append(
                        MILESTONE_TEMPLATE.format(chapter=chapter, verse=item["number"])
                    )
    return " ".join(parts)


# --- structure ----------------------------------------------------------------------


def test_the_document_declares_itself_as_usj():
    usj = rows_to_usj(GREEK_ROWS, book="MRK")
    assert usj["type"] == "USJ"
    assert usj["version"]


def test_the_book_code_is_the_first_node():
    usj = rows_to_usj(GREEK_ROWS, book="MRK")
    assert usj["content"][0] == {"type": "book", "marker": "id", "code": "MRK"}


def test_one_chapter_node_and_one_para_per_chapter():
    content = rows_to_usj(GREEK_ROWS, book="MRK")["content"][1:]
    assert [node["type"] for node in content] == ["chapter", "para", "chapter", "para"]
    assert [node["number"] for node in content if node["type"] == "chapter"] == ["1", "2"]


def test_a_para_holds_verse_nodes_and_text():
    para = rows_to_usj(GREEK_ROWS, book="MRK")["content"][2]
    assert para["marker"] == "p"
    assert para["content"][0] == {"type": "verse", "marker": "v", "number": "1"}
    assert para["content"][1] == "Ἀρχὴ χριστοῦ."


def test_every_verse_in_the_rows_appears_once():
    usj = rows_to_usj(GREEK_ROWS, book="MRK")
    verses = [
        item["number"]
        for node in usj["content"]
        if node["type"] == "para"
        for item in node["content"]
        if isinstance(item, dict) and item["type"] == "verse"
    ]
    assert verses == ["1", "2", "1"]


def test_no_annotation_is_added():
    """`include` is not implemented yet, and an empty payload must be an absent key."""
    usj = rows_to_usj(GREEK_ROWS, book="MRK")
    assert "scripture_pipelines" not in usj


def test_no_rows_yields_a_document_with_no_chapters():
    usj = rows_to_usj([], book="MRK")
    assert [node["type"] for node in usj["content"]] == ["book"]


# --- the oracle: flattening reproduces `milestones` ---------------------------------


@real_data
@pytest.mark.parametrize(
    "passage", ["MRK 1:1", "MRK 1:1-3", "MRK 1", "MRK 8:35", "MRK 1:45-2:3", "MRK 16"]
)
@pytest.mark.parametrize("edition", ["SBLGNT-TSV", "SBLGNT-TEI"])
def test_flattening_usj_reproduces_milestones(edition, passage):
    usj = edition_text(edition, passage, fmt="usj", editions=EDITIONS)
    milestones = edition_text(edition, passage, fmt="milestones", editions=EDITIONS)
    assert flatten(usj) == milestones


@hebrew_data
@pytest.mark.parametrize("passage", ["GEN 1:1", "GEN 1:1-2", "GEN 1"])
def test_flattening_usj_reproduces_milestones_in_hebrew(passage):
    usj = edition_text("WLC", passage, fmt="usj", editions=EDITIONS)
    assert flatten(usj) == edition_text("WLC", passage, fmt="milestones", editions=EDITIONS)


# --- through the step contract -------------------------------------------------------


@real_data
def test_the_edition_returns_a_dict_not_a_string_for_usj():
    assert isinstance(edition_text("SBLGNT-TSV", "MRK 1:1", fmt="usj", editions=EDITIONS), dict)


@real_data
def test_the_book_code_comes_from_the_passage():
    usj = edition_text("SBLGNT-TSV", "MRK 1:1", fmt="usj", editions=EDITIONS)
    assert usj["content"][0]["code"] == "MRK"


@real_data
def test_a_cross_chapter_range_carries_both_chapters():
    usj = edition_text("SBLGNT-TSV", "MRK 1:45-2:3", fmt="usj", editions=EDITIONS)
    numbers = [n["number"] for n in usj["content"] if n["type"] == "chapter"]
    assert numbers == ["1", "2"]


def test_an_unknown_format_is_rejected():
    with pytest.raises(ValueError, match="unknown format"):
        edition_text("SBLGNT-TSV", "MRK 1:1", fmt="parquet", editions=EDITIONS)
