"""`include: [frequency]` — how often each word's lemma occurs in its corpus.

The counts come from tables generated once from Macula Lowfat and committed in `data/`: the Greek
New Testament for SBLGNT, the Hebrew Bible for WLC. Expected values are read from those tables, so
the tests follow the data rather than restating it.
"""

import json
from pathlib import Path

import pytest

from llmflow import load_pipeline
from llmflow import paths as _paths

DATA = Path(__file__).resolve().parent.parent / "data"


def table(name):
    lemmas = json.loads((DATA / name).read_text(encoding="utf-8"))["lemmas"]
    return {entry["lemma"]: entry for entry in lemmas}


GREEK = table("lemma-frequency-greek.json")
HEBREW = table("lemma-frequency-hebrew.json")

GREEK_COLUMNS = ["xml:id", "ref", "text", "after", "lemma"]
GREEK_ROWS = [
    ("n41001007014", "MRK 1:7!14", "κύψας", " ", "κύπτω"),
    ("n41001007015", "MRK 1:7!15", "λῦσαι", " ", "λύω"),
    ("n41001007017", "MRK 1:7!17", "ἱμάντα", "", "ἱμάς"),
]

HEBREW_COLUMNS = ["xml:id", "ref", "text", "after", "lemma", "pos", "lang"]
HEBREW_ROWS = [
    ("o010020210041", "GEN 2:21!4", "תַּרְדֵּמָה", " ", "תַּרְדֵּמָה", "noun", "H"),
    ("o010320010063", "GEN 2:21!5", "בְנוֹתָ", "", "בַּת", "noun", "H"),
    ("o010320010064", "GEN 2:21!5", "י", " ", "הוּא", "suffix", "H"),
]


def write_tsv(path, columns, rows):
    path.write_text(
        "\t".join(columns) + "\n" + "".join("\t".join(row) + "\n" for row in rows),
        encoding="utf-8",
    )


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Three registered resources: SBLGNT and WLC with synthetic text, and one with no table."""
    greek = tmp_path / "greek.tsv"
    hebrew = tmp_path / "hebrew.tsv"
    write_tsv(greek, GREEK_COLUMNS, GREEK_ROWS)
    write_tsv(hebrew, HEBREW_COLUMNS, HEBREW_ROWS)

    registrations = tmp_path / "store" / "registrations"
    registrations.mkdir(parents=True)
    monkeypatch.setenv(_paths.SP_HOME_ENV, str(tmp_path / "store"))
    for name, path in (("SBLGNT", greek), ("WLC", hebrew), ("OTHERGRK", greek)):
        (registrations / f"{name}.yaml").write_text(
            f"id: {name}\nkind: tsv\nversification_scheme: org\npath: {path}\n",
            encoding="utf-8",
        )
    return tmp_path


def run(tmp_path, resource, passage, fmt="usj", include=("ids", "frequency")):
    out = tmp_path / "out.json"
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(
        "name: frequency\n"
        "steps:\n"
        "  - name: text\n"
        "    type: scripture\n"
        f"    resource: {resource}\n"
        f'    passage: "{passage}"\n'
        f"    format: {fmt}\n"
        f"    include: [{', '.join(include)}]\n"
        "    output: text\n"
        f"    saveas: {out}\n",
        encoding="utf-8",
    )
    load_pipeline(pipeline).run()
    return json.loads(out.read_text(encoding="utf-8"))


def test_each_greek_word_carries_its_lemmas_frequency_in_the_gnt(store):
    usj = run(store, "SBLGNT", "MRK 1:7")
    frequency = usj["scripture_pipelines"]["frequency"]

    assert frequency["n41001007014"] == {
        "corpus": "GNT",
        "count": GREEK["κύπτω"]["count"],
        "in_least_frequent_percent": GREEK["κύπτω"]["in_least_frequent_percent"],
    }
    assert frequency["n41001007017"]["count"] == GREEK["ἱμάς"]["count"]


def test_a_hebrew_word_is_counted_in_the_hebrew_bible(store):
    usj = run(store, "WLC", "GEN 2:21")
    frequency = usj["scripture_pipelines"]["frequency"]

    assert frequency["o010020210041"] == {
        "corpus": "HOT",
        "count": HEBREW["תַּרְדֵּמָה"]["count"],
        "in_least_frequent_percent": HEBREW["תַּרְדֵּמָה"]["in_least_frequent_percent"],
    }


def test_a_pronominal_suffix_is_left_out_as_the_table_leaves_it_out(store):
    """The table was counted without suffixes, which carry the independent pronoun's lemma."""
    usj = run(store, "WLC", "GEN 2:21")

    assert "o010320010064" not in usj["scripture_pipelines"]["frequency"]
    assert "o010320010063" in usj["scripture_pipelines"]["frequency"]


def test_frequency_travels_beside_milestones_text_too(store):
    result = run(store, "SBLGNT", "MRK 1:7", fmt="milestones")

    assert result["scripture_pipelines"]["frequency"]["n41001007015"]["corpus"] == "GNT"


def test_a_resource_with_no_corpus_table_answers_null(store, caplog):
    """The question could not be asked, which is a different fact from asked and found nothing."""
    with caplog.at_level("WARNING"):
        usj = run(store, "OTHERGRK", "MRK 1:7")

    assert usj["scripture_pipelines"]["frequency"] is None
    assert any("frequency" in record.message for record in caplog.records)


def test_frequency_needs_ids_beside_it():
    from llmflow.utils.scripture import check_include

    with pytest.raises(ValueError, match="needs `ids` beside it"):
        check_include(["frequency"], "usj")
