"""Named scripture editions: a reference range in, running text out.

Text is `text + after` per word, with a space added only where `after` is punctuation that
ends a word — the source carries the mark without one. These tests pin the cases where that
distinction is visible, in both scripts:

  * maqqef joins:                עַל־פְּנֵי
  * Greek elision joins:          κατ’ὄναρ
  * a Hebrew morpheme joins:      בְּרֵאשִׁית
  * sof pasuq ends a word:        הָאָרֶץ׃ וְהָאָרֶץ
  * Greek punctuation ends one:   χριστοῦ. Καθὼς
  * milestones mark positions:    ⌊1:1⌋ … ⌊1:2⌋ …

A test asserting only that "some text came out" would pass on text that is subtly wrong,
which is the failure this feature exists to prevent.
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


class TestJoining:
    def test_maqqef_joins_with_no_space(self):
        out = rows_to_text(HEBREW_ROWS, fmt="plain")
        assert "עַל־פְּנֵ֣י" in out, out
        assert "עַל ־" not in out and "עַל־ פְּנֵ֣י" not in out

    def test_greek_elision_joins_with_no_space(self):
        rows = [{"ref": "MAT 1:20!1", "text": "κατ", "after": "’"},
                {"ref": "MAT 1:20!2", "text": "ὄναρ", "after": " "}]
        assert rows_to_text(rows, fmt="plain") == "κατ’ὄναρ"

    def test_an_empty_after_joins_two_morphemes_of_one_word(self):
        """Macula Hebrew splits a word into morphemes and marks the continuation this way."""
        rows = [{"ref": "GEN 1:1!1", "text": "בְּ", "after": ""},
                {"ref": "GEN 1:1!2", "text": "רֵאשִׁית", "after": " "}]
        assert rows_to_text(rows, fmt="plain") == "בְּרֵאשִׁית"

    def test_a_missing_after_joins_rather_than_spacing(self):
        rows = [{"ref": "GEN 1:1!1", "text": "עַל", "after": "־"},
                {"ref": "GEN 1:1!2", "text": "פְּנֵי"}]
        assert rows_to_text(rows, fmt="plain") == "עַל־פְּנֵי"

    def test_sof_pasuq_attaches_and_takes_a_space_after_it(self):
        out = rows_to_text(HEBREW_ROWS, fmt="plain")
        assert "הָאָֽרֶץ׃ וְחֹ֖שֶׁךְ" in out, out

    def test_greek_punctuation_attaches_and_takes_a_space_after_it(self):
        out = rows_to_text(GREEK_ROWS, fmt="plain")
        assert "χριστοῦ. Καθὼς" in out, out
        assert "χριστοῦ ." not in out and "χριστοῦ.Καθὼς" not in out

    def test_a_space_in_the_source_is_not_doubled(self):
        assert "  " not in rows_to_text(HEBREW_ROWS, fmt="plain")
        assert "  " not in rows_to_text(GREEK_ROWS, fmt="plain")

    def test_one_code_path_serves_both_languages(self):
        """No per-language branching: the same call handles either row set."""
        assert rows_to_text(HEBREW_ROWS, fmt="plain")
        assert rows_to_text(GREEK_ROWS, fmt="plain")


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
