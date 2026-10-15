"""`type: acai` — the people, places and things ACAI names in a passage (#272).

ACAI is an analysis of SBLGNT and WLC, so it is served against those two resources and no other.
The payload states each entity once, and indexes the verses that name it:

    {"entities": {"<id>": {type, label, description, lemmas, dictionary}},
     "verses": {"<USFM verse>": [{"id", "key"}]}}

Every expected value comes from `SAMPLE` below, which is written for these tests. No assertion
names a figure read off the real release: a count taken from it measures the data rather than the
code. The measurements are in `design-ears-to-hear-resources.md`.
"""

from __future__ import annotations

import json
import logging

import pytest

from llmflow import load_pipeline
from llmflow import paths as _paths

#: `(category directory, entity)`. The shapes the step has to get right:
#:
#:   - John, named in MRK 1:4 and 1:6, a key reference in 1:4 only, with two Tyndale articles
#:     and a source that is not Tyndale
#:   - the Jordan, named in MRK 1:5, with no lemmas and no dictionary
#:   - a non-primary record of John, which is not an entity of its own
#:   - David, named in PSA 51:3 as ACAI numbers it, which an English reader calls 51:1
#:   - the Corinthians, named in 2CO 13:13 and in 2CO 13:14, a verse ACAI's own scheme lacks
SAMPLE = [
    ("people", {
        "id": "person:John", "primary_id": "person:John", "type": "person",
        "alternate_sources": {"aquifer": [
            "100|John the Baptist|TyndaleBibleDictionary",
            "101|John, Gospel of|TyndaleBibleDictionary",
            "900|John|BiblicaStudyNotesKeyTerms",
        ]},
        "localizations": {"eng": {"preferred_label": "John", "descriptions": [
            {"source": "acai", "description": "John the Baptist, who baptized in the Jordan."},
        ]}},
        "lemmas": {"el": ["Ἰωάννης"]},
        "key_references": ["41001004"],
        "references": ["41001004", "41001006"],
    }),
    ("places", {
        "id": "place:Jordan", "primary_id": "place:Jordan", "type": "place",
        "localizations": {"eng": {"preferred_label": "Jordan River", "descriptions": [
            {"source": "acai", "description": "The river John baptized in."},
        ]}},
        "key_references": [],
        "references": ["41001005"],
    }),
    ("people", {
        "id": "person:John.2", "primary_id": "person:John", "type": "person",
        "localizations": {"eng": {"preferred_label": "John (duplicate)"}},
        "references": ["41001004"],
    }),
    ("people", {
        "id": "person:David", "primary_id": "person:David", "type": "person",
        "localizations": {"eng": {"preferred_label": "David", "descriptions": [
            {"source": "acai", "description": "The king of Israel."},
        ]}},
        "key_references": ["19051003"],
        "references": ["19051003"],
    }),
    ("groups", {
        "id": "group:Corinth", "primary_id": "group:Corinth", "type": "group",
        "localizations": {"eng": {"preferred_label": "Corinthians"}},
        "references": ["47013013", "47013014"],
    }),
]


def build_sample(root) -> None:
    for directory, entity in SAMPLE:
        target = root / directory / "json" / f"{entity['id'].replace(':', '_')}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(entity, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def store(tmp_path, monkeypatch):
    """A store with SBLGNT and another resource registered, and ACAI not yet."""
    home = tmp_path / "store"
    (home / "registrations").mkdir(parents=True)
    (home / "datasets").mkdir()
    monkeypatch.setenv(_paths.SP_HOME_ENV, str(home))
    for name in ("SBLGNT", "OTHER"):
        (home / "registrations" / f"{name}.yaml").write_text(
            f"id: {name}\nkind: tsv\nversification_scheme: org\n", encoding="utf-8"
        )
    return home


@pytest.fixture
def registered(tmp_path, store):
    """ACAI on this machine, registered as the dataset `ACAI`."""
    root = tmp_path / "ACAI"
    build_sample(root)
    (store / "datasets" / "ACAI.yaml").write_text(
        f"id: ACAI\nname: ACAI\npath: {root}\nformat: json\n", encoding="utf-8"
    )
    return root


def build(tmp_path, passage, resource="SBLGNT", extra=""):
    """A one-step pipeline that saves the step's result as JSON."""
    out = tmp_path / "acai.json"
    pipeline = tmp_path / "acai.yaml"
    pipeline.write_text(
        "name: acai-under-test\n"
        "steps:\n"
        "  - name: entities\n"
        "    type: acai\n"
        f"    resource: {resource}\n"
        f'    passage: "{passage}"\n'
        f"{extra}"
        "    output: acai\n"
        f"    saveas: {out}\n",
        encoding="utf-8",
    )
    return load_pipeline(pipeline), out


def run(tmp_path, passage, resource="SBLGNT", extra=""):
    pipeline, out = build(tmp_path, passage, resource, extra)
    pipeline.run()
    return json.loads(out.read_text(encoding="utf-8"))


class TestTheStepIsInTheLanguage:
    def test_the_schema_declares_the_type_and_its_keys(self):
        from llmflow.pipeline_schema import allowed_step_keys

        allowed = allowed_step_keys("acai")
        assert allowed is not None, "the type is permissive — no schema branch declares it"
        assert {"resource", "passage", "versification"} <= allowed

    def test_a_well_formed_step_lints_clean(self, tmp_path, registered):
        pipeline, _ = build(tmp_path, "MRK 1:4-6")
        result = pipeline.lint()
        assert result.valid, result.errors

    def test_a_key_belonging_to_another_step_type_is_refused(self, tmp_path, registered):
        pipeline, _ = build(tmp_path, "MRK 1:4-6", extra="    include: [ids]\n")
        result = pipeline.lint()
        assert not result.valid
        assert any("include" in str(error) for error in result.errors)


class TestThePayload:
    def test_each_entity_once_and_the_verses_that_name_it(self, tmp_path, registered):
        assert run(tmp_path, "MRK 1:4-6") == {
            "entities": {
                "person:John": {
                    "type": "person",
                    "label": "John",
                    "description": "John the Baptist, who baptized in the Jordan.",
                    "lemmas": {"el": ["Ἰωάννης"]},
                    "dictionary": [
                        {"id": "100", "title": "John the Baptist"},
                        {"id": "101", "title": "John, Gospel of"},
                    ],
                },
                "place:Jordan": {
                    "type": "place",
                    "label": "Jordan River",
                    "description": "The river John baptized in.",
                },
            },
            "verses": {
                "MRK 1:4": [{"id": "person:John", "key": True}],
                "MRK 1:5": [{"id": "place:Jordan", "key": False}],
                "MRK 1:6": [{"id": "person:John", "key": False}],
            },
        }

    def test_the_verses_are_in_order(self, tmp_path, registered):
        assert list(run(tmp_path, "MRK 1:4-6")["verses"]) == ["MRK 1:4", "MRK 1:5", "MRK 1:6"]

    def test_a_non_primary_record_is_not_an_entity(self, tmp_path, registered):
        result = run(tmp_path, "MRK 1:4")
        assert list(result["entities"]) == ["person:John"]
        assert result["verses"]["MRK 1:4"] == [{"id": "person:John", "key": True}]

    def test_only_tyndale_articles_are_the_dictionary(self, tmp_path, registered):
        dictionary = run(tmp_path, "MRK 1:4")["entities"]["person:John"]["dictionary"]
        assert [article["id"] for article in dictionary] == ["100", "101"]

    def test_an_entity_with_no_lemmas_or_articles_has_neither_key(self, tmp_path, registered):
        jordan = run(tmp_path, "MRK 1:5")["entities"]["place:Jordan"]
        assert "lemmas" not in jordan and "dictionary" not in jordan

    def test_a_passage_naming_nothing_is_empty_not_null(self, tmp_path, registered):
        """Consulted, and nothing is named here."""
        assert run(tmp_path, "MRK 2:1") == {"entities": {}, "verses": {}}


class TestTheRequestIsMappedBeforeLookup:
    def test_a_reference_in_another_scheme_finds_the_verse(self, tmp_path, registered):
        """ACAI numbers in `org`, where the psalm's superscription is counted.

        The verse an English reader calls PSA 51:1 is 51:3 there. Unmapped, the request finds
        nothing and still reports success. The answer is labelled as ACAI numbers it.
        """
        result = run(tmp_path, "PSA 51:1", extra="    versification: eng\n")
        assert result["verses"] == {"PSA 51:3": [{"id": "person:David", "key": True}]}


class TestAReferenceOutsideACAIsOwnScheme:
    """ACAI numbers in `org`, where 2CO 13 has 13 verses; a reference to 13:14 is not a verse."""

    def test_is_dropped_and_the_entity_s_other_verses_stay(self, tmp_path, registered):
        result = run(tmp_path, "2CO 13:13")
        assert result["verses"] == {"2CO 13:13": [{"id": "group:Corinth", "key": False}]}

    def test_is_named_once_when_acai_is_read_not_on_every_lookup(self, registered, caplog):
        from llmflow.utils import acai

        acai.load.cache_clear()
        with caplog.at_level(logging.WARNING):
            index = acai.load(str(registered))
            acai.entities_for_passage(index, "2CO 13:13", "org")
            acai.entities_for_passage(index, "2CO 13:1-13", "org")
        naming = [r for r in caplog.records if "2CO 13:14" in r.getMessage()]
        assert len(naming) == 1
        assert "group:Corinth" in naming[0].getMessage()


class TestRefusals:
    def test_a_resource_acai_was_not_made_about_is_null(self, tmp_path, registered, caplog):
        """ACAI analyses SBLGNT and WLC; against another text its word choices would not hold."""
        with caplog.at_level(logging.WARNING):
            assert run(tmp_path, "MRK 1:4", resource="OTHER") is None
        assert any("OTHER" in r.getMessage() and "ACAI" in r.getMessage() for r in caplog.records)

    def test_the_run_refuses_without_acai_and_names_the_command(self, tmp_path, store, caplog):
        """Refused by the run's own lint, before any step has run."""
        pipeline, out = build(tmp_path, "MRK 1:4")
        with caplog.at_level(logging.ERROR), pytest.raises(SystemExit):
            pipeline.run()
        assert any("sp dataset add ACAI" in r.getMessage() for r in caplog.records)
        assert not out.exists()

    def test_the_step_refuses_without_acai_when_reached_directly(self, store):
        """The handler's own refusal, for a caller that did not lint first."""
        from llmflow.steps.acai import run_acai_step

        step = {"name": "entities", "type": "acai", "resource": "SBLGNT", "passage": "MRK 1:4"}
        with pytest.raises(ValueError) as caught:
            run_acai_step(step, {})
        assert "sp dataset add ACAI" in str(caught.value)

    def test_lint_reports_acai_missing_as_an_error(self, store):
        from llmflow.utils import resource_preflight

        steps = [{"name": "entities", "type": "acai", "resource": "SBLGNT", "passage": "MRK 1:4"}]
        findings = resource_preflight.check(steps, {})
        missing = [f for f in findings if f.kind == "dataset" and f.resource == "ACAI"]
        assert missing and missing[0].is_error


class TestTheDeclaration:
    def test_names_the_dataset_and_the_texts_acai_analyses(self):
        from llmflow.utils.scripture import _data_path

        declared = json.loads(_data_path("acai.json").read_text(encoding="utf-8"))
        assert declared["dataset"] == "ACAI"
        assert sorted(declared["resources"]) == ["SBLGNT", "WLC"]


class TestThroughTheCommandLine:
    def test_a_var_reaches_the_step_and_the_answer_lands_on_disk(
        self, tmp_path, monkeypatch, registered
    ):
        from llmflow.cli import main

        out = tmp_path / "acai.json"
        pipeline = tmp_path / "acai.yaml"
        pipeline.write_text(
            "name: acai-through-the-cli\n"
            "steps:\n"
            "  - name: entities\n"
            "    type: acai\n"
            "    resource: SBLGNT\n"
            '    passage: "${passage}"\n'
            "    output: acai\n"
            f"    saveas: {out}\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        main(["run", "--pipeline", str(pipeline), "--var", "passage=MRK 1:5"])

        assert json.loads(out.read_text(encoding="utf-8"))["verses"] == {
            "MRK 1:5": [{"id": "place:Jordan", "key": False}]
        }
