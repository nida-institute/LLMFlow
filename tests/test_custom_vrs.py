"""Tests: reading a Paratext `custom.vrs` overlay and folding it onto its base scheme.

The four constructs come from `json2vrs.py` in the Copenhagen specification, which writes this
format from the JSON scheme: `maxVerses`, `excludedVerses`, `partialVerses`, `mappedVerses`.

Covers:
  - Chapter lengths: one chapter, a whole book on one line, `END` as a terminator, and the
    sparse case where a line names chapters that neither start at 1 nor run consecutively
  - Excluded verses, and partial-verse declarations, which the engine parses but does not read
  - Mappings: ranges on either side, a segment letter on the left, `=` without spaces, a
    mixed-case book code, and the same left-hand side stated twice, which is a merge
  - A file opening with a UTF-8 byte order mark
  - Folding: a per-chapter override leaves the base's other chapters alone, the scheme carries
    the project's name, and a chapter the base cannot supply is refused rather than invented
"""

from pathlib import Path

import pytest

from llmflow.utils.versification import (
    CustomOverlay,
    UnmappableReference,
    fold_custom,
    map_candidates,
    map_reference,
    packaged_mappings_dir,
    packaged_scheme,
    read_custom_vrs,
    scheme_name,
)

FIXTURES = Path(__file__).parent / "fixtures" / "versification"
OVERLAY = FIXTURES / "custom-overlay.vrs"
BOM = FIXTURES / "custom-bom.vrs"


@pytest.fixture(scope="module")
def overlay() -> CustomOverlay:
    return read_custom_vrs(OVERLAY)


# ---------------------------------------------------------------------------
# maxVerses — chapter lengths
# ---------------------------------------------------------------------------

class TestChapterLengths:

    def test_single_chapter_book(self, overlay):
        assert overlay.chapter_lengths["3JN"] == {1: 15}

    def test_whole_book_on_one_line(self, overlay):
        assert overlay.chapter_lengths["JOL"] == {1: 20, 2: 32, 3: 21}

    def test_end_is_a_terminator_not_a_chapter(self, overlay):
        assert 0 not in overlay.chapter_lengths["JOL"]
        assert len(overlay.chapter_lengths["JOL"]) == 3

    def test_sparse_and_indented_line(self, overlay):
        assert overlay.chapter_lengths["PSA"] == {47: 10, 48: 15}

    def test_a_mixed_case_book_code_is_normalised(self, overlay):
        assert overlay.chapter_lengths["1SA"] == {1: 28, 2: 36}

    def test_a_code_the_name_resolver_calls_ambiguous(self, overlay):
        # `PSS` is the code for Psalms of Solomon; as a name it is ambiguous with Psalms. A
        # `.vrs` names books by code, so the code is what it means.
        assert overlay.chapter_lengths["PSS"] == {1: 8}


# ---------------------------------------------------------------------------
# excludedVerses and partialVerses
# ---------------------------------------------------------------------------

class TestExcludedVerses:

    def test_excluded_verses_are_collected(self, overlay):
        assert overlay.excluded_verses == frozenset({"MAT 17:21", "MRK 9:44"})


class TestPartialVerses:

    def test_segments_are_collected_in_order(self, overlay):
        assert overlay.partial_verses["PSA 3:1"] == ("-", "a", "b")

    def test_a_book_code_containing_a_digit(self, overlay):
        assert overlay.partial_verses["S3Y 1:1"] == ("a", "b", "c")


# ---------------------------------------------------------------------------
# mappedVerses
# ---------------------------------------------------------------------------

class TestMappings:

    def test_pairs_keep_the_file_order(self, overlay):
        assert overlay.mapped_verses[0] == ("REV 13:1", "REV 12:18")

    def test_the_same_left_hand_side_may_be_stated_twice(self, overlay):
        targets = [rhs for lhs, rhs in overlay.mapped_verses if lhs == "REV 13:1"]
        assert targets == ["REV 12:18", "REV 13:1"]

    def test_a_range_on_both_sides(self, overlay):
        assert ("NEH 7:68-73", "NEH 7:67-72") in overlay.mapped_verses

    def test_a_segment_letter_on_the_left(self, overlay):
        assert ("PSA 3:1a", "PSA 3:2") in overlay.mapped_verses

    def test_equals_without_surrounding_spaces(self, overlay):
        assert ("PSA 13:1-6", "PSA 13:2-7") in overlay.mapped_verses

    def test_a_mixed_case_book_code(self, overlay):
        assert ("1Sa 1:1", "1SA 1:1") in overlay.mapped_verses

    def test_one_verse_dividing_into_a_run(self, overlay):
        assert ("JOL 2:1", "JOL 2:1-2") in overlay.mapped_verses

    def test_a_trailing_comment_is_not_part_of_the_target(self, overlay):
        for _, rhs in overlay.mapped_verses:
            assert "#" not in rhs


# ---------------------------------------------------------------------------
# Lexical robustness
# ---------------------------------------------------------------------------

class TestFileLevelDetails:

    def test_a_byte_order_mark_does_not_hide_the_first_line(self):
        parsed = read_custom_vrs(BOM)
        assert parsed.chapter_lengths["3JN"] == {1: 15}
        assert "MAT 17:21" in parsed.excluded_verses

    def test_a_missing_file_is_refused(self, tmp_path):
        with pytest.raises(UnmappableReference):
            read_custom_vrs(tmp_path / "absent.vrs")

    def test_an_unreadable_line_is_refused_naming_the_line(self, tmp_path):
        path = tmp_path / "bad.vrs"
        path.write_text("3JN 1:15\nthis is not a versification line\n")
        with pytest.raises(UnmappableReference) as raised:
            read_custom_vrs(path)
        assert "2" in str(raised.value)

    def test_comments_and_blank_lines_contribute_nothing(self, tmp_path):
        path = tmp_path / "only-comments.vrs"
        path.write_text("# a comment\n\n   \n# another\n")
        parsed = read_custom_vrs(path)
        assert parsed.chapter_lengths == {}
        assert parsed.excluded_verses == frozenset()
        assert parsed.partial_verses == {}
        assert parsed.mapped_verses == ()


# ---------------------------------------------------------------------------
# Folding onto the base scheme
# ---------------------------------------------------------------------------

class TestFoldCustom:

    def test_the_scheme_carries_the_project_name(self, overlay):
        folded = fold_custom(packaged_scheme("eng"), overlay, name="spaNVIv3")
        assert folded.name == "spaNVIv3"

    def test_a_per_chapter_override_wins(self, overlay):
        folded = fold_custom(packaged_scheme("eng"), overlay, name="p")
        assert int(folded.max_verses["PSA"][46]) == 10

    def test_the_base_s_other_chapters_are_untouched(self, overlay):
        base = packaged_scheme("eng")
        folded = fold_custom(base, overlay, name="p")
        assert folded.max_verses["PSA"][0] == base.max_verses["PSA"][0]
        assert len(folded.max_verses["PSA"]) == len(base.max_verses["PSA"])

    def test_the_base_is_not_mutated(self, overlay):
        base = packaged_scheme("eng")
        before = list(base.max_verses["PSA"])
        fold_custom(base, overlay, name="p")
        assert list(base.max_verses["PSA"]) == before

    def test_excluded_verses_are_the_union(self, overlay):
        base = packaged_scheme("eng")
        folded = fold_custom(base, overlay, name="p")
        assert "MAT 17:21" in folded.excluded_verses
        assert base.excluded_verses <= folded.excluded_verses

    def test_a_left_hand_side_stated_twice_becomes_two_hub_verses(self, overlay):
        folded = fold_custom(packaged_scheme("eng"), overlay, name="p")
        assert folded.to_hub["REV 13:1"] == ["REV 12:18", "REV 13:1"]

    def test_a_range_mapping_expands_verse_by_verse(self, overlay):
        folded = fold_custom(packaged_scheme("eng"), overlay, name="p")
        assert folded.to_hub["NEH 7:68"] == ["NEH 7:67"]
        assert folded.to_hub["NEH 7:73"] == ["NEH 7:72"]

    def test_a_chapter_the_base_cannot_supply_is_refused(self):
        # The base has no such book, so filling the unstated chapters 1-4 would be invention.
        overlay = CustomOverlay(
            chapter_lengths={"ZZZ": {5: 10}},
            excluded_verses=frozenset(),
            partial_verses={},
            mapped_verses=(),
        )
        with pytest.raises(UnmappableReference):
            fold_custom(packaged_scheme("eng"), overlay, name="p")

    def test_the_overlay_replaces_a_verse_the_base_also_maps(self):
        base = packaged_scheme("eng")
        mapped_in_base = next(iter(base.to_hub))
        overlay = CustomOverlay(mapped_verses=((mapped_in_base, "GEN 1:1"),))
        folded = fold_custom(base, overlay, name="p")
        assert folded.to_hub[mapped_in_base] == ["GEN 1:1"]

    def test_a_chapter_immediately_past_the_base_s_last_is_appended(self):
        base = packaged_scheme("eng")
        next_chapter = len(base.max_verses["JOL"]) + 1
        overlay = CustomOverlay(
            chapter_lengths={"JOL": {next_chapter: 7}},
            excluded_verses=frozenset(),
            partial_verses={},
            mapped_verses=(),
        )
        folded = fold_custom(base, overlay, name="p")
        assert int(folded.max_verses["JOL"][next_chapter - 1]) == 7


# ---------------------------------------------------------------------------
# A Scheme object is accepted wherever a scheme name is
# ---------------------------------------------------------------------------

class TestSchemeObjectsAsArguments:

    def test_scheme_name_reads_a_string(self):
        assert scheme_name("eng") == "eng"

    def test_scheme_name_reads_an_object(self):
        assert scheme_name(packaged_scheme("eng")) == "eng"

    def test_a_scheme_object_maps_like_its_name(self):
        by_name = map_candidates(
            "PSA 51:1", "eng", "org", mappings_dir=packaged_mappings_dir()
        )
        by_object = map_candidates(
            "PSA 51:1", packaged_scheme("eng"), "org", mappings_dir=packaged_mappings_dir()
        )
        assert by_object == by_name

    def test_a_scheme_object_as_the_target(self):
        by_name = map_reference(
            "PSA 51:3", "org", "eng", mappings_dir=packaged_mappings_dir()
        )
        by_object = map_reference(
            "PSA 51:3", "org", packaged_scheme("eng"), mappings_dir=packaged_mappings_dir()
        )
        assert by_object == by_name

    def test_two_names_for_the_same_scheme_do_not_map(self):
        # A folded overlay is labelled for its project, so its name differs from its base's.
        # Mapping between a scheme and itself must be a no-op whatever it is called.
        folded = fold_custom(packaged_scheme("eng"), CustomOverlay(), name="myProject")
        assert map_candidates(
            "PSA 51:1", folded, folded, mappings_dir=packaged_mappings_dir()
        ) == ["PSA 51:1"]

    def test_an_error_message_names_the_scheme_not_the_object(self):
        overlay = CustomOverlay(mapped_verses=(("GEN 1:1", "GEN 1:1-2"),))
        folded = fold_custom(packaged_scheme("eng"), overlay, name="myProject")
        with pytest.raises(UnmappableReference) as raised:
            map_reference("GEN 1:1", folded, "org", mappings_dir=packaged_mappings_dir())
        assert "myProject" in str(raised.value)
        assert "Scheme(" not in str(raised.value)
