"""`include: [senses]` on SBLGNT, with each Louw-Nida code joined to its SDGNT entry (#272).

A word's `ln` names one or more codes. Each becomes an entry in `entries`, joined on the word's
lemma and the code, because one code can be filed under several headwords with a definition each.
Where the lemma does not match, a code SDGNT files under exactly one headword still joins, and the
entry carries that headword as `lemma`; a code filed under several, or under none, has no entry
and is named in a warning.

Every expected value comes from `SDGNT` and `WORDS` below, which are written for these tests. No
assertion names a figure read off the real dictionary: a count taken from that file measures the
data rather than the code. The measurements are in `design-ears-to-hear-resources.md`.
"""

from __future__ import annotations

import csv
import logging

import pytest

from llmflow import paths as _paths
from llmflow.utils.scripture import CONTAINER_KEY, resource_text

#: Where the dictionary sits inside the dataset, as the open-licence repository lays it out.
DICTIONARY = "dictionaries/greek/XML/UBSGreekNTDic-v1.1-en.XML"

#: The shapes the join has to get right:
#:
#:   - Παῦλος `93.1`, a code under its own lemma
#:   - ἀγαθός `65.20` and `88.1`, two codes under one lemma
#:   - αὐτός `92.11`, a code filed under one headword that another word carries
#:   - ἄγω and ὁράω, both `91.13`, a code filed under two headwords
#:   - ὕψος `12.7{N:001}`, `12.8{N:001}` and `12.9`, the suffix on either side or both
SDGNT = """<?xml version="1.0" encoding="utf-8"?>
<Lexicon>
{entries}
</Lexicon>
"""

MEANING = """      <LEXMeaning Id="{id}" IsBiblicalTerm="{term}" EntryCode="{code}" Indent="0">
        <LEXDomains><LEXDomain Code="{domain_code}">{domain}</LEXDomain></LEXDomains>
        <LEXSubDomains><LEXSubDomain Code="{subdomain_code}">{subdomain}</LEXSubDomain></LEXSubDomains>
        <LEXSenses>
          <LEXSense LanguageCode="en">
            <DefinitionLong />
            <DefinitionShort>{definition}</DefinitionShort>
            <Glosses>{glosses}</Glosses>
          </LEXSense>
        </LEXSenses>
      </LEXMeaning>"""

ENTRY = """  <Lexicon_Entry Id="{id}" Lemma="{lemma}">
    <BaseForms><BaseForm><LEXMeanings>
{meanings}
    </LEXMeanings></BaseForm></BaseForms>
  </Lexicon_Entry>"""

#: `(lemma, code, domain, subdomain, definition, glosses, biblical term)`, one per meaning.
#: Glosses are `|`-separated; most meanings in the real dictionary have more than one.
MEANINGS = [
    ("Παῦλος", "93.1", "Names of Persons and Places", "Persons", "a person named Paul", "Paul", "Y"),
    ("ἀγαθός", "65.20", "Value", "Good, Bad", "positive moral qualities", "good|useful", "N"),
    ("ἀγαθός", "88.1", "Moral and Ethical Qualities", "Goodness", "of good character", "good", "N"),
    ("αὐτός", "92.11", "Discourse Referentials", "Reciprocal",
     "a reflexive reference (see {D:92.1}){N:001}", "self", "N"),
    ("ἄγω", "91.13", "Discourse Markers", "Prompters", "a prompter of attention", "come", "N"),
    ("ὁράω", "91.13", "Discourse Markers", "Prompters", "a prompter of attention", "look", "N"),
    ("ὕψος", "12.7{N:001}", "Supernatural Beings", "Supernatural", "a heavenly height", "high", "N"),
    ("ὕψος", "12.8{N:001}", "Supernatural Beings", "Supernatural", "the heavenly realm", "height", "N"),
    ("ὕψος", "12.9", "Supernatural Beings", "Supernatural", "the highest place", "heaven", "N"),
]


def sdgnt_xml() -> str:
    """`MEANINGS` as SDGNT's XML, one `Lexicon_Entry` per lemma."""
    by_lemma: dict = {}
    for lemma, *rest in MEANINGS:
        by_lemma.setdefault(lemma, []).append(rest)
    entries = []
    for number, (lemma, meanings) in enumerate(by_lemma.items(), start=1):
        rendered = [
            MEANING.format(
                id=f"{number:06d}{index:03d}", term=term, code=code, domain=domain,
                domain_code="000", subdomain=subdomain, subdomain_code="000000",
                definition=definition,
                glosses="".join(f"<Gloss>{gloss}</Gloss>" for gloss in glosses.split("|")),
            )
            for index, (code, domain, subdomain, definition, glosses, term) in enumerate(meanings, 1)
        ]
        entries.append(ENTRY.format(id=f"{number:06d}", lemma=lemma, meanings="\n".join(rendered)))
    return SDGNT.format(entries="\n".join(entries))


#: One word per case, in PHM 1:1. `(lemma, domain, ln)`.
WORDS = [
    ("Παῦλος", "093001", "93.1"),
    ("ἀγαθός", "065001 088001", "65.20 88.1"),
    ("ἑαυτοῦ", "092001", "92.11"),
    ("ἰδού", "091001", "91.13"),
    ("ὕψος", "012001", "12.7{N:001}"),
    ("ὕψος", "012001", "12.8"),
    ("ὕψος", "012001", "12.9{N:001}"),
    ("λόγος", "033001", "33.403"),
]

COLUMNS = ["ref", "xml:id", "text", "after", "lemma", "domain", "ln"]


def word_id(position: int) -> str:
    return f"n57001001{position:03d}"


def write_tsv(path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        for position, (lemma, domain, ln) in enumerate(WORDS, start=1):
            writer.writerow({
                "ref": f"PHM 1:1!{position}", "xml:id": word_id(position), "text": lemma,
                "after": " ", "lemma": lemma, "domain": domain, "ln": ln,
            })


@pytest.fixture
def resources(tmp_path):
    """SBLGNT, and a second resource reading the same rows that no dictionary is declared for."""
    tsv = tmp_path / "macula-greek-SBLGNT.tsv"
    write_tsv(tsv)
    definition = {"kind": "tsv", "path": str(tsv), "versification_scheme": "org"}
    return {"SBLGNT": dict(definition), "UNDECLARED": dict(definition)}


@pytest.fixture
def registered(tmp_path):
    """SDGNT on this machine, registered as the dataset `ubs-sdgnt`."""
    root = tmp_path / "ubs-open-license"
    target = root / DICTIONARY
    target.parent.mkdir(parents=True)
    target.write_text(sdgnt_xml(), encoding="utf-8")
    datasets = _paths.sp_home() / "datasets"
    datasets.mkdir(parents=True, exist_ok=True)
    (datasets / "ubs-sdgnt.yaml").write_text(
        f"id: ubs-sdgnt\nname: ubs-sdgnt\npath: {root}\nformat: xml\n", encoding="utf-8"
    )
    return root


def senses(resources, resource="SBLGNT") -> dict:
    document = resource_text(
        resource, "PHM 1:1", fmt="usj", resources=resources, include=["ids", "senses"]
    )
    return document[CONTAINER_KEY]["senses"]


def entries(resources, position: int) -> list:
    return senses(resources)[word_id(position)].get("entries", [])


def codes(found: list) -> list:
    return [entry["code"] for entry in found]


class TestAnEntryPerCode:
    def test_a_code_under_its_own_lemma_carries_the_dictionary_s_fields(
        self, resources, registered
    ):
        assert entries(resources, 1) == [
            {
                "code": "93.1",
                "lemma": "Παῦλος",
                "domain": "Names of Persons and Places",
                "subdomain": "Persons",
                "definition": "a person named Paul",
                "glosses": ["Paul"],
                "biblical_term": "Y",
            }
        ]

    def test_every_gloss_is_kept_in_the_dictionary_s_order(self, resources, registered):
        assert entries(resources, 2)[0]["glosses"] == ["good", "useful"]

    def test_a_definition_s_own_markup_is_carried_verbatim(self, resources, registered):
        """`{D:…}` cross-references and `{N:…}` note markers are the dictionary's, and stay."""
        assert entries(resources, 3)[0]["definition"] == "a reflexive reference (see {D:92.1}){N:001}"

    def test_the_source_columns_are_kept_beside_the_entries(self, resources, registered):
        sense = senses(resources)[word_id(1)]
        assert sense["domain"] == "093001" and sense["ln"] == "93.1"

    def test_a_word_with_two_codes_gets_both_in_order(self, resources, registered):
        found = entries(resources, 2)
        assert codes(found) == ["65.20", "88.1"]
        assert [entry["subdomain"] for entry in found] == ["Good, Bad", "Goodness"]


class TestTheSuffixIsNotPartOfTheCode:
    """`{N:001}` is written on some codes, by Macula and by SDGNT, and on different ones."""

    def test_on_both_sides(self, resources, registered):
        assert [entry["glosses"] for entry in entries(resources, 5)] == [["high"]]

    def test_on_the_dictionary_s_side_only(self, resources, registered):
        assert [entry["glosses"] for entry in entries(resources, 6)] == [["height"]]

    def test_on_the_word_s_side_only(self, resources, registered):
        assert [entry["glosses"] for entry in entries(resources, 7)] == [["heaven"]]

    def test_an_entry_names_the_code_without_it(self, resources, registered):
        assert codes(entries(resources, 7)) == ["12.9"]


class TestALemmaThatDoesNotMatch:
    def test_a_code_under_one_other_headword_joins_and_names_it(self, resources, registered):
        """ἑαυτοῦ's `92.11` is filed under αὐτός. The code names the meaning, so it is the entry."""
        found = entries(resources, 3)
        assert codes(found) == ["92.11"]
        assert found[0]["lemma"] == "αὐτός"

    def test_a_code_under_several_other_headwords_has_no_entry(self, resources, registered):
        assert entries(resources, 4) == []

    def test_and_the_warning_names_the_word_and_the_code(self, resources, registered, caplog):
        with caplog.at_level(logging.WARNING):
            senses(resources)
        assert any("91.13" in r.getMessage() and "ἰδού" in r.getMessage() for r in caplog.records)


class TestACodeTheDictionaryLacks:
    def test_has_no_entry(self, resources, registered):
        assert entries(resources, 8) == []

    def test_and_is_named_in_a_warning(self, resources, registered, caplog):
        with caplog.at_level(logging.WARNING):
            senses(resources)
        assert any("33.403" in r.getMessage() for r in caplog.records)


class TestWithoutTheDictionary:
    def test_senses_are_as_the_source_states_them(self, resources):
        """Not registered: the columns, and no `entries` key at all."""
        assert senses(resources)[word_id(1)] == {"domain": "093001", "ln": "93.1"}

    def test_one_warning_names_what_to_register(self, resources, caplog):
        with caplog.at_level(logging.WARNING):
            senses(resources)
        naming = [r for r in caplog.records if "ubs-sdgnt" in r.getMessage()]
        assert len(naming) == 1


class TestAResourceNoDictionaryIsDeclaredFor:
    def test_gets_no_entries(self, resources, registered):
        found = senses(resources, "UNDECLARED")
        assert all("entries" not in sense for sense in found.values())

    def test_and_no_warning_about_it(self, resources, registered, caplog):
        """Most texts have no SDGNT and never will; saying so on every request is noise."""
        with caplog.at_level(logging.WARNING):
            senses(resources, "UNDECLARED")
        assert not [r for r in caplog.records if "ubs-sdgnt" in r.getMessage()]


class TestTheDeclaration:
    def test_sblgnt_names_the_dictionary_through_its_dataset(self):
        from llmflow.utils.scripture import _family

        declared = _family("senses").get("dictionaries", {})
        assert declared.get("SBLGNT") == f"ubs-sdgnt/{DICTIONARY}"
