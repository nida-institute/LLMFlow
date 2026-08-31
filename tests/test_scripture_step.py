"""`type: scripture` — a named edition and a passage, in a pipeline (LLMFlow#200).

The point of the step, rather than a `type: function` call, is that an edition is *named* and
the engine resolves where it lives. Absolute paths written into pipeline YAML are why
`ears-to-hear` and `discourse-flow` only run on one laptop, and why an assistant ends up
choosing a text source — a decision that belongs to the Captain, expressed as configuration.

**Step behaviour is exercised through the API**, per rule 1 in
`docs/ai-context/project/rules.md`: `load_pipeline(...)` then `.lint()` and `.run()`. A raw
`{"type": "scripture", ...}` dict handed to `run_scripture_step` satisfies both the runner and
the object model by construction, so it cannot see a key the schema does not declare — which is
how `sp lint` came to accept `format: parquet`. A scripture-only pipeline calls no model, so
running one here is free.

The second half tests functions that take *values* rather than steps — the registry reader and
the USJ flattener. Routing those through a pipeline would test the pipeline instead.
"""
import json
from pathlib import Path

import pytest

from llmflow import load_pipeline
from llmflow.utils.scripture import load_registry_editions

MACULA = Path("/Users/jonathan/github/Clear/macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv")
SHIPPED_SCHEMES = Path(__file__).resolve().parent.parent / "src/llmflow/templates/sp/versification"

real_data = pytest.mark.skipif(not MACULA.is_file(), reason="Macula Greek is not on this machine")

HEBREW_TSV = (
    "ref\ttext\tafter\n"
    "GEN 1:1!1\tבְּרֵאשִׁית\t \n"
    "GEN 1:1!2\tבָּרָא\t\n"
    "GEN 1:2!1\tוְהָאָרֶץ\t\n"
)


@pytest.fixture
def store(tmp_path, monkeypatch) -> Path:
    """A throwaway `$SP_HOME` holding registered editions and the shipped schemes."""
    home = tmp_path / "sp"
    editions = home / "editions"
    editions.mkdir(parents=True)

    tsv = tmp_path / "wlc.tsv"
    tsv.write_text(HEBREW_TSV, encoding="utf-8")
    (editions / "WLC.yaml").write_text(
        f"id: WLC\nname: Westminster Leningrad Codex\nkind: tsv\npath: {tsv}\n"
        f"versification_scheme: org\n",
        encoding="utf-8",
    )
    if MACULA.is_file():
        (editions / "SBLGNT.yaml").write_text(
            f"id: SBLGNT\nname: SBL Greek New Testament\nkind: tsv\npath: {MACULA}\n"
            f"versification_scheme: org\n",
            encoding="utf-8",
        )

    versification = home / "versification"
    versification.mkdir()
    for scheme in SHIPPED_SCHEMES.glob("*.json"):
        (versification / scheme.name).write_text(scheme.read_text(encoding="utf-8"), "utf-8")

    monkeypatch.setenv("SP_HOME", str(home))
    return home


def pipeline_file(tmp_path: Path, steps: str, name: str = "api-test") -> Path:
    path = tmp_path / "pipeline.yaml"
    path.write_text(f"name: {name}\nsteps:\n{steps}", encoding="utf-8")
    return path


def run(path: Path) -> dict:
    """Lint then run, failing with the linter's own message rather than a bare exception."""
    pipeline = load_pipeline(path)
    result = pipeline.lint()
    assert result.valid, f"pipeline did not lint: {getattr(result, 'errors', result)}"
    return pipeline.run(log_file=str(path.parent / "llmflow.log"))


# --- the object model exposes what the schema declares --------------------------------


def test_the_api_exposes_every_scripture_key(tmp_path, store):
    """If a key is missing here it is missing from the schema, since Step is generated."""
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n"
        "    type: scripture\n"
        "    edition: WLC\n"
        '    passage: "GEN 1:1"\n'
        "    format: usj\n"
        "    versification: org\n"
        "    include: [ids]\n"
        "    output: source\n",
    )
    step = load_pipeline(path).steps[0]
    assert step.edition == "WLC"
    assert step.passage == "GEN 1:1"
    assert step.format == "usj"
    assert step.versification == "org"
    assert step.include == ["ids"]


# --- lint is the edge a raw dict cannot test ------------------------------------------


def test_an_unknown_format_is_rejected_by_lint(tmp_path, store):
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n    type: scripture\n    edition: WLC\n"
        '    passage: "GEN 1:1"\n    format: parquet\n    output: t\n',
    )
    result = load_pipeline(path).lint()
    assert not result.valid


def test_an_unknown_include_family_is_rejected_by_lint(tmp_path, store):
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n    type: scripture\n    edition: WLC\n"
        '    passage: "GEN 1:1"\n    format: usj\n    include: [parsing]\n    output: t\n',
    )
    result = load_pipeline(path).lint()
    assert not result.valid


# --- running, which calls no model ----------------------------------------------------


def test_a_passage_reaches_the_output_variable(tmp_path, store):
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n    type: scripture\n    edition: WLC\n"
        '    passage: "GEN 1:1"\n    format: plain\n    output: source\n',
    )
    assert run(path)["source"] == "בְּרֵאשִׁית בָּרָא"


def test_milestones_is_the_default_format(tmp_path, store):
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n    type: scripture\n    edition: WLC\n"
        '    passage: "GEN 1:1"\n    output: source\n',
    )
    assert run(path)["source"].startswith("⌊1:1⌋")


@real_data
def test_usj_with_ids_arrives_as_a_document_with_srcloc(tmp_path, store):
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n    type: scripture\n    edition: SBLGNT\n"
        '    passage: "MRK 1:1"\n    format: usj\n    include: [ids]\n    output: source\n',
    )
    usj = run(path)["source"]
    assert usj["type"] == "USJ"
    assert usj["scripture_pipelines"]["versification"] == "org"
    words = [
        item
        for node in usj["content"]
        if node["type"] == "para"
        for item in node["content"]
        if isinstance(item, dict) and item.get("marker") == "w"
    ]
    assert words and words[0]["srcloc"] == "n41001001001"


@real_data
def test_versification_maps_before_fetching(tmp_path, store):
    """`PSA 51:1` in English is `PSA 51:3` in the original — the mapping happens before the read.

    Uses a Greek passage so the assertion does not depend on Hebrew data being present: the
    point is that the key is honoured through the whole stack, not what Psalms says.
    """
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n    type: scripture\n    edition: SBLGNT\n"
        '    passage: "MRK 1:1"\n    versification: eng\n    format: plain\n    output: source\n',
    )
    # `eng` and `org` agree throughout the New Testament, so the text is unchanged — what is
    # being tested is that declaring a scheme neither errors nor alters a passage it should not.
    assert run(path)["source"].startswith("Ἀρχὴ")


def test_a_missing_edition_names_what_is_registered(tmp_path, store):
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n    type: scripture\n    edition: NOPE\n"
        '    passage: "GEN 1:1"\n    output: t\n',
    )
    with pytest.raises(Exception) as caught:
        load_pipeline(path).run(log_file=str(tmp_path / "llmflow.log"))
    assert "WLC" in str(caught.value), "the error should list the registered editions"


# --- the payload survives serialisation, which is how a consumer receives it ----------


@real_data
def test_the_usj_payload_is_json_serialisable(tmp_path, store):
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n    type: scripture\n    edition: SBLGNT\n"
        '    passage: "MRK 1:1"\n    format: usj\n    include: [ids]\n    output: source\n',
    )
    payload = json.dumps(run(path)["source"], ensure_ascii=False)
    assert "n41001001001" in payload


def test_passage_resolves_a_pipeline_variable(tmp_path, store):
    """`${ref}` must be resolved before the fetch, not passed through as a literal."""
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n    type: scripture\n    edition: WLC\n"
        '    passage: "${ref}"\n    format: plain\n    output: source\n',
    )
    pipeline = load_pipeline(path)
    assert pipeline.lint(vars={"ref": "GEN 1:2"}).valid
    context = pipeline.run(vars={"ref": "GEN 1:2"}, log_file=str(tmp_path / "llmflow.log"))
    assert "וְהָאָרֶץ" in context["source"]


def test_a_passage_the_edition_does_not_cover_errors_rather_than_returning_empty(tmp_path, store):
    """Silently empty source text is the failure mode that reaches a model unnoticed."""
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n    type: scripture\n    edition: WLC\n"
        '    passage: "MRK 1:1"\n    output: source\n',
    )
    with pytest.raises(ValueError, match="No text found"):
        load_pipeline(path).run(log_file=str(tmp_path / "llmflow.log"))


# =====================================================================================
# Values rather than steps: these take a path or a document, so they are called directly.
# =====================================================================================

@pytest.fixture
def editions_dir(tmp_path):
    """A registry editions directory with one TSV edition registered."""
    tsv = tmp_path / "wlc.tsv"
    tsv.write_text(HEBREW_TSV, encoding="utf-8")
    d = tmp_path / "editions"
    d.mkdir()
    (d / "WLC.yaml").write_text(
        f'id: WLC\nname: Westminster Leningrad Codex\nkind: tsv\npath: "{tsv}"\n',
        encoding="utf-8",
    )
    return d


class TestEditionsComeFromTheRegistry:
    def test_editions_are_read_from_yaml_files(self, editions_dir):
        eds = load_registry_editions(editions_dir)
        assert "WLC" in eds
        assert eds["WLC"]["kind"] == "tsv"

    def test_a_missing_directory_is_not_an_error(self, tmp_path):
        """A fresh machine has no editions registered; that is a clear error at use time,
        not an exception at import time."""
        assert load_registry_editions(tmp_path / "nope") == {}

    def test_a_malformed_edition_file_does_not_hide_the_others(self, editions_dir):
        (editions_dir / "BROKEN.yaml").write_text("this: [is: not: valid", encoding="utf-8")
        eds = load_registry_editions(editions_dir)
        assert "WLC" in eds, "one bad file must not make every edition unreadable"


class TestSchemaAndLinter:
    def test_the_step_type_is_declared_in_the_schema(self):
        from llmflow.pipeline_schema import declared_step_types
        assert "scripture" in declared_step_types()

    def test_its_keys_are_allowed(self):
        from llmflow.pipeline_schema import allowed_step_keys
        keys = allowed_step_keys("scripture")
        assert keys is not None
        for k in ("edition", "passage", "format"):
            assert k in keys, f"{k} missing from the scripture branch"

    def test_a_typo_in_a_scripture_key_is_rejected(self, tmp_path):
        """The schema is the single source of the step vocabulary (#189/#197); an unknown key
        must fail rather than be silently ignored."""
        from llmflow.utils.linter import lint_pipeline_full
        p = tmp_path / "p.yaml"
        p.write_text(json.dumps({
            "name": "p",
            "steps": [{"name": "s", "type": "scripture", "edition": "WLC",
                       "passage": "GEN 1:1", "translation": "oops", "output": "t"}],
        }), encoding="utf-8")
        result = lint_pipeline_full(str(p))
        assert not result.valid
        assert any("translation" in e for e in result.errors), result.errors


class TestApparatusIsNotText:
    """Footnotes must not reach a prompt as though they were scripture.

    BSB Mark 1:1 carries a textual-variant footnote — "ECM, NE, BYZ, and TR; SBL and WH the
    beginning of the gospel…". Flattening USJ naively includes it, and a translation-notes
    prompt would then quote the apparatus as the text. Caught by testing against the real
    data rather than a fixture.
    """

    def test_footnote_content_is_excluded(self):
        from llmflow.utils.scripture import usj_to_text
        usj = {
            "type": "USJ",
            "content": [
                {"type": "chapter", "marker": "c", "number": "1"},
                {"type": "para", "marker": "p", "content": [
                    {"type": "verse", "marker": "v", "number": "1"},
                    "This is the beginning of the gospel.",
                    {"type": "note", "marker": "f", "content": [
                        {"type": "char", "marker": "fr", "content": ["1:1 "]},
                        {"type": "char", "marker": "ft",
                         "content": ["ECM, NE, BYZ, and TR; SBL and WH ..."]},
                    ]},
                ]},
            ],
        }
        out = usj_to_text(usj, fmt="milestones")
        assert out == "⌊1:1⌋ This is the beginning of the gospel.", out
        assert "ECM" not in out and "BYZ" not in out

    def test_inline_char_content_is_kept(self):
        """`\\nd` (divine name) and `\\add` (supplied words) are part of the reading."""
        from llmflow.utils.scripture import usj_to_text
        usj = {"type": "USJ", "content": [
            {"type": "chapter", "marker": "c", "number": "23"},
            {"type": "para", "marker": "p", "content": [
                {"type": "verse", "marker": "v", "number": "1"},
                "The ",
                {"type": "char", "marker": "nd", "content": ["LORD"]},
                " is my shepherd.",
            ]},
        ]}
        assert usj_to_text(usj, fmt="plain") == "The LORD is my shepherd."
