"""Named scripture editions: reference range -> running text (LLMFlow#200).

Every consumer repo built its own loader, and they converged on the shape the conventions
forbid — a dict or list keyed by verse. That is not carelessness: while each project loads
raw assets itself, each inherits the asset's shape. `discourse-flow` reads a verse-per-line
BSB file and returns `{"Mark 1:1": "..."}` because that is what the file is.

The engine's job is to be the layer that turns an asset into running text with verse
milestones, so "verses are milestones, not containers" stops being advisory.

Extraction is a straight concatenation of `text + after` per word (Captain, 2026-08-17).
The Macula TSVs carry both columns, so the joining is data rather than logic — no
whitespace inference, and one code path for Hebrew and Greek. These tests pin the
behaviour that matters:

  * maqqef joins words with no space:      עַל־פְּנֵי
  * sof pasuq attaches to the last word:   הָאָֽרֶץ׃
  * Greek punctuation attaches:            χριστοῦ.
  * verse milestones mark positions:       ⌊1:1⌋ … ⌊1:2⌋ …

A test that only asserts "some text came out" would pass on text that is subtly wrong,
which is the failure this whole feature exists to prevent.
"""
import pytest

from llmflow.utils.scripture import (
    MILESTONE_TEMPLATE,
    EditionNotRegistered,
    parse_passage_ref,
    rows_to_text,
)

# ---------------------------------------------------------------------------
# Fixtures: minimal row sets in the shape the Macula TSVs provide.
# ---------------------------------------------------------------------------

HEBREW_ROWS = [
    {"ref": "GEN 1:1!1", "text": "בְּרֵאשִׁ֖ית", "after": " "},
    {"ref": "GEN 1:1!2", "text": "בָּרָ֣א", "after": " "},
    {"ref": "GEN 1:1!3", "text": "אֱלֹהִ֑ים", "after": " "},
    {"ref": "GEN 1:1!4", "text": "הָאָֽרֶץ", "after": "׃"},
    {"ref": "GEN 1:2!1", "text": "וְחֹ֖שֶׁךְ", "after": " "},
    {"ref": "GEN 1:2!2", "text": "עַל", "after": "־"},
    {"ref": "GEN 1:2!3", "text": "פְּנֵ֣י", "after": " "},
    {"ref": "GEN 1:2!4", "text": "תְה֑וֹם", "after": "׃"},
]

GREEK_ROWS = [
    {"ref": "MRK 1:1!1", "text": "Ἀρχὴ", "after": " "},
    {"ref": "MRK 1:1!2", "text": "τοῦ", "after": " "},
    {"ref": "MRK 1:1!3", "text": "χριστοῦ", "after": "."},
    {"ref": "MRK 1:2!1", "text": "Καθὼς", "after": " "},
    {"ref": "MRK 1:2!2", "text": "γέγραπται", "after": " "},
    {"ref": "MRK 1:2!3", "text": "προφήτῃ", "after": "·"},
]


class TestJoiningIsDataNotLogic:
    def test_maqqef_joins_with_no_space(self):
        out = rows_to_text(HEBREW_ROWS, fmt="plain")
        assert "עַל־פְּנֵ֣י" in out, out
        assert "עַל ־" not in out and "עַל־ פְּנֵ֣י" not in out

    def test_sof_pasuq_attaches(self):
        out = rows_to_text(HEBREW_ROWS, fmt="plain")
        assert "הָאָֽרֶץ׃" in out, out

    def test_greek_punctuation_attaches(self):
        out = rows_to_text(GREEK_ROWS, fmt="plain")
        assert "χριστοῦ." in out and "χριστοῦ ." not in out, out

    def test_one_code_path_serves_both_languages(self):
        """No per-language branching: the same call handles either row set."""
        assert rows_to_text(HEBREW_ROWS, fmt="plain")
        assert rows_to_text(GREEK_ROWS, fmt="plain")

    def test_missing_after_is_treated_as_empty_not_as_a_space(self):
        """Inserting a space where the data has none would corrupt joined forms."""
        rows = [{"ref": "GEN 1:1!1", "text": "עַל", "after": "־"},
                {"ref": "GEN 1:1!2", "text": "פְּנֵי"}]
        assert rows_to_text(rows, fmt="plain") == "עַל־פְּנֵי"


class TestMilestones:
    def test_milestones_mark_verse_starts(self):
        out = rows_to_text(HEBREW_ROWS, fmt="milestones")
        assert out.startswith("⌊1:1⌋"), out
        assert "⌊1:2⌋" in out

    def test_plain_has_no_milestones(self):
        assert "⌊" not in rows_to_text(HEBREW_ROWS, fmt="plain")

    def test_milestone_template_is_declared_once(self):
        """The delimiter is a convention inherited from ears-to-hear; keep it in one place
        so it can be changed by decision rather than by search-and-replace."""
        assert MILESTONE_TEMPLATE.format(chapter=1, verse=1) == "⌊1:1⌋"

    def test_running_text_is_not_split_into_verse_records(self):
        """The shape the conventions forbid must not be reachable through this function."""
        out = rows_to_text(HEBREW_ROWS, fmt="milestones")
        assert isinstance(out, str)

    def test_verse_boundary_gets_separating_space(self):
        """Without it, the last word of a verse fuses onto the next milestone."""
        out = rows_to_text(GREEK_ROWS, fmt="milestones")
        assert "χριστοῦ. ⌊1:2⌋" in out or "χριστοῦ.\n⌊1:2⌋" in out, out


class TestPassageParsing:
    @pytest.mark.parametrize("passage,expected", [
        ("MRK 1:1-8", ("MRK", 1, 1, 1, 8)),
        ("MRK 1",     ("MRK", 1, None, 1, None)),
        ("GEN 1:1",   ("GEN", 1, 1, 1, 1)),
    ])
    def test_shapes_the_engine_must_accept(self, passage, expected):
        got = parse_passage_ref(passage)
        assert (got.book, got.start_chapter, got.start_verse,
                got.end_chapter, got.end_verse) == expected

    def test_cross_chapter_range(self):
        got = parse_passage_ref("MRK 1:40-2:12")
        assert (got.start_chapter, got.start_verse) == (1, 40)
        assert (got.end_chapter, got.end_verse) == (2, 12)

    def test_book_only(self):
        got = parse_passage_ref("PHM")
        assert got.book == "PHM" and got.start_chapter is None

    def test_rubbish_is_rejected_with_the_input_quoted(self):
        with pytest.raises(ValueError, match="not a passage"):
            parse_passage_ref("the bit about the shepherd")


class TestFiltering:
    def test_rows_outside_the_range_are_excluded(self):
        from llmflow.utils.scripture import filter_rows
        got = filter_rows(HEBREW_ROWS, parse_passage_ref("GEN 1:2"))
        assert all("1:2" in r["ref"] for r in got), got
        assert len(got) == 4

    def test_a_range_spanning_both_verses(self):
        from llmflow.utils.scripture import filter_rows
        assert len(filter_rows(HEBREW_ROWS, parse_passage_ref("GEN 1:1-2"))) == 8

    def test_wrong_book_yields_nothing(self):
        from llmflow.utils.scripture import filter_rows
        assert filter_rows(HEBREW_ROWS, parse_passage_ref("EXO 1:1")) == []


class TestEditionResolution:
    def test_unregistered_edition_names_what_is_available(self):
        """A bare KeyError would send the reader to the source; the error should say what
        editions exist and how to register one."""
        from llmflow.utils.scripture import resolve_edition
        with pytest.raises(EditionNotRegistered) as exc:
            resolve_edition("NO_SUCH_EDITION", registry_editions={"WLC": "/tmp/wlc.tsv"})
        msg = str(exc.value)
        assert "NO_SUCH_EDITION" in msg and "WLC" in msg

    def test_a_registered_edition_resolves_to_its_path(self):
        from llmflow.utils.scripture import resolve_edition
        assert resolve_edition("WLC", registry_editions={"WLC": "/tmp/wlc.tsv"}) == "/tmp/wlc.tsv"
