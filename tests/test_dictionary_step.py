"""`type: dictionary` — Tyndale Open Bible Dictionary articles, by title (#272).

ACAI names each entity's Tyndale articles by an id and a title. The id is the Aquifer adaptation's,
and the text served is Tyndale's own release, which has no ids: so an article is found by its
title. Tyndale marks some titles with `*`; a request matches without it, and the article comes back
with its title as Tyndale wrote it.

    {"articles": [{"title", "name", "body"}], "attribution": "…"}

Every expected value comes from `ARTICLES` below, which are written for these tests. The
measurements are in `design-ears-to-hear-resources.md`.
"""

from __future__ import annotations

import json
import logging

import pytest

from llmflow import load_pipeline
from llmflow import paths as _paths

#: `(file, name, title, body)`. The shapes the step has to get right:
#:
#:   - Daric, whose title Tyndale writes `Daric*`
#:   - the two John articles ACAI's sample names for `person:John`
#:   - Philemon, whose body carries Tyndale's own links
ARTICLES = [
    ("D.xml", "Daric", "Daric*", '<p class="h1">DARIC*</p><p class="fl">Persian gold coin.</p>'),
    ("J.xml", "JohntheBaptist", "John the Baptist", '<p class="h1">JOHN THE BAPTIST</p><p class="fl">Prophet.</p>'),
    ("J.xml", "JohnGospelof", "John, Gospel of", '<p class="h1">JOHN, GOSPEL OF</p><p class="fl">Fourth Gospel.</p>'),
    ("P.xml", "PhilemonPerson", "Philemon (Person)",
     '<p class="fl">Christian addressed in <a href="?bref=Phlm.1.1">Phlm 1:1</a>.</p>'),
]


def build_sample(root) -> None:
    """`ARTICLES` as Tyndale lays them out: one file per letter, a letter index item first."""
    by_file: dict = {}
    for file, name, title, body in ARTICLES:
        by_file.setdefault(file, []).append(
            f'<item typename="Article" product="TyndaleOpenBibleDictionary" name="{name}">\n'
            f"  <title>{title}</title>\n  <body>{body}</body>\n</item>"
        )
    (root / "Articles").mkdir(parents=True)
    for file, items in by_file.items():
        letter = file[0]
        index = (
            f'<item typename="DictionaryLetter" name="{letter}" product="TyndaleBibleDict">\n'
            f'  <body><p class="h1">{letter}</p></body>\n</item>'
        )
        (root / "Articles" / file).write_text(
            '<items release="1.6">\n' + "\n".join([index, *items]) + "\n</items>\n", encoding="utf-8"
        )


@pytest.fixture
def store(tmp_path, monkeypatch):
    home = tmp_path / "store"
    (home / "registrations").mkdir(parents=True)
    (home / "datasets").mkdir()
    monkeypatch.setenv(_paths.SP_HOME_ENV, str(home))
    return home


@pytest.fixture
def registered(tmp_path, store):
    """The dictionary on this machine, registered as `tyndale-open-bible-dictionary`."""
    root = tmp_path / "tyndale"
    build_sample(root)
    (store / "datasets" / "tyndale-open-bible-dictionary.yaml").write_text(
        f"id: tyndale-open-bible-dictionary\nname: Tyndale\npath: {root}\nformat: xml\n",
        encoding="utf-8",
    )
    return root


def build(tmp_path, keys: str):
    out = tmp_path / "articles.json"
    pipeline = tmp_path / "dictionary.yaml"
    pipeline.write_text(
        "name: dictionary-under-test\n"
        "steps:\n"
        "  - name: articles\n"
        "    type: dictionary\n"
        f"{keys}"
        "    output: articles\n"
        f"    saveas: {out}\n",
        encoding="utf-8",
    )
    return load_pipeline(pipeline), out


def run(tmp_path, keys: str):
    pipeline, out = build(tmp_path, keys)
    pipeline.run()
    return json.loads(out.read_text(encoding="utf-8"))


def articles(tmp_path, *titles: str) -> list:
    listed = "".join(f'      - "{title}"\n' for title in titles)
    return run(tmp_path, f"    entries:\n{listed}")["articles"]


def step_directly(**keys):
    from llmflow.steps.dictionary import run_dictionary_step

    context: dict = {}
    run_dictionary_step({"name": "articles", "type": "dictionary", "output": "articles", **keys}, context)
    return context["articles"]


class TestTheStepIsInTheLanguage:
    def test_the_schema_declares_the_type_and_its_keys(self):
        from llmflow.pipeline_schema import allowed_step_keys

        allowed = allowed_step_keys("dictionary")
        assert allowed is not None, "the type is permissive — no schema branch declares it"
        assert {"entries", "acai"} <= allowed

    def test_a_well_formed_step_lints_clean(self, tmp_path, registered):
        pipeline, _ = build(tmp_path, '    entries: ["Daric"]\n')
        result = pipeline.lint()
        assert result.valid, result.errors

    @pytest.mark.parametrize("keys", [{}, {"entries": ["Daric"], "acai": {"entities": {}}}])
    def test_it_takes_entries_or_acai_and_not_both_or_neither(self, registered, keys):
        """Refused before the dictionary is read."""
        with pytest.raises(ValueError) as caught:
            step_directly(**keys)
        assert "entries" in str(caught.value) and "acai" in str(caught.value)


class TestLookup:
    def test_a_title_returns_the_article_and_its_verbatim_body(self, tmp_path, registered):
        assert articles(tmp_path, "Philemon (Person)") == [
            {
                "title": "Philemon (Person)",
                "name": "PhilemonPerson",
                "body": '<p class="fl">Christian addressed in <a href="?bref=Phlm.1.1">Phlm 1:1</a>.</p>',
            }
        ]

    def test_a_title_matches_without_tyndale_s_asterisk_and_keeps_it(self, tmp_path, registered):
        [found] = articles(tmp_path, "Daric")
        assert found["title"] == "Daric*" and found["name"] == "Daric"

    def test_an_acai_pair_is_looked_up_by_its_title(self, registered):
        found = step_directly(entries=[{"id": "100", "title": "John the Baptist"}])["articles"]
        assert [article["name"] for article in found] == ["JohntheBaptist"]

    def test_a_whole_acai_result_gives_every_article_its_entities_name_once(self, registered):
        acai = {
            "entities": {
                "person:John": {"dictionary": [
                    {"id": "100", "title": "John the Baptist"},
                    {"id": "101", "title": "John, Gospel of"},
                ]},
                "person:Philemon": {"dictionary": [{"id": "7708", "title": "Philemon (Person)"}]},
                "person:John.again": {"dictionary": [{"id": "100", "title": "John the Baptist"}]},
                "place:Jordan": {},
            },
            "verses": {},
        }
        found = step_directly(acai=acai)["articles"]
        assert [article["name"] for article in found] == [
            "JohntheBaptist", "JohnGospelof", "PhilemonPerson",
        ]

    def test_articles_come_in_the_order_asked_and_once(self, tmp_path, registered):
        found = articles(tmp_path, "Philemon (Person)", "Daric", "Philemon (Person)")
        assert [article["name"] for article in found] == ["PhilemonPerson", "Daric"]

    def test_a_title_tyndale_lacks_has_no_article_and_is_named(self, registered, caplog):
        with caplog.at_level(logging.WARNING):
            found = step_directly(entries=["Daric", "No Such Article"])["articles"]
        assert [article["name"] for article in found] == ["Daric"]
        assert any("No Such Article" in r.getMessage() for r in caplog.records)


class TestThePayload:
    def test_the_attribution_tyndale_s_licence_asks_for_travels_with_it(self, registered):
        attribution = step_directly(entries=["Daric"])["attribution"]
        assert "Tyndale House Publishers" in attribution and "CC BY-SA 4.0" in attribution


class TestRefusals:
    def test_lint_reports_the_dictionary_missing(self, store):
        from llmflow.utils import resource_preflight

        steps = [{"name": "articles", "type": "dictionary", "entries": ["Daric"]}]
        findings = resource_preflight.check(steps, {})
        missing = [f for f in findings if f.kind == "dataset" and f.resource == "tyndale-open-bible-dictionary"]
        assert missing and missing[0].is_error

    def test_the_step_refuses_without_it_and_names_the_command(self, store):
        with pytest.raises(ValueError) as caught:
            step_directly(entries=["Daric"])
        assert "sp dataset add tyndale-open-bible-dictionary" in str(caught.value)


class TestTheDeclaration:
    def test_names_the_dataset_the_files_and_the_language(self):
        from llmflow.utils.scripture import _data_path

        declared = json.loads(_data_path("tyndale.json").read_text(encoding="utf-8"))
        assert declared["dataset"] == "tyndale-open-bible-dictionary"
        assert declared["articles"] == "Articles/*.xml"
        assert declared["language"] == "eng"


class TestThroughTheCommandLine:
    def test_an_acai_step_feeds_the_dictionary_and_the_articles_land_on_disk(
        self, tmp_path, monkeypatch, registered, store
    ):
        """The design's route to articles by passage: an `acai` step, then a `dictionary` step."""
        from llmflow.cli import main
        from tests.test_acai_step import build_sample as build_acai

        acai_root = tmp_path / "ACAI"
        build_acai(acai_root)
        (store / "datasets" / "ACAI.yaml").write_text(
            f"id: ACAI\nname: ACAI\npath: {acai_root}\nformat: json\n", encoding="utf-8"
        )
        (store / "registrations" / "SBLGNT.yaml").write_text(
            "id: SBLGNT\nkind: tsv\nversification_scheme: org\n", encoding="utf-8"
        )

        out = tmp_path / "articles.json"
        pipeline = tmp_path / "articles.yaml"
        pipeline.write_text(
            "name: articles-for-a-passage\n"
            "steps:\n"
            "  - name: entities\n"
            "    type: acai\n"
            "    resource: SBLGNT\n"
            '    passage: "${passage}"\n'
            "    output: entities\n"
            "  - name: articles\n"
            "    type: dictionary\n"
            "    acai: ${entities}\n"
            "    output: articles\n"
            f"    saveas: {out}\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        main(["run", "--pipeline", str(pipeline), "--var", "passage=MRK 1:4"])

        saved = json.loads(out.read_text(encoding="utf-8"))
        assert [article["name"] for article in saved["articles"]] == ["JohntheBaptist", "JohnGospelof"]
