"""Reading the UBS Parallel Passages database at verse level.

The reader answers one question: which groups does a passage take part in. A group is
returned whole, never intersected with the request (#258).
"""

from __future__ import annotations

import pytest

from llmflow.utils.parallel_passages import groups_for_passage, load_parallel_passages

SAMPLE = """<?xml version="1.0" encoding="utf-8"?>
<Passages>
  <Passage>
    <Verse GRK="000001221222200001000000">MAT 3:1-2</Verse>
    <Verse GRK="12212220222222">MRK 1:4</Verse>
  </Passage>
  <Passage>
    <Verse GRK="000010222022222222222222">MAT 3:3</Verse>
    <Verse GRK="2200222000000000000022222222222222">MRK 1:2-3</Verse>
    <Verse GRK="1200022222222222222222">LUK 3:4</Verse>
  </Passage>
  <Passage>
    <Verse GRK="0002221114112222522">MAT 8:16</Verse>
    <Verse GRK="2221111411222250252022225212521211522">MRK 1:32,34</Verse>
  </Passage>
  <Passage>
    <Verse HEB="221222412111300000003000000030030000">MAL 3:1</Verse>
    <Verse GRK="12000005222222252222">MRK 1:2</Verse>
  </Passage>
</Passages>
"""


@pytest.fixture
def index(tmp_path):
    path = tmp_path / "ParallelPassages.xml"
    path.write_text(SAMPLE, encoding="utf-8")
    return load_parallel_passages(path)


class TestFindingAGroup:
    def test_a_verse_finds_the_group_naming_it(self, index):
        groups = groups_for_passage(index, "MRK 1:4")
        assert len(groups) == 1
        assert [v["reference"] for v in groups[0]["verses"]] == ["MAT 3:1-2", "MRK 1:4"]

    def test_a_verse_inside_a_range_row_finds_it(self, index):
        """`MRK 1:2-3` is a row; asking for 1:3 must find it.

        String equality is what the reader must not do: 647 of 5,266 rows carry a range.
        """
        groups = groups_for_passage(index, "MRK 1:3")
        assert len(groups) == 1
        assert [v["reference"] for v in groups[0]["verses"]] == [
            "MAT 3:3",
            "MRK 1:2-3",
            "LUK 3:4",
        ]

    def test_a_verse_in_a_comma_row_finds_it(self, index):
        groups = groups_for_passage(index, "MRK 1:34")
        assert len(groups) == 1
        assert groups[0]["verses"][1]["reference"] == "MRK 1:32,34"

    def test_a_verse_the_comma_row_omits_does_not_match(self, index):
        """`MRK 1:32,34` names two verses and not the one between them."""
        assert groups_for_passage(index, "MRK 1:33") == []


class TestTheGroupIsReturnedWhole:
    def test_a_partial_overlap_returns_every_member(self, index):
        """The whole row, never an intersection (#258)."""
        groups = groups_for_passage(index, "MRK 1:2")
        refs = {v["reference"] for g in groups for v in g["verses"]}
        assert "MAT 3:3" in refs and "LUK 3:4" in refs

    def test_a_range_request_collects_every_group_once(self, index):
        """MRK 1:2 is in two groups and 1:3 in one of them; no group is repeated."""
        groups = groups_for_passage(index, "MRK 1:2-4")
        signatures = [tuple(v["reference"] for v in g["verses"]) for g in groups]
        assert len(signatures) == len(set(signatures))
        assert len(groups) == 3


class TestWhatAVerseCarries:
    def test_a_verse_carries_its_scores_and_the_edition_indexing_them(self, index):
        groups = groups_for_passage(index, "MAL 3:1")
        verses = {v["reference"]: v for v in groups[0]["verses"]}
        assert verses["MAL 3:1"]["indexed_by"] == "HEB"
        assert verses["MRK 1:2"]["indexed_by"] == "GRK"
        assert verses["MRK 1:2"]["scores"] == "12000005222222252222"


class TestTwoKindsOfNothing:
    def test_a_passage_in_no_group_returns_an_empty_list(self, index):
        """Consulted, and it takes part in nothing. Rule `say-which-kind-of-nothing`."""
        assert groups_for_passage(index, "PSA 23:1") == []
