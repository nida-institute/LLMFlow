"""Mapping a reference between versification schemes."""
import json
from pathlib import Path

import pytest

from llmflow.utils.versification import (
    HUB_SCHEME,
    UnmappableReference,
    load_scheme,
    map_candidates,
    map_reference,
)

COPENHAGEN = (
    Path.home()
    / "github/copenhagen-alliance/versification-specification"
    / "versification-mappings/standard-mappings"
)

real_data = pytest.mark.skipif(
    not (COPENHAGEN / "eng.json").is_file(),
    reason="the Copenhagen mappings are not on this machine",
)


def write_scheme(directory: Path, name: str, **fields) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.json"
    path.write_text(json.dumps(fields), encoding="utf-8")
    return path


@pytest.fixture
def schemes(tmp_path) -> Path:
    """A minimal three-scheme store: the hub, one mapping to it, and one based on another."""
    directory = tmp_path / "versification"
    write_scheme(directory, HUB_SCHEME, maxVerses={"PSA": ["6", "12", "21"]}, mappedVerses={})
    write_scheme(
        directory,
        "eng",
        maxVerses={"PSA": ["6", "12", "19"]},
        mappedVerses={"PSA 3:0": "PSA 3:1", "PSA 3:1-19": "PSA 3:3-21"},
    )
    write_scheme(directory, "partial", basedOn="eng", mappedVerses={"PSA 3:5": "PSA 3:6"})
    return directory


# --- the pure mapping ---------------------------------------------------------------


def test_the_same_scheme_is_identity(schemes):
    assert map_reference("PSA 3:1", "eng", "eng", mappings_dir=schemes) == "PSA 3:1"


def test_a_range_maps_verse_by_verse(schemes):
    assert map_reference("PSA 3:1", "eng", HUB_SCHEME, mappings_dir=schemes) == "PSA 3:3"
    assert map_reference("PSA 3:19", "eng", HUB_SCHEME, mappings_dir=schemes) == "PSA 3:21"


def test_a_single_verse_entry_maps(schemes):
    assert map_reference("PSA 3:0", "eng", HUB_SCHEME, mappings_dir=schemes) == "PSA 3:1"


def test_mapping_to_the_hub_reverses(schemes):
    assert map_reference("PSA 3:3", HUB_SCHEME, "eng", mappings_dir=schemes) == "PSA 3:1"


def test_an_unmapped_reference_passes_through(schemes):
    """Only the verses a scheme lists differ from the hub; the rest are already aligned."""
    assert map_reference("GEN 1:1", "eng", HUB_SCHEME, mappings_dir=schemes) == "GEN 1:1"


def test_a_reference_beyond_the_scheme_is_an_error_not_an_empty_result(schemes):
    with pytest.raises(UnmappableReference, match="PSA 3:40"):
        map_reference("PSA 3:40", "eng", HUB_SCHEME, mappings_dir=schemes)


def test_an_unknown_scheme_names_what_is_available(schemes):
    with pytest.raises(UnmappableReference, match="eng"):
        map_reference("PSA 3:1", "klingon", HUB_SCHEME, mappings_dir=schemes)


def test_a_malformed_reference_is_rejected(schemes):
    with pytest.raises(UnmappableReference, match="not a reference"):
        map_reference("halfway through Psalms", "eng", HUB_SCHEME, mappings_dir=schemes)


# --- basedOn ------------------------------------------------------------------------


def test_a_partial_custom_mapping_resolves_through_its_base(schemes):
    """`partial` lists one verse and inherits the rest of `eng` rather than erroring."""
    assert map_reference("PSA 3:5", "partial", HUB_SCHEME, mappings_dir=schemes) == "PSA 3:6"
    assert map_reference("PSA 3:1", "partial", HUB_SCHEME, mappings_dir=schemes) == "PSA 3:3"


def test_a_base_is_reported_when_it_is_missing(tmp_path):
    directory = tmp_path / "versification"
    write_scheme(directory, "orphan", basedOn="absent", mappedVerses={})
    with pytest.raises(UnmappableReference, match="absent"):
        map_reference("PSA 3:1", "orphan", HUB_SCHEME, mappings_dir=directory)


def test_a_basedon_cycle_is_reported_rather_than_hanging(tmp_path):
    directory = tmp_path / "versification"
    write_scheme(directory, "a", basedOn="b", mappedVerses={})
    write_scheme(directory, "b", basedOn="a", mappedVerses={})
    with pytest.raises(UnmappableReference, match="cycle"):
        load_scheme("a", mappings_dir=directory)


# --- order, and one-to-many -----------------------------------------------------------


def test_verses_that_swap_places_map_both_ways(tmp_path):
    """Traditions disagree on sequence — the commandments in Exodus 20 among them — so a
    mapping is a set of independent pairs and never an ordering."""
    directory = tmp_path / "versification"
    write_scheme(directory, HUB_SCHEME, mappedVerses={})
    write_scheme(
        directory,
        "swapped",
        maxVerses={"EXO": ["17"] * 20},
        mappedVerses={"EXO 20:13": "EXO 20:15", "EXO 20:14": "EXO 20:13"},
    )
    assert map_reference("EXO 20:13", "swapped", HUB_SCHEME, mappings_dir=directory) == "EXO 20:15"
    assert map_reference("EXO 20:14", "swapped", HUB_SCHEME, mappings_dir=directory) == "EXO 20:13"
    assert map_reference("EXO 20:15", HUB_SCHEME, "swapped", mappings_dir=directory) == "EXO 20:13"


def test_verse_segments_may_map_out_of_order(tmp_path):
    """A subdivided verse's parts can land in a different sequence than they were written."""
    directory = tmp_path / "versification"
    write_scheme(directory, HUB_SCHEME, mappedVerses={})
    write_scheme(
        directory,
        "shuffled",
        maxVerses={"SIR": ["30"]},
        mappedVerses={
            "SIR 1:1a": "SIR 1:1d",
            "SIR 1:1b": "SIR 1:1c",
            "SIR 1:1c": "SIR 1:1b",
            "SIR 1:1d": "SIR 1:1a",
        },
    )
    for own, hub in (("a", "d"), ("b", "c"), ("c", "b"), ("d", "a")):
        assert (
            map_reference(f"SIR 1:1{own}", "shuffled", HUB_SCHEME, mappings_dir=directory)
            == f"SIR 1:1{hub}"
        )


def test_one_hub_verse_reached_from_two_places_is_reported_not_chosen(tmp_path):
    directory = tmp_path / "versification"
    write_scheme(directory, HUB_SCHEME, maxVerses={"DAN": ["30", "30", "30", "30"]}, mappedVerses={})
    write_scheme(
        directory,
        "split",
        maxVerses={"DAG": ["30", "30", "30", "30"]},
        mappedVerses={"DAG 4:1": "DAN 4:4", "DAG 4:7": "DAN 4:4"},
    )
    assert map_candidates("DAN 4:4", HUB_SCHEME, "split", mappings_dir=directory) == [
        "DAG 4:1",
        "DAG 4:7",
    ]
    with pytest.raises(UnmappableReference, match="DAG 4:1, DAG 4:7"):
        map_reference("DAN 4:4", HUB_SCHEME, "split", mappings_dir=directory)


@real_data
def test_greek_daniel_reaches_one_original_verse_from_two_chapters():
    """`DAN 4:4` is reached from `DAG 4:1` and `DAG 4:7`, which are not adjacent."""
    assert map_candidates("DAN 4:4", "org", "lxx", mappings_dir=COPENHAGEN) == [
        "DAG 4:1",
        "DAG 4:7",
    ]


@real_data
def test_the_song_of_the_three_swaps_two_verses():
    assert map_reference("S3Y 1:32", "eng", "org", mappings_dir=COPENHAGEN) == "DAG 3:55"
    assert map_reference("S3Y 1:33", "eng", "org", mappings_dir=COPENHAGEN) == "DAG 3:54"


# --- a bad entry in a shipped mapping -----------------------------------------------


def test_an_entry_whose_sides_disagree_is_skipped_and_reported(tmp_path, caplog):
    """One bad entry must not make a whole scheme unusable, nor be guessed at."""
    directory = tmp_path / "versification"
    write_scheme(directory, HUB_SCHEME, mappedVerses={})
    write_scheme(
        directory,
        "wonky",
        maxVerses={"DAG": ["30", "49", "97"], "PSA": ["6"]},
        mappedVerses={"DAG 3:52-23": "S3Y 1:30-31", "PSA 1:1": "PSA 1:2"},
    )
    with caplog.at_level("WARNING"):
        scheme = load_scheme("wonky", mappings_dir=directory)

    assert "DAG 3:52-23" in caplog.text
    assert scheme.to_hub["PSA 1:1"] == "PSA 1:2"
    assert not any(key.startswith("DAG 3:5") for key in scheme.to_hub)


# --- against the real Copenhagen data -----------------------------------------------


@real_data
@pytest.mark.parametrize(
    "reference, expected",
    [
        ("PSA 51:1", "PSA 51:3"),
        ("PSA 51:19", "PSA 51:21"),
        ("PSA 51:0", "PSA 51:2"),
        ("MAL 4:1", "MAL 3:19"),
        ("MAL 4:6", "MAL 3:24"),
        ("MRK 1:1", "MRK 1:1"),
    ],
)
def test_english_maps_to_the_original(reference, expected):
    assert map_reference(reference, "eng", "org", mappings_dir=COPENHAGEN) == expected


@real_data
def test_malachi_has_four_chapters_in_english_and_three_in_the_original():
    assert len(load_scheme("eng", mappings_dir=COPENHAGEN).max_verses["MAL"]) == 4
    assert len(load_scheme("org", mappings_dir=COPENHAGEN).max_verses["MAL"]) == 3


@real_data
@pytest.mark.parametrize("reference", ["PSA 51:1", "MAL 4:1", "GEN 32:1", "MRK 1:1"])
def test_a_round_trip_through_the_hub_returns_the_reference(reference):
    through_hub = map_reference(reference, "eng", "org", mappings_dir=COPENHAGEN)
    assert map_reference(through_hub, "org", "eng", mappings_dir=COPENHAGEN) == reference


@real_data
def test_two_non_hub_schemes_map_through_the_hub():
    """`eng` to `vul` is two lookups, and neither scheme mentions the other.

    Vulgate Psalms run one behind through most of the Psalter, so English 51 is Vulgate 50,
    and the verse offset within the Psalm is the one `eng` already carries.
    """
    assert map_reference("PSA 51:1", "eng", "vul", mappings_dir=COPENHAGEN) == "PSA 50:3"


@real_data
def test_every_standard_scheme_loads():
    for name in ("org", "eng", "lxx", "vul", "rsc", "rso"):
        assert load_scheme(name, mappings_dir=COPENHAGEN).max_verses
