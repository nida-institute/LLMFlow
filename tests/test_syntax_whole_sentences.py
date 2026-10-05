"""With `include: [syntax]`, a `scripture` step returns every word of every sentence it touches (#267).

The tree of a sentence the passage meets is carried whole, so the words must be too: a tree naming
words the payload does not contain leaves a participle without the verb it depends on. The text
widens with the analyses, in every format, and each word outside the requested verses is marked.
"""

import json
from pathlib import Path

import pytest

from llmflow import load_pipeline
from llmflow import paths as _paths

COLUMNS = ["xml:id", "ref", "text", "after", "lemma", "class"]

#: Three verses. Verse 1 is a sentence of its own; one sentence runs from verse 2 into verse 3.
WORDS = [
    ("n41001001001", "MRK 1:1!1", "Ἀρχὴ", " ", "ἀρχή", "noun"),
    ("n41001001002", "MRK 1:1!2", "εὐαγγελίου", " ", "εὐαγγέλιον", "noun"),
    ("n41001002001", "MRK 1:2!1", "Καθὼς", " ", "καθώς", "conj"),
    ("n41001002002", "MRK 1:2!2", "γέγραπται", " ", "γράφω", "verb"),
    ("n41001003001", "MRK 1:3!1", "φωνὴ", " ", "φωνή", "noun"),
    ("n41001003002", "MRK 1:3!2", "βοῶντος", "", "βοάω", "verb"),
]

LOWFAT = """<book>
<sentence><p>a</p><wg class="cl">
  <w xml:id="n41001001001" ref="MRK 1:1!1">Ἀρχὴ</w>
  <w xml:id="n41001001002" ref="MRK 1:1!2">εὐαγγελίου</w>
</wg></sentence>
<sentence><p>b</p><wg class="cl">
  <w xml:id="n41001002001" ref="MRK 1:2!1">Καθὼς</w>
  <w xml:id="n41001002002" ref="MRK 1:2!2">γέγραπται</w>
  <w xml:id="n41001003001" ref="MRK 1:3!1">φωνὴ</w>
  <w xml:id="n41001003002" ref="MRK 1:3!2">βοῶντος</w>
</wg></sentence>
</book>
"""

VERSE_2 = {"n41001002001", "n41001002002"}


@pytest.fixture
def registered(tmp_path, monkeypatch):
    """A registered Greek resource with a TSV and a Lowfat directory, both synthetic."""
    tsv = tmp_path / "words.tsv"
    tsv.write_text(
        "\t".join(COLUMNS) + "\n" + "".join("\t".join(row) + "\n" for row in WORDS),
        encoding="utf-8",
    )
    lowfat = tmp_path / "lowfat"
    lowfat.mkdir()
    (lowfat / "mark.xml").write_text(LOWFAT, encoding="utf-8")

    store = tmp_path / "store"
    (store / "registrations").mkdir(parents=True)
    monkeypatch.setenv(_paths.SP_HOME_ENV, str(store))
    (store / "registrations" / "TESTGRK.yaml").write_text(
        "id: TESTGRK\n"
        "kind: tsv\n"
        "versification_scheme: org\n"
        f"path: {tsv}\n"
        f"lowfat_path: {lowfat}\n",
        encoding="utf-8",
    )
    return "TESTGRK"


def run(tmp_path, passage, fmt, include):
    out = tmp_path / "out.json"
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(
        "name: whole-sentences\n"
        "steps:\n"
        "  - name: greek\n"
        "    type: scripture\n"
        "    resource: TESTGRK\n"
        f'    passage: "{passage}"\n'
        f"    format: {fmt}\n"
        f"    include: [{', '.join(include)}]\n"
        "    output: greek\n"
        f"    saveas: {out}\n",
        encoding="utf-8",
    )
    load_pipeline(pipeline).run()
    text = out.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def word_ids(usj):
    found = []

    def walk(node):
        if isinstance(node, dict):
            if "srcloc" in node:
                found.append(node["srcloc"])
            for child in node.get("content", []):
                walk(child)

    walk(usj)
    return found


def test_usj_carries_the_words_of_a_sentence_that_starts_before_the_passage(tmp_path, registered):
    usj = run(tmp_path, "MRK 1:3", "usj", ["ids", "syntax"])

    assert word_ids(usj) == [
        "n41001002001", "n41001002002", "n41001003001", "n41001003002"
    ], "the sentence from 1:2 is carried whole, words as well as tree"


def test_every_word_a_tree_names_is_in_the_document(tmp_path, registered):
    usj = run(tmp_path, "MRK 1:3", "usj", ["ids", "syntax"])

    def leaves(node):
        if "token" in node:
            return [node["token"]]
        return [t for child in node.get("children", []) for t in leaves(child)]

    named = {t for entry in usj["scripture_pipelines"]["syntax"] for t in leaves(entry)}
    assert named <= set(word_ids(usj))


def test_the_words_outside_the_requested_verses_are_marked(tmp_path, registered):
    usj = run(tmp_path, "MRK 1:3", "usj", ["ids", "syntax"])

    assert usj["scripture_pipelines"]["outside_passage"] == {i: True for i in sorted(VERSE_2)}


def test_the_other_families_are_carried_for_the_widened_words(tmp_path, registered):
    usj = run(tmp_path, "MRK 1:3", "usj", ["ids", "morphology", "syntax"])

    assert VERSE_2 <= set(usj["scripture_pipelines"]["morphology"])


def test_the_text_widens_in_milestones_format_too(tmp_path, registered):
    result = run(tmp_path, "MRK 1:3", "milestones", ["ids", "syntax"])

    assert "Καθὼς" in result["text"], "text and analyses agree on which words are present"
    assert "⌊1:2⌋" in result["text"]


def test_a_passage_on_sentence_boundaries_is_unchanged(tmp_path, registered):
    usj = run(tmp_path, "MRK 1:1", "usj", ["ids", "syntax"])

    assert word_ids(usj) == ["n41001001001", "n41001001002"]
    assert usj["scripture_pipelines"]["outside_passage"] == {}, "asked, and nothing was outside"


MACULA_GREEK = Path("/Users/jonathan/github/Clear/macula-greek/SBLGNT")

real_data = pytest.mark.skipif(
    not (MACULA_GREEK / "lowfat").is_dir(), reason="the Macula Greek corpus is not on this machine"
)

SBLGNT = {
    "SBLGNT": {
        "kind": "tsv",
        "path": str(MACULA_GREEK / "tsv/macula-greek-SBLGNT.tsv"),
        "versification_scheme": "org",
        "lowfat_path": str(MACULA_GREEK / "lowfat"),
    }
}


@real_data
def test_mark_1_3_8_carries_the_twenty_words_of_1_2():
    """The sentence opening `Καθὼς γέγραπται` in 1:2 runs into the passage."""
    from llmflow.utils.scripture import resource_text

    usj = resource_text("SBLGNT", "MRK 1:3-8", fmt="usj", resources=SBLGNT, include=["ids", "syntax"])
    outside = usj["scripture_pipelines"]["outside_passage"]

    assert len(outside) == 20
    assert all(identifier.startswith("n41001002") for identifier in outside)


@real_data
def test_matthew_19_1_11_meets_no_sentence_beyond_it():
    from llmflow.utils.scripture import resource_text

    usj = resource_text("SBLGNT", "MAT 19:1-11", fmt="usj", resources=SBLGNT, include=["ids", "syntax"])

    assert usj["scripture_pipelines"]["outside_passage"] == {}


def test_without_syntax_nothing_widens(tmp_path, registered):
    usj = run(tmp_path, "MRK 1:3", "usj", ["ids"])

    assert word_ids(usj) == ["n41001003001", "n41001003002"]
    assert "outside_passage" not in usj["scripture_pipelines"]
