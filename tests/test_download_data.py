"""Fetching a catalog resource onto this machine (#217).

`sp download-data` is gone. It carried its own four-entry catalog — a smaller, drifting copy of
the public one, whose `berean-usx` entry pointed at a repository that 404s and whose dataset
names disagreed with the catalog's ids. Fetching now reads the public catalog, and the command
surface is `sp resource`.
"""
import io
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from llmflow.cli import build_parser
from llmflow.download_data import _archive_url, fetch, get_default_data_dir

MACULA = {
    "id": "macula-greek-nt",
    "name": "Macula Greek NT",
    "github": "https://github.com/Clear-Bible/macula-greek",
    "dataset": "Clear-Bible/macula-greek",
}


# --- the command surface -------------------------------------------------------------


def test_download_data_is_gone():
    """One surface for resources; two commands that fetch was the thing being removed."""
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["download-data", "macula-greek"])


@pytest.mark.parametrize(
    "argv,expected",
    [
        (["resource", "list"], {"resource_command": "list"}),
        (["resource", "add", "WLC"], {"id": "WLC", "no_download": False}),
        (["resource", "add", "WLC", "--no-download"], {"no_download": True}),
        (["resource", "download", "acai"], {"id": "acai"}),
    ],
)
def test_the_resource_surface_parses(argv, expected):
    args = build_parser().parse_args(argv)
    for key, value in expected.items():
        assert getattr(args, key) == value


def test_registering_your_own_takes_a_path_and_a_kind():
    args = build_parser().parse_args(
        ["resource", "add", "MINE", "--path", "/data/x.tsv", "--kind", "tsv"]
    )
    assert (args.path, args.kind) == ("/data/x.tsv", "tsv")


# --- where a resource is fetched from ------------------------------------------------


def test_a_repository_is_fetched_as_its_default_branch_zip():
    assert _archive_url(MACULA).endswith("/archive/refs/heads/main.zip")


def test_a_named_download_is_fetched_as_it_stands():
    source = {"id": "x", "download": "https://example.com/files/thing.zip"}
    assert _archive_url(source) == "https://example.com/files/thing.zip"


def test_a_resource_with_no_source_says_so():
    with pytest.raises(ValueError, match="nowhere to fetch"):
        _archive_url({"id": "bdag"})


# --- the data directory --------------------------------------------------------------


def test_the_fetcher_and_the_reader_agree_on_where_data_lives(monkeypatch, tmp_path):
    """They did not, and a real `sp resource add` unpacked 150MB where nothing would read it.

    `download_data` kept its own idea of the data directory — the old hidden `~/.sp/data` —
    while `resources.resolve_path` had moved to the visible one. Two encodings of one fact,
    agreeing until they silently did not.
    """
    from llmflow import resources as R

    for env in ({}, {"SP_HOME": str(tmp_path / "sp")}, {"LLMFLOW_DATA_DIR": str(tmp_path / "d")}):
        monkeypatch.delenv("SP_HOME", raising=False)
        monkeypatch.delenv("LLMFLOW_DATA_DIR", raising=False)
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        assert get_default_data_dir() == R.data_dir(), f"disagree with {env}"


def test_default_data_dir_is_visible(monkeypatch):
    monkeypatch.delenv("SP_HOME", raising=False)
    monkeypatch.delenv("LLMFLOW_DATA_DIR", raising=False)
    assert get_default_data_dir() == Path.home() / "sp" / "resources"


def test_llmflow_data_dir_env_overrides_default(monkeypatch):
    monkeypatch.setenv("LLMFLOW_DATA_DIR", "/custom/data")
    assert get_default_data_dir() == Path("/custom/data")


# --- fetching ------------------------------------------------------------------------


def _zip(prefix: str, files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        for path, content in files.items():
            archive.writestr(f"{prefix}{path}", content)
    return buf.getvalue()


def _response(data: bytes) -> MagicMock:
    mock = MagicMock()
    mock.read.return_value = data
    mock.__enter__ = lambda self: self
    mock.__exit__ = MagicMock(return_value=False)
    return mock


def test_present_data_is_not_fetched_again(tmp_path):
    (tmp_path / "already").mkdir()
    with patch("urllib.request.urlopen") as urlopen:
        assert fetch(MACULA, dest=tmp_path / "already") == tmp_path / "already"
        urlopen.assert_not_called()


def test_a_repository_archive_loses_its_wrapper_directory(tmp_path):
    data = _zip("macula-greek-main/", {"README.md": "#", "data/x.xml": "<r/>"})
    with patch("urllib.request.urlopen", return_value=_response(data)):
        fetch(MACULA, dest=tmp_path / "out")
    assert (tmp_path / "out" / "README.md").is_file()
    assert (tmp_path / "out" / "data" / "x.xml").is_file()


def test_a_plain_download_keeps_its_own_layout(tmp_path):
    """A site's zip is not a GitHub archive and has no wrapper to strip."""
    source = {"id": "tyndale", "download": "https://example.com/t.zip", "dataset": "x"}
    data = _zip("", {"notes/GEN.xml": "<n/>"})
    with patch("urllib.request.urlopen", return_value=_response(data)):
        fetch(source, dest=tmp_path / "out")
    assert (tmp_path / "out" / "notes" / "GEN.xml").is_file()


def test_a_download_that_is_not_an_archive_is_saved_as_a_file(tmp_path):
    source = {"id": "tables", "download": "https://example.com/bsb_tables.tsv", "dataset": "x"}
    with patch("urllib.request.urlopen", return_value=_response(b"ref\ttext\n")):
        fetch(source, dest=tmp_path / "out")
    assert (tmp_path / "out" / "bsb_tables.tsv").read_bytes() == b"ref\ttext\n"


def test_an_archive_cannot_write_outside_its_own_directory(tmp_path):
    """A zip naming `../` must not reach the rest of the store."""
    source = {"id": "hostile", "download": "https://example.com/h.zip", "dataset": "x"}
    data = _zip("", {"../escaped.txt": "no", "fine.txt": "yes"})
    with patch("urllib.request.urlopen", return_value=_response(data)):
        fetch(source, dest=tmp_path / "out")
    assert (tmp_path / "out" / "fine.txt").is_file()
    assert not (tmp_path / "escaped.txt").exists()


# --- what version is this? -----------------------------------------------------------


def test_a_fetch_records_what_it_fetched(tmp_path):
    """Two machines with identically-named directories held different bytes and nothing said so.

    That is the failure a shared directory does not fix: skew is invisible until an analysis
    disagrees between projects and nobody can say which copy is which.
    """
    from llmflow import resources as R

    data = _zip("macula-greek-main/", {"README.md": "#"})
    with patch("urllib.request.urlopen", return_value=_response(data)):
        fetch(MACULA, dest=tmp_path / "out")

    recorded = R.installed_version(tmp_path / "out")
    assert recorded["id"] == "macula-greek-nt"
    assert recorded["source"].endswith("/archive/refs/heads/main.zip")
    assert recorded["branch"] == "main"
    assert len(recorded["sha256"]) == 64
    assert recorded["fetched"], "when, so a stale copy can be recognised"


def test_the_same_bytes_hash_the_same(tmp_path):
    from llmflow import resources as R

    data = _zip("macula-greek-main/", {"README.md": "#"})
    for name in ("one", "two"):
        with patch("urllib.request.urlopen", return_value=_response(data)):
            fetch(MACULA, dest=tmp_path / name)
    first = R.installed_version(tmp_path / "one")["sha256"]
    assert first == R.installed_version(tmp_path / "two")["sha256"]


def test_different_bytes_hash_differently(tmp_path):
    from llmflow import resources as R

    for name, content in (("june", "old"), ("today", "new")):
        data = _zip("macula-greek-main/", {"README.md": content})
        with patch("urllib.request.urlopen", return_value=_response(data)):
            fetch(MACULA, dest=tmp_path / name)
    assert (
        R.installed_version(tmp_path / "june")["sha256"]
        != R.installed_version(tmp_path / "today")["sha256"]
    )


def test_data_placed_by_hand_has_no_recorded_version(tmp_path):
    """Absence is the honest answer, not a guess — and doctor reports it."""
    from llmflow import resources as R

    (tmp_path / "byhand").mkdir()
    assert R.installed_version(tmp_path / "byhand") is None


def test_a_failed_fetch_leaves_no_half_unpacked_directory(tmp_path):
    with patch("urllib.request.urlopen", side_effect=OSError("network")):
        with pytest.raises(OSError):
            fetch(MACULA, dest=tmp_path / "out")
    assert not (tmp_path / "out").exists()
