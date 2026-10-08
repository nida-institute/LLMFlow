"""`format: analysis` — a passage and its analyses as compact text for a model to read.

The USJ form repeats `type`, `marker` and `content` for every word, nests the tree as objects, and
carries a Mandarin gloss nobody asked for; on MAT 19:1-11 it was 37.6k of the reader's guide's 42k
input tokens. This form is derived from the USJ one, so it can carry nothing USJ does not: each
sentence's tree in bracketed treebank notation, then one table row per word. Plan:
`project/plans/plan-starter-cost.md` D1.
"""
import json
import re
from pathlib import Path

import pytest

from llmflow.utils.analysis_format import usj_to_analysis


def w(form, identifier, lemma):
    return {"type": "char", "marker": "w", "content": [form], "srcloc": identifier, "lemma": lemma}


DOC = {
    "type": "USJ",
    "version": "3.1",
    "content": [
        {"type": "book", "marker": "id", "code": "MAT"},
        {"type": "chapter", "marker": "c", "number": "19", "sid": "MAT 19"},
        {"type": "para", "marker": "p", "content": [
            {"type": "verse", "marker": "v", "number": "1", "sid": "MAT 19:1"},
            w("Καὶ", "n40019001001", "καί"), " ",
            w("ἐγένετο", "n40019001002", "γίνομαι"), " ",
            {"type": "verse", "marker": "v", "number": "2", "sid": "MAT 19:2"},
            w("ὅτε", "n40019002001", "ὅτε"),
        ]},
    ],
    "scripture_pipelines": {
        "versification": "org",
        "morphology": {
            "n40019001001": {"class": "conj"},
            "n40019001002": {"class": "verb", "person": "third", "number": "singular",
                             "tense": "aorist", "voice": "middle", "mood": "indicative"},
            "n40019002001": {"class": "conj"},
        },
        "senses": {"n40019001001": {"domain": "091001", "ln": "91.1"}},
        "glosses": {
            "n40019001001": {"gloss": "And", "english": "now", "mandarin": "就"},
            "n40019001002": {"gloss": "it came to pass", "mandarin": "成"},
        },
        "frequency": {
            "n40019001002": {"corpus": "GNT", "count": 669, "in_least_frequent_percent": 99.9},
        },
        "syntax": [
            {"class": "cl", "children": [
                {"token": "n40019001001", "class": "conj"},
                {"class": "cl", "clauseType": "main", "children": [
                    {"token": "n40019001002", "class": "verb", "role": "v"},
                ]},
            ]},
            {"class": "cl", "children": [{"token": "n40019002001", "class": "conj"}]},
        ],
        "outside_passage": {"n40019002001": True},
        "referents": {"n40019001002": [{"entity": "Jesus"}]},
    },
}


@pytest.fixture
def text():
    return usj_to_analysis(DOC)


def _rows(text):
    return [line for line in text.splitlines() if re.match(r"^\d+\t", line)]


def test_every_word_has_one_row_in_source_order(text):
    forms = [row.split("\t")[3] for row in _rows(text)]
    assert forms == ["Καὶ", "ἐγένετο", "ὅτε"]


def test_a_row_carries_its_reference_id_lemma_and_morphology(text):
    row = _rows(text)[1].split("\t")
    assert row[1] == "19:1" and row[2] == "n40019001002" and row[4] == "γίνομαι"
    assert "verb" in row[5] and "aorist" in row[5] and "indicative" in row[5]


def test_a_short_morphology_value_keeps_its_name():
    """`lang: A` is Aramaic; a bare `A` in a row of Hebrew would say nothing."""
    doc = json.loads(json.dumps(DOC))
    doc["scripture_pipelines"]["morphology"]["n40019001001"] = {"pos": "noun", "lang": "A"}
    row = _rows(usj_to_analysis(doc))[0].split("\t")
    assert row[5] == "noun lang=A"


def test_every_tree_node_is_kept(text):
    """Six nodes in the two trees, so six opening brackets, and every word in them by number."""
    trees = [line for line in text.splitlines() if line.startswith("(")]
    assert len(trees) == 2
    assert sum(tree.count("(") for tree in trees) == 6
    assert "ἐγένετο/2" in trees[0] and "ὅτε/3" in trees[1]


def test_a_node_keeps_its_role_and_attributes(text):
    assert "(cl clauseType=main (verb:v ἐγένετο/2))" in text


def test_glosses_are_english_only(text):
    assert "就" not in text and "成" not in text
    assert "And" in text and "now" in text, "both English glosses survive"


def test_the_sense_is_carried_and_says_what_it_is(text):
    """A bare `34.22` was read by a model as "occurs 34×" when the prompt asked for a count and
    the word had none — measured on MAT 19:1-11. Every number names what it is."""
    assert _rows(text)[0].split("\t")[6] == "LN 91.1"


def test_frequency_is_on_its_word_and_says_what_it_is(text):
    cell = _rows(text)[1].split("\t")[8]
    assert cell == "669× in GNT · 99.9%"


def test_a_word_outside_the_passage_is_marked(text):
    assert _rows(text)[2].rstrip().endswith("outside")
    assert not _rows(text)[0].rstrip().endswith("outside")


def test_a_family_with_no_column_travels_as_json_and_is_not_dropped(text):
    assert "referents" in text and "Jesus" in text


def test_it_is_unicode_never_escaped(text):
    assert "\\u" not in text


# --- through the scripture step ------------------------------------------------------


def test_analysis_needs_ids():
    from llmflow.utils.scripture import check_include

    with pytest.raises(ValueError, match="ids"):
        check_include(["morphology"], "analysis")


def test_the_language_accepts_it():
    from llmflow.pipeline_schema import SCRIPTURE_FORMATS

    assert "analysis" in SCRIPTURE_FORMATS


MACULA_GREEK = Path("/Users/jonathan/github/Clear/macula-greek/SBLGNT")
real_data = pytest.mark.skipif(
    not (MACULA_GREEK / "lowfat").is_dir(), reason="the Macula Greek corpus is not on this machine"
)
SBLGNT = {"SBLGNT": {
    "kind": "tsv", "path": str(MACULA_GREEK / "tsv/macula-greek-SBLGNT.tsv"),
    "versification_scheme": "org", "lowfat_path": str(MACULA_GREEK / "lowfat"),
}}
FAMILIES = ["ids", "morphology", "senses", "glosses", "syntax", "frequency"]


def _word_ids(node, out):
    if isinstance(node, dict):
        if node.get("marker") == "w":
            out.append(node.get("srcloc"))
        for child in node.get("content") or []:
            _word_ids(child, out)
    return out


def _tree_nodes(node):
    return 1 + sum(_tree_nodes(child) for child in node.get("children", []))


@real_data
@pytest.mark.parametrize("passage", ["MRK 1:1-8", "MAT 19:1-11"])
def test_it_carries_what_the_usj_form_carries(passage):
    from llmflow.utils.scripture import resource_text

    usj = resource_text("SBLGNT", passage, fmt="usj", resources=SBLGNT, include=FAMILIES)
    text = resource_text("SBLGNT", passage, fmt="analysis", resources=SBLGNT, include=FAMILIES)

    assert [row.split("\t")[2] for row in _rows(text)] == _word_ids({"content": usj["content"]}, [])
    trees = [line for line in text.splitlines() if line.startswith("(")]
    assert sum(t.count("(") for t in trees) == sum(
        _tree_nodes(s) for s in usj["scripture_pipelines"]["syntax"]
    )


@real_data
def test_it_is_far_smaller_than_the_usj_form():
    import tiktoken

    from llmflow.utils.scripture import resource_text

    encode = tiktoken.get_encoding("o200k_base").encode
    usj = resource_text("SBLGNT", "MAT 19:1-11", fmt="usj", resources=SBLGNT, include=FAMILIES)
    text = resource_text("SBLGNT", "MAT 19:1-11", fmt="analysis", resources=SBLGNT, include=FAMILIES)
    as_sent = json.dumps(usj, ensure_ascii=False, separators=(",", ":"))
    assert len(encode(text)) < 0.6 * len(encode(as_sent))
