"""An edition declares its scheme, and a passage is mapped before the text is fetched."""
import json
from pathlib import Path

import pytest

from llmflow.utils.scripture import (
    ASSUMED_SCHEME,
    SCHEME_KEY,
    edition_scheme,
    edition_text,
    resolve_passage,
)
from llmflow.utils.versification import HUB_SCHEME, UnmappableReference, load_scheme

#: Two verses of a fictional book in two schemes, so a mapping is visible in the text itself.
ROWS = "\n".join(
    ["ref\ttext\tafter"]
    + [f"TST 1:{verse}\tverse{verse}\t " for verse in range(1, 6)]
)


@pytest.fixture
def store(tmp_path):
    """A throwaway store holding a hub and one scheme that shifts TST by two verses."""
    directory = tmp_path / "versification"
    directory.mkdir()
    (directory / f"{HUB_SCHEME}.json").write_text(
        json.dumps({"maxVerses": {"TST": ["5"]}, "mappedVerses": {}}), encoding="utf-8"
    )
    (directory / "shifted.json").write_text(
        json.dumps(
            {"maxVerses": {"TST": ["5"]}, "mappedVerses": {"TST 1:1-3": "TST 1:3-5"}}
        ),
        encoding="utf-8",
    )
    tsv = tmp_path / "hub.tsv"
    tsv.write_text(ROWS, encoding="utf-8")
    return {"dir": directory, "tsv": str(tsv)}


def editions(store, **overrides):
    definition = {"kind": "tsv", "path": store["tsv"], "versification_scheme": HUB_SCHEME}
    definition.update(overrides)
    return {"HUB": definition}


# --- an edition declares its scheme --------------------------------------------------


def test_an_edition_declaring_a_scheme_reports_it(store):
    assert edition_scheme(editions(store)["HUB"]) == HUB_SCHEME


def test_an_edition_declaring_nothing_has_an_unknown_scheme():
    """There is no global default: a Byzantine text and a critical text differ."""
    assert edition_scheme({"kind": "tsv", "path": "x.tsv"}) is None


def test_a_bare_path_definition_has_an_unknown_scheme():
    """The shorthand form is a path string with nowhere to put a scheme."""
    assert edition_scheme("/some/where.tsv") is None


@pytest.mark.parametrize(
    "name, expected", [("SBLGNT", "org"), ("sblgnt", "org"), ("WLC", "org"), ("BSB", "eng")]
)
def test_an_edition_we_construct_is_known_by_name(name, expected):
    assert edition_scheme({"kind": "tsv", "path": "x.tsv"}, name) == expected


def test_a_declared_scheme_beats_the_table():
    assert edition_scheme({"kind": "tsv", SCHEME_KEY: "lxx"}, "SBLGNT") == "lxx"


def test_a_paratext_project_scheme_comes_from_its_settings(tmp_path):
    project = tmp_path / "PROJ"
    project.mkdir()
    (project / "Settings.xml").write_text(
        "<ScriptureText><Versification>4</Versification></ScriptureText>", encoding="utf-8"
    )
    definition = {"kind": "usfm", "base_dir": str(tmp_path), "project": "PROJ"}
    assert edition_scheme(definition) == "eng"


def test_a_paratext_project_with_no_versification_is_unknown(tmp_path):
    project = tmp_path / "PROJ"
    project.mkdir()
    (project / "Settings.xml").write_text("<ScriptureText/>", encoding="utf-8")
    definition = {"kind": "usfm", "base_dir": str(tmp_path), "project": "PROJ"}
    assert edition_scheme(definition) is None


def test_a_paratext_custom_vrs_is_reported_as_unread(tmp_path, caplog):
    project = tmp_path / "PROJ"
    project.mkdir()
    (project / "Settings.xml").write_text(
        "<ScriptureText><Versification>1</Versification></ScriptureText>", encoding="utf-8"
    )
    (project / "custom.vrs").write_text("# overlay\n", encoding="utf-8")
    definition = {"kind": "usfm", "base_dir": str(tmp_path), "project": "PROJ"}
    with caplog.at_level("WARNING"):
        assert edition_scheme(definition) == "org"
    assert "custom.vrs" in caplog.text


def test_mapping_without_a_known_edition_scheme_assumes_english_and_warns(store, caplog):
    """An edition that declares no scheme is read as English, loudly.

    This test previously required a refusal, on the reasoning that mapping without a declared
    source scheme has to guess. The guess is now made, because much of the translation world
    uses English versification without meeting the issue and a project may have no
    versification file at all — but never silently, since a wrong assumption returns the wrong
    verses rather than the wrong label. Covered in full by
    `tests/test_assumed_versification.py`.
    """
    definition = {"kind": "tsv", "path": store["tsv"]}
    with caplog.at_level("WARNING"):
        edition_text(
            "MYSTERY", "TST 1:1", fmt="plain", editions={"MYSTERY": definition},
            versification=ASSUMED_SCHEME, mappings_dir=store["dir"],
        )
    assert SCHEME_KEY in caplog.text, "the warning must name the field to add"


def test_an_unknown_edition_scheme_is_fine_when_nothing_is_mapped(store):
    """No `versification:` means no mapping, so the scheme is never needed."""
    definition = {"kind": "tsv", "path": store["tsv"]}
    got = edition_text("MYSTERY", "TST 1:1", fmt="plain", editions={"MYSTERY": definition})
    assert got == "verse1"


# --- mapping before fetching ----------------------------------------------------------


def test_no_requested_scheme_leaves_the_passage_alone(store):
    assert resolve_passage("TST 1:1", HUB_SCHEME, None, mappings_dir=store["dir"]) == "TST 1:1"


def test_the_same_scheme_leaves_the_passage_alone(store):
    got = resolve_passage("TST 1:1", HUB_SCHEME, HUB_SCHEME, mappings_dir=store["dir"])
    assert got == "TST 1:1"


def test_a_single_verse_is_mapped_into_the_edition_scheme(store):
    """The caller asks in `shifted`; the edition is the hub, so the verse moves by two."""
    got = resolve_passage("TST 1:1", HUB_SCHEME, "shifted", mappings_dir=store["dir"])
    assert got == "TST 1:3"


def test_both_ends_of_a_range_are_mapped(store):
    got = resolve_passage("TST 1:1-3", HUB_SCHEME, "shifted", mappings_dir=store["dir"])
    assert got == "TST 1:3-5"


def test_a_whole_chapter_needs_no_mapping(store):
    """A chapter reference names no verse, so there is nothing to move."""
    assert resolve_passage("TST 1", HUB_SCHEME, "shifted", mappings_dir=store["dir"]) == "TST 1"


def test_a_whole_book_needs_no_mapping(store):
    assert resolve_passage("TST", HUB_SCHEME, "shifted", mappings_dir=store["dir"]) == "TST"


def test_a_cross_chapter_range_maps_both_ends(store):
    (store["dir"] / f"{HUB_SCHEME}.json").write_text(
        json.dumps({"maxVerses": {"TST": ["5", "5"]}, "mappedVerses": {}}), encoding="utf-8"
    )
    (store["dir"] / "twochapters.json").write_text(
        json.dumps(
            {
                "maxVerses": {"TST": ["5", "5"]},
                "mappedVerses": {"TST 1:5": "TST 1:4", "TST 2:1": "TST 2:2"},
            }
        ),
        encoding="utf-8",
    )
    got = resolve_passage("TST 1:4-2:2", "twochapters", HUB_SCHEME, mappings_dir=store["dir"])
    assert got == "TST 1:5-2:1"


def test_an_ambiguous_endpoint_is_reported_rather_than_chosen(store):
    """Two verses of the target scheme reach one hub verse; picking one silently is the bug."""
    (store["dir"] / "split.json").write_text(
        json.dumps(
            {
                "maxVerses": {"TST": ["5"]},
                "mappedVerses": {"TST 1:1": "TST 1:4", "TST 1:5": "TST 1:4"},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(UnmappableReference, match="TST 1:1, TST 1:5"):
        resolve_passage("TST 1:4", "split", HUB_SCHEME, mappings_dir=store["dir"])


# --- end to end through edition_text --------------------------------------------------


def test_asking_in_another_scheme_returns_the_mapped_verse(store):
    """`versification="shifted"` means "I am naming verses the way `shifted` does"."""
    plain = edition_text(
        "HUB", "TST 1:1", fmt="plain", editions=editions(store),
        versification="shifted", mappings_dir=store["dir"],
    )
    assert plain == "verse3"


def test_without_a_versification_key_the_edition_scheme_governs(store):
    plain = edition_text("HUB", "TST 1:1", fmt="plain", editions=editions(store))
    assert plain == "verse1"


# --- the shipped schemes, and the editions they describe ------------------------------

SHIPPED = Path(__file__).resolve().parent.parent / "src/llmflow/templates/sp/versification"

MACULA_GREEK = Path("/Users/jonathan/github/Clear/macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv")
MACULA_HEBREW = Path("/Users/jonathan/github/Clear/macula-hebrew/WLC/tsv/macula-hebrew.tsv")


@pytest.mark.parametrize("scheme", ["org", "eng", "lxx", "vul", "rsc", "rso"])
def test_every_shipped_scheme_loads(scheme):
    assert load_scheme(scheme, mappings_dir=SHIPPED).max_verses


def test_installing_puts_every_catalogued_mapping_in_the_store(tmp_path):
    """The write path, not a simulation of it: declaring a file installs nothing by itself."""
    from llmflow.cli_utils import install_global_versification
    from llmflow.file_catalog import Scope, entries
    from llmflow.utils.versification import MAPPINGS_DIRNAME

    store = tmp_path / "sp"
    install_global_versification(sp_home=store)

    declared = {
        e.path
        for e in entries()
        if e.scope is Scope.SP_HOME and e.path.startswith(f"{MAPPINGS_DIRNAME}/")
    }
    assert declared, "the catalog declares no versification files"
    for path in declared:
        assert (store / path).is_file(), f"{path} was declared but not installed"


def test_a_scheme_loads_from_the_store_after_installing(tmp_path):
    from llmflow.cli_utils import install_global_versification
    from llmflow.utils.versification import MAPPINGS_DIRNAME, map_reference

    store = tmp_path / "sp"
    install_global_versification(sp_home=store)
    got = map_reference("PSA 51:1", "eng", "org", mappings_dir=store / MAPPINGS_DIRNAME)
    assert got == "PSA 51:3"


def test_installing_leaves_a_custom_mapping_alone(tmp_path):
    """A scheme the human adds is not catalogued, so nothing may overwrite or remove it.

    The store is kept read-only, so adding one means making the directory writable first.
    """
    from llmflow.cli_utils import _unlock_sp_dir, install_global_versification
    from llmflow.utils.versification import MAPPINGS_DIRNAME

    store = tmp_path / "sp"
    install_global_versification(sp_home=store)

    mappings = store / MAPPINGS_DIRNAME
    _unlock_sp_dir(mappings)
    mine = mappings / "mine.json"
    mine.write_text('{"basedOn": "eng", "mappedVerses": {}}', encoding="utf-8")

    install_global_versification(sp_home=store)
    assert mine.is_file()
    assert "basedOn" in mine.read_text(encoding="utf-8")


def test_the_installed_mappings_are_left_read_only(tmp_path):
    """Consistent with the rest of the store, and why adding a custom scheme needs an unlock."""
    import os

    from llmflow.cli_utils import install_global_versification
    from llmflow.utils.versification import MAPPINGS_DIRNAME

    store = tmp_path / "sp"
    install_global_versification(sp_home=store)
    assert not os.access(store / MAPPINGS_DIRNAME, os.W_OK)


def test_the_shipped_schemes_carry_their_licence():
    """CC BY-SA 4.0 requires the notice to travel with the data it covers."""
    attribution = (SHIPPED / "ATTRIBUTION.md").read_text(encoding="utf-8")
    assert "CC BY-SA 4.0" in attribution
    assert "creativecommons.org/licenses/by-sa/4.0" in attribution


@pytest.mark.skipif(not MACULA_GREEK.is_file(), reason="Macula Greek is not on this machine")
def test_macula_greek_is_numbered_as_the_hub_scheme_says():
    """The default scheme for an edition is the hub, so this is what that default asserts.

    `org` and `eng` map no New Testament verse differently, but their bounds differ: 2 Cor 13
    has 13 verses in one and 14 in the other, and 3 John 15 exists in one only.
    """
    scheme = load_scheme(HUB_SCHEME, mappings_dir=SHIPPED)
    assert int(scheme.max_verses["2CO"][12]) == 13
    assert int(scheme.max_verses["3JN"][0]) == 15
    assert scheme.contains("2CO", 13, 13) and not scheme.contains("2CO", 13, 14)
    assert scheme.contains("3JN", 1, 15)


@pytest.mark.skipif(not MACULA_HEBREW.is_file(), reason="Macula Hebrew is not on this machine")
def test_macula_hebrew_is_numbered_as_the_hub_scheme_says():
    """Psalm 51 runs to 21 verses and Malachi has three chapters — the original numbering."""
    scheme = load_scheme(HUB_SCHEME, mappings_dir=SHIPPED)
    assert int(scheme.max_verses["PSA"][50]) == 21
    assert len(scheme.max_verses["MAL"]) == 3
    assert scheme.contains("PSA", 51, 21)
    assert not scheme.contains("MAL", 4, 1)


def test_an_unknown_requested_scheme_names_what_is_available(store):
    with pytest.raises(UnmappableReference, match="shifted"):
        edition_text(
            "HUB", "TST 1:1", fmt="plain", editions=editions(store),
            versification="klingon", mappings_dir=store["dir"],
        )


def test_installing_works_when_the_store_is_already_locked(tmp_path):
    """`~/.sp` is kept read-only, so creating a new subdirectory needs the parent unlocked.

    Reported from a real `sp init`: the store existed and was mode 555, so
    `~/.sp/versification` could not be created and the schemes never installed.
    """
    import os

    from llmflow.cli_utils import _lock_sp_dir, install_global_versification
    from llmflow.utils.versification import MAPPINGS_DIRNAME

    store = tmp_path / "sp"
    store.mkdir()
    _lock_sp_dir(store)
    assert not os.access(store, os.W_OK), "the store must be locked for this to test anything"

    try:
        install_global_versification(sp_home=store)
        assert (store / MAPPINGS_DIRNAME / "org.json").is_file()
    finally:
        for path in (store / MAPPINGS_DIRNAME, store):
            if path.exists():
                path.chmod(0o755)
