"""`type: scripture` — a named edition and a passage, in a pipeline (LLMFlow#200).

The point of the step, rather than a `type: function` call, is that an edition is *named* and
the engine resolves where it lives. Absolute paths written into pipeline YAML are why
`ears-to-hear` and `discourse-flow` only run on one laptop, and why an assistant ends up
choosing a text source — a decision that belongs to the Captain, expressed as configuration.

Editions are read from `~/.sp/editions/*.yaml`, one file per edition, so adding or changing a
source never means editing code.
"""
import json

import pytest

from llmflow.utils.scripture import load_registry_editions

# ---------------------------------------------------------------------------

HEBREW_TSV = "ref\ttext\tafter\nGEN 1:1!1\tבְּרֵאשִׁית\t \nGEN 1:1!2\tבָּרָא\t\nGEN 1:2!1\tוְהָאָרֶץ\t\n"


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


class TestStep:
    def _run(self, step, editions_dir, context=None):
        from llmflow.steps.scripture import run_scripture_step
        ctx = dict(context or {})
        run_scripture_step(step, ctx, {"_editions_dir": str(editions_dir)})
        return ctx

    def test_fetches_running_text_into_the_output_variable(self, editions_dir):
        ctx = self._run({
            "name": "fetch", "type": "scripture",
            "edition": "WLC", "passage": "GEN 1:1",
            "format": "plain", "output": "source_text",
        }, editions_dir)
        assert ctx["source_text"] == "בְּרֵאשִׁית בָּרָא"

    def test_milestones_is_the_default_format(self, editions_dir):
        ctx = self._run({
            "name": "fetch", "type": "scripture",
            "edition": "WLC", "passage": "GEN 1:1", "output": "t",
        }, editions_dir)
        assert ctx["t"].startswith("⌊1:1⌋")

    def test_passage_resolves_pipeline_variables(self, editions_dir):
        ctx = self._run({
            "name": "fetch", "type": "scripture",
            "edition": "WLC", "passage": "${ref}", "output": "t",
        }, editions_dir, context={"ref": "GEN 1:2"})
        assert "וְהָאָרֶץ" in ctx["t"]

    def test_unregistered_edition_says_what_is_registered(self, editions_dir):
        from llmflow.utils.scripture import EditionNotRegistered
        with pytest.raises(EditionNotRegistered, match="WLC"):
            self._run({
                "name": "fetch", "type": "scripture",
                "edition": "NIV11", "passage": "GEN 1:1", "output": "t",
            }, editions_dir)

    def test_a_passage_outside_the_edition_errors_rather_than_returning_empty(self, editions_dir):
        """Silently empty source text is the failure mode that reaches a model unnoticed."""
        with pytest.raises(ValueError, match="No text found"):
            self._run({
                "name": "fetch", "type": "scripture",
                "edition": "WLC", "passage": "MRK 1:1", "output": "t",
            }, editions_dir)


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
