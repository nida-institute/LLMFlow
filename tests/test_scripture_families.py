"""`include:` families, and why the same declaration serves two languages.

Greek and Hebrew are different languages and their analyses differ. A family therefore emits
whichever of its declared columns the edition actually has, and nothing merges the two systems: a
Greek verb has `tense`, `voice` and `mood`; a Hebrew verb has `stem` and `state`. A Greek sense is
a Louw-Nida number in `domain`/`ln`; a Hebrew sense is an SDBH domain in `lexdomain` and its
neighbours.

Container field names are the source's column names, verbatim, so a consumer can trace any field
back to a column. The two exceptions are `lemma` and `strong`, which USX already defines as
attributes on a `w` element and which therefore go there instead.
"""
import json
import re
from pathlib import Path

import pytest

from llmflow import file_catalog as fc
from llmflow.utils.scripture import (
    CONTAINER_KEY,
    IMPLEMENTED_FAMILIES,
    INCLUDE_FAMILIES,
    USJ_SRCLOC,
    family_columns,
    rows_to_usj,
)

# One Greek word, carrying the columns the Macula Greek TSV provides.
GREEK_ROWS = [
    {
        "ref": "PHM 1:1!1", "xml:id": "n57001001001", "text": "Παῦλος", "after": " ",
        "lemma": "Παῦλος", "strong": "G3972", "morph": "N-NSM-P",
        "class": "noun", "role": "s", "type": "proper", "person": "", "number": "singular",
        "gender": "masculine", "case": "nominative", "tense": "", "voice": "", "mood": "",
        "degree": "", "domain": "093001", "ln": "93.1", "gloss": "Paul", "english": "Paul",
        "mandarin": "保罗", "referent": "n57001001001", "subjref": "", "frame": "",
        "normalized": "Παυλος",
    },
]

# One Hebrew word, carrying the columns the Macula Hebrew TSV provides instead.
HEBREW_ROWS = [
    {
        "ref": "RUT 1:1!1", "xml:id": "o080010010011", "text": "וַ", "after": "",
        "lemma": "ו", "strongnumberx": "H9001", "stronglemma": "ו", "morph": "C",
        "class": "conjunction", "type": "", "person": "", "number": "", "gender": "",
        "stem": "", "state": "", "pos": "conj", "lang": "H",
        "lexdomain": "", "contextualdomain": "", "coredomain": "", "sdbh": "", "sensenumber": "",
        "gloss": "and", "english": "and", "mandarin": "而",
        "participantref": "", "subjref": "", "transliteration": "wa",
    },
]


# ---------------------------------------------------------------------------
# The declaration
# ---------------------------------------------------------------------------


def test_every_declared_family_is_a_known_family():
    declared = set(json.loads(_declaration_path().read_text(encoding="utf-8"))["families"])
    assert declared == set(INCLUDE_FAMILIES)


def _declaration_path() -> Path:
    return Path(fc.__file__).resolve().parent.parent.parent / "data" / "include-families.json"


def test_morph_is_not_carried():
    """A packed morphology string duplicating the columns beside it is payload for no reader."""
    assert "morph" not in family_columns("morphology")


def test_the_four_families_are_implemented():
    for family in ("morphology", "senses", "glosses", "referents"):
        assert family in IMPLEMENTED_FAMILIES, family


# ---------------------------------------------------------------------------
# One declaration, two languages
# ---------------------------------------------------------------------------


def test_greek_morphology_emits_the_greek_categories():
    doc = rows_to_usj(GREEK_ROWS, "PHM", include=["ids", "morphology"])
    entry = doc[CONTAINER_KEY]["morphology"]["n57001001001"]
    assert entry["case"] == "nominative"
    assert entry["class"] == "noun"
    assert "stem" not in entry and "state" not in entry


def test_hebrew_morphology_emits_the_hebrew_categories():
    doc = rows_to_usj(HEBREW_ROWS, "RUT", include=["ids", "morphology"])
    entry = doc[CONTAINER_KEY]["morphology"]["o080010010011"]
    assert entry["pos"] == "conj"
    assert entry["lang"] == "H"
    assert "case" not in entry and "tense" not in entry


def test_an_empty_column_is_not_emitted():
    """The source leaves a category blank where it does not apply."""
    entry = rows_to_usj(GREEK_ROWS, "PHM", include=["ids", "morphology"])[CONTAINER_KEY][
        "morphology"
    ]["n57001001001"]
    assert "tense" not in entry and "person" not in entry


def test_greek_senses_are_louw_nida():
    doc = rows_to_usj(GREEK_ROWS, "PHM", include=["ids", "senses"])
    assert doc[CONTAINER_KEY]["senses"]["n57001001001"] == {"domain": "093001", "ln": "93.1"}


def test_a_hebrew_word_with_no_sense_data_yields_no_entry():
    doc = rows_to_usj(HEBREW_ROWS, "RUT", include=["ids", "senses"])
    assert doc[CONTAINER_KEY]["senses"] == {}


def test_glosses_share_their_column_names_across_both_editions():
    greek = rows_to_usj(GREEK_ROWS, "PHM", include=["ids", "glosses"])[CONTAINER_KEY]["glosses"]
    hebrew = rows_to_usj(HEBREW_ROWS, "RUT", include=["ids", "glosses"])[CONTAINER_KEY]["glosses"]
    assert greek["n57001001001"] == {"gloss": "Paul", "english": "Paul", "mandarin": "保罗"}
    assert hebrew["o080010010011"] == {"gloss": "and", "english": "and", "mandarin": "而"}


def test_referents_carry_each_edition_s_own_column():
    greek = rows_to_usj(GREEK_ROWS, "PHM", include=["ids", "referents"])[CONTAINER_KEY]["referents"]
    assert greek["n57001001001"] == {"referent": "n57001001001"}


def test_two_families_together_are_two_keys_not_one_merged_map():
    doc = rows_to_usj(GREEK_ROWS, "PHM", include=["ids", "morphology", "glosses"])
    container = doc[CONTAINER_KEY]
    assert set(container) >= {"morphology", "glosses"}
    assert "gloss" not in container["morphology"]["n57001001001"]


# ---------------------------------------------------------------------------
# lemma and strong are spec-defined, so they are attributes rather than container content
# ---------------------------------------------------------------------------


def test_lemma_and_strong_are_attributes_on_the_word_node():
    doc = rows_to_usj(GREEK_ROWS, "PHM", include=["ids", "morphology"])
    word = _first_word(doc)
    assert word["lemma"] == "Παῦλος"
    assert word["strong"] == "G3972"
    assert word[USJ_SRCLOC] == "n57001001001"


def test_the_hebrew_strong_column_fills_the_same_attribute():
    """Hebrew names its Strong's column `strongnumberx`; the destination is spec-defined."""
    doc = rows_to_usj(HEBREW_ROWS, "RUT", include=["ids", "morphology"])
    word = _first_word(doc)
    assert word["strong"] == "H9001"
    assert "strongnumberx" not in word


def test_lemma_is_absent_without_morphology():
    """The family delivers it; `format: usj` alone does not."""
    doc = rows_to_usj(GREEK_ROWS, "PHM", include=["ids"])
    assert "lemma" not in _first_word(doc)


def _first_word(doc):
    for node in doc["content"]:
        if node.get("type") == "para":
            for child in node["content"]:
                if isinstance(child, dict) and child.get("marker") == "w":
                    return child
    raise AssertionError("no word node in the document")


# ---------------------------------------------------------------------------
# A per-word family needs somewhere to join to
# ---------------------------------------------------------------------------


def test_a_per_word_family_without_ids_is_refused():
    """The container keys are word ids; without `ids` the document carries none to match."""
    with pytest.raises(ValueError, match="ids"):
        rows_to_usj(GREEK_ROWS, "PHM", include=["morphology"])


def test_discourse_does_not_require_ids():
    """Discourse items name their own word ids, so they stand without `srcloc`."""
    doc = rows_to_usj(GREEK_ROWS, "PHM", include=["discourse"], discourse=[])
    assert doc[CONTAINER_KEY]["discourse"] == []


# ---------------------------------------------------------------------------
# The document a consumer reads
# ---------------------------------------------------------------------------

#: A row of the shipped document's family table: the name, and whether it is built.
FAMILY_STATUS = re.compile(r"^\| `([a-z]+)` \| (built|not built) \|", re.M)

SCRIPTURE_DOC = "docs/ai-context/sp/scripture-representations.md"


def _shipped_document() -> str:
    """The scripture-representations text `sp init` installs, read through the catalog."""
    entry = next(e for e in fc.entries() if e.path == SCRIPTURE_DOC)
    content = fc.shipped_content(entry)
    assert content is not None, f"{SCRIPTURE_DOC} ships no content"
    return content


def test_the_shipped_document_states_which_families_are_built():
    """A consumer has no other way to find out, and asking for an unbuilt family raises."""
    status = dict(FAMILY_STATUS.findall(_shipped_document()))
    assert set(status) == set(INCLUDE_FAMILIES)
    built = {name for name, state in status.items() if state == "built"}
    assert built == set(IMPLEMENTED_FAMILIES)
