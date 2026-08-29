"""Provisioning a resource: the catalog says how to open it, the store says where it is (#217).

A machine that had finished setup and had never registered a resource ran a pipeline that linted
clean and failed deep in execution. Three facts were missing and none of them was the data: which
catalog entry carries a readable text, which file inside it, and how to read that file. They live
in the catalog now, and `~/.sp/resources/` records only what this machine chose.
"""
import json
from pathlib import Path

import pytest

from llmflow import resources as R

# A catalog in the shape of the public one: a dataset entry, and what it provides.
CATALOG = [
    {
        "id": "macula-hebrew",
        "name": "Macula Hebrew",
        "category": "Hebrew Bible — Base Texts & Morphology",
        "license": "CC BY 4.0",
        "github": "https://github.com/Clear-Bible/macula-hebrew",
        "provides": [
            {
                "id": "WLC",
                "name": "Westminster Leningrad Codex",
                "kind": "tsv",
                "path": "WLC/tsv/macula-hebrew.tsv",
                "versification": "org",
                "canon": "OT",
                "language": "Hebrew",
            }
        ],
    },
    {
        "id": "acai",
        "name": "ACAI",
        "category": "Entity Annotation",
        "license": "CC BY-SA 4.0",
        "github": "https://github.com/BibleAquifer/ACAI",
    },
]


@pytest.fixture
def catalog(tmp_path, monkeypatch):
    path = tmp_path / "resources.json"
    path.write_text(json.dumps(CATALOG), encoding="utf-8")
    monkeypatch.setattr(R, "catalog_path", lambda: path)
    R.catalog.cache_clear()
    yield path
    R.catalog.cache_clear()


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("SP_HOME", str(tmp_path / "sp"))
    return tmp_path / "sp"


# --- the catalog ---------------------------------------------------------------------


def test_only_entries_that_provide_something_are_readable(catalog):
    """ACAI is in the catalog and is not a text; asking for it is not a silent empty result."""
    assert set(R.readable()) == {"WLC"}


def test_a_readable_item_carries_what_the_engine_needs_to_open_it(catalog):
    wlc = R.readable()["WLC"]
    assert wlc["kind"] == "tsv"
    assert wlc["path"] == "WLC/tsv/macula-hebrew.tsv"
    assert wlc["versification"] == "org"


def test_a_readable_item_knows_which_dataset_carries_it(catalog):
    """One download may provide several texts, so the item has to name its own source.

    The directory is the repository path, not the catalog id: an id is a label someone chose
    and may rename, while `Clear-Bible/macula-hebrew` is the resource's actual identity and
    cannot collide with another contributor's.
    """
    assert R.readable()["WLC"]["dataset"] == "Clear-Bible/macula-hebrew"
    assert R.readable()["WLC"]["source_id"] == "macula-hebrew"


def test_a_resource_not_in_git_is_named_for_its_host_and_file():
    """Not everything worth reading is on GitHub. A download keeps the same two-part shape:
    where it came from, then which file — so a directory listing still says who published it."""
    entry = {
        "id": "tyndale-study-notes",
        "url": "https://tyndaleopenresources.com/",
        "download": "https://tyndaleopenresources.com/files/tyndale_open-studynotes.zip",
    }
    assert R.dataset_dir(entry) == "https-tyndaleopenresources.com/tyndale_open-studynotes"


def test_a_site_with_no_download_named_falls_back_to_the_catalog_id():
    entry = {"id": "codex-sinaiticus", "url": "https://www.codexsinaiticus.org/en/"}
    assert R.dataset_dir(entry) == "https-www.codexsinaiticus.org/codex-sinaiticus"


def test_a_resource_with_neither_is_its_catalog_id():
    assert R.dataset_dir({"id": "somewhere-else"}) == "somewhere-else"


def test_a_host_that_could_escape_the_directory_is_made_safe():
    entry = {"id": "x", "download": "https://example.com:8443/a/b/../weird name.tar.gz"}
    directory = R.dataset_dir(entry)
    assert ".." not in directory
    assert " " not in directory


def test_the_repository_path_is_taken_from_the_source_url():
    entry = {"id": "x", "github": "https://github.com/Clear-Bible/macula-greek"}
    assert R.dataset_dir(entry) == "Clear-Bible/macula-greek"


def test_the_licence_travels_with_the_item(catalog):
    """A later reader sees the terms without going back to the catalog."""
    assert R.readable()["WLC"]["license"] == "CC BY 4.0"


# --- resolving a path ----------------------------------------------------------------


def test_a_dataset_relative_path_resolves_against_the_store(store):
    definition = {
        "kind": "tsv",
        "dataset": "Clear-Bible/macula-hebrew",
        "path": "WLC/tsv/x.tsv",
    }
    expected = store / "resources" / "Clear-Bible" / "macula-hebrew" / "WLC/tsv/x.tsv"
    assert R.resolve_path(definition) == expected


def test_an_absolute_path_is_honoured_unchanged(store):
    """A maintainer works against their own clone; that registration must keep working."""
    definition = {"kind": "tsv", "path": "/Users/someone/github/macula-hebrew/x.tsv"}
    assert str(R.resolve_path(definition)) == "/Users/someone/github/macula-hebrew/x.tsv"


def test_an_absolute_path_wins_over_a_dataset(store):
    definition = {
        "kind": "tsv",
        "dataset": "macula-hebrew",
        "path": "/Users/someone/clone/x.tsv",
    }
    assert str(R.resolve_path(definition)) == "/Users/someone/clone/x.tsv"


# --- what this machine has -----------------------------------------------------------


def test_absent_when_the_dataset_is_not_downloaded(catalog, store):
    assert R.status("WLC") == "absent"


def test_available_when_the_data_is_there_but_nothing_is_registered(catalog, store):
    tsv = store / "resources" / "Clear-Bible" / "macula-hebrew" / "WLC" / "tsv"
    tsv.mkdir(parents=True)
    (tsv / "macula-hebrew.tsv").write_text("x")
    assert R.status("WLC") == "available"


def test_registered_once_the_store_names_it(catalog, store):
    (store / "registrations").mkdir(parents=True)
    (store / "registrations" / "WLC.yaml").write_text("id: WLC\nkind: tsv\npath: x.tsv\n")
    assert R.status("WLC") == "registered"


# --- the store directory, renamed ----------------------------------------------------


def test_registrations_and_corpora_live_apart(store):
    """Small files saying what this machine may read stay with the configuration; the corpora
    themselves are hundreds of megabytes and do not belong in a dotfile."""
    assert R.default_resources_dir() == store / "registrations"
    assert R.data_dir() == store / "resources"


def test_an_unmigrated_machine_still_reads_its_registrations(store, caplog):
    """Renaming the directory must not fail every pipeline on the machines that upgrade."""
    legacy = store / "editions"
    legacy.mkdir(parents=True)
    (legacy / "WLC.yaml").write_text("id: WLC\nkind: tsv\npath: /tmp/wlc.tsv\n")
    assert "WLC" in R.load_registered()
    assert "sp doctor" in caplog.text, "and it must say how to stop needing the fallback"


def test_the_new_directory_wins_when_both_exist(store):
    for name, path in (("editions", "/tmp/old.tsv"), ("registrations", "/tmp/new.tsv")):
        directory = store / name
        directory.mkdir(parents=True)
        (directory / "WLC.yaml").write_text(f"id: WLC\nkind: tsv\npath: {path}\n")
    assert R.load_registered()["WLC"]["path"] == "/tmp/new.tsv"


def test_the_corpus_directory_is_never_read_as_registrations(store):
    """`resources` names the corpora now. Reading it as a registrations directory would try to
    parse a library of texts as YAML — so it is not in the fallback list."""
    corpus = store / "resources" / "Clear-Bible" / "macula-hebrew"
    corpus.mkdir(parents=True)
    (corpus / "notes.yaml").write_text("id: NOT_A_REGISTRATION\n")
    assert R.load_registered() == {}


# --- registering one -----------------------------------------------------------------


def test_registering_writes_a_file_named_for_the_resource(catalog, store):
    R.register("WLC", download=False)
    assert (store / "registrations" / "WLC.yaml").is_file()


def test_a_registration_records_a_relative_path_not_this_machine_s(catalog, store):
    """The whole point: the file means the same thing on every machine."""
    import yaml

    R.register("WLC", download=False)
    written = yaml.safe_load((store / "registrations" / "WLC.yaml").read_text())
    assert written["path"] == "WLC/tsv/macula-hebrew.tsv"
    assert written["dataset"] == "Clear-Bible/macula-hebrew"
    assert not str(written["path"]).startswith("/")


def test_a_registration_carries_the_scheme_and_the_licence(catalog, store):
    import yaml

    R.register("WLC", download=False)
    written = yaml.safe_load((store / "registrations" / "WLC.yaml").read_text())
    assert written["versification_scheme"] == "org"
    assert written["license"] == "CC BY 4.0"
    assert written["kind"] == "tsv"


def test_registering_something_the_catalog_never_heard_of_is_refused(catalog, store):
    with pytest.raises(KeyError, match="WLC"):
        R.register("NOT_A_TEXT", download=False)


def test_registering_twice_is_not_an_error(catalog, store):
    R.register("WLC", download=False)
    R.register("WLC", download=False)
    assert R.status("WLC") == "registered"


def test_listing_reports_a_status_for_every_readable_resource(catalog, store):
    report = R.report()
    assert [row["id"] for row in report] == ["WLC"]
    assert report[0]["status"] == "absent"
    assert report[0]["dataset"] == "Clear-Bible/macula-hebrew"


# --- a USFM project is a directory, not a file ---------------------------------------


def test_a_usfm_registration_becomes_base_dir_and_project(store):
    """`load_usfm_passage` takes a directory and a project name, so one path must split.

    The catalog can only state one relative path — the project directory inside the download —
    because it describes where things are, not what one reader's signature happens to be.
    """
    from llmflow.utils.scripture import load_registry_editions

    directory = store / "registrations"
    directory.mkdir(parents=True)
    (directory / "BSB.yaml").write_text(
        "id: BSB\nkind: usfm\ndataset: https-bereanbible.com/bsb_usfm\npath: bsb_usfm\n"
    )
    definition = load_registry_editions()["BSB"]
    assert definition["project"] == "bsb_usfm"
    assert definition["base_dir"] == str(store / "resources" / "https-bereanbible.com" / "bsb_usfm")


def test_a_usfm_registration_that_already_says_both_is_left_alone(store):
    from llmflow.utils.scripture import load_registry_editions

    directory = store / "registrations"
    directory.mkdir(parents=True)
    (directory / "OWN.yaml").write_text(
        "id: OWN\nkind: usfm\nbase_dir: /Users/someone/paratext\nproject: MYPROJ\n"
    )
    definition = load_registry_editions()["OWN"]
    assert definition["base_dir"] == "/Users/someone/paratext"
    assert definition["project"] == "MYPROJ"


# --- registering something of your own -----------------------------------------------


def test_a_paratext_project_registers_from_its_path(store, tmp_path):
    """Access to the project is the licence question already answered; sp does not re-ask."""
    project = tmp_path / "paratext" / "MYPROJ"
    project.mkdir(parents=True)
    (project / "Settings.xml").write_text("<Settings><Versification>4</Versification></Settings>")

    R.register_local("MYPROJ", project)

    import yaml

    written = yaml.safe_load((store / "registrations" / "MYPROJ.yaml").read_text())
    assert written["kind"] == "usfm"
    assert written["project"] == "MYPROJ"
    assert written["base_dir"] == str(project.parent)
    assert written["versification_scheme"] == "eng", "read from Settings.xml, not guessed"


def test_a_local_file_registers_with_the_kind_you_name(store, tmp_path):
    tsv = tmp_path / "my.tsv"
    tsv.write_text("ref\ttext\tafter\n")

    R.register_local("MINE", tsv, kind="tsv", versification="org")

    import yaml

    written = yaml.safe_load((store / "registrations" / "MINE.yaml").read_text())
    assert written["kind"] == "tsv"
    assert written["path"] == str(tsv), "an absolute path, because it is not in the store"
    assert written["versification_scheme"] == "org"


def test_a_local_file_with_no_kind_is_refused(store, tmp_path):
    plain = tmp_path / "mystery.dat"
    plain.write_text("x")
    with pytest.raises(ValueError, match="kind"):
        R.register_local("MYSTERY", plain)


def test_registering_a_path_that_is_not_there_is_refused(store, tmp_path):
    with pytest.raises(FileNotFoundError):
        R.register_local("GHOST", tmp_path / "nowhere", kind="tsv")


# --- asking for something that is not registered -------------------------------------


def test_the_refusal_names_a_command_that_exists():
    """The old message said `sp registry`, which had no subcommand that could register."""
    from llmflow.utils.scripture import ResourceNotRegistered, resolve_edition

    with pytest.raises(ResourceNotRegistered) as raised:
        resolve_edition("NO_SUCH", registry_editions={"WLC": "/tmp/wlc.tsv"})
    message = str(raised.value)
    assert "NO_SUCH" in message
    assert "WLC" in message, "the reader is told what is registered"
    assert "sp resource add" in message


def test_the_refusal_says_when_the_catalog_knows_the_resource():
    """`available` and `absent` are different problems and want different remedies."""
    from llmflow.utils.scripture import ResourceNotRegistered, resolve_edition

    with pytest.raises(ResourceNotRegistered) as raised:
        resolve_edition("SBLGNT", registry_editions={})
    assert "sp resource add SBLGNT" in str(raised.value)


# --- the vendored copy ---------------------------------------------------------------

UPSTREAM = (
    Path.home() / "github/nida-institute/awesome-biblical-data" / R.CATALOG_FILENAME
)

upstream = pytest.mark.skipif(
    not UPSTREAM.is_file(), reason="the catalog's home repository is not on this machine"
)


@upstream
def test_the_vendored_catalog_matches_its_source():
    """It is maintained in `awesome-biblical-data` and copied here so nothing needs a network.

    A copy that has drifted is worse than no copy: `sp resource list` would describe resources
    this machine cannot get, and the difference would be invisible.
    """
    assert R.catalog_path().read_text(encoding="utf-8") == UPSTREAM.read_text(encoding="utf-8")


def test_every_readable_item_in_the_real_catalog_can_be_opened():
    """The four facts are what a reader needs; an item missing one cannot be acted on."""
    for identifier, item in R.readable().items():
        for field in ("kind", "path", "versification", "canon", "language"):
            assert item.get(field), f"{identifier} has no {field}"
        assert item["kind"] in ("tsv", "tei", "usfm"), f"{identifier}: unknown kind"
        assert item["canon"] in ("OT", "NT", "OT+NT"), f"{identifier}: unknown canon"
        assert item["dataset"], f"{identifier} names no dataset"
        assert not Path(item["path"]).is_absolute(), f"{identifier}: path must be relative"


def test_the_catalog_answers_the_scheme_a_name_alone_used_to_answer():
    """`known_editions` held WLC and SBLGNT; the catalog holds them now, and only one may.

    The table matched on the id string, which two people can choose independently. The catalog
    is anchored to a repository and a file inside it, so it is the stronger identity and wins.
    """
    from llmflow.utils.scripture import _edition_table, _known_editions

    hand_written = {
        key for key in _edition_table().get("known_editions", {}) if not key.startswith("$")
    }
    assert hand_written == set(), f"still hand-listed: {sorted(hand_written)}"

    resolved = _known_editions()
    for identifier, scheme in (("WLC", "org"), ("SBLGNT", "org"), ("BSB", "eng")):
        assert resolved[identifier]["scheme"] == scheme
        assert resolved[identifier]["source"] == "catalog"


def test_the_evidence_for_a_scheme_travelled_with_it():
    """The `why` strings were established by a human and are not lost in the move."""
    assert "PSA 51" in R.readable()["WLC"]["versification_why"]
    assert "3JN 15" in R.readable()["SBLGNT"]["versification_why"]


def test_every_declared_versification_is_a_scheme_we_ship():
    from llmflow.utils.versification import packaged_scheme_names

    known = set(packaged_scheme_names())
    for identifier, item in R.readable().items():
        assert item["versification"] in known, f"{identifier}: unknown scheme"
