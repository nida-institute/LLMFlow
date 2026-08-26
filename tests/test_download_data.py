"""Tests for sp download-data command."""
import io
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Capture the real SystemExit before test_lint_exit.py can patch builtins.SystemExit
# (test_lint_exit.py replaces builtins.SystemExit with a TracedSystemExit subclass at
# module load time, which breaks pytest.raises(SystemExit) for the full-suite run).
_SystemExit = SystemExit

from llmflow.cli import build_parser


# --- Parser registration ---

def test_download_data_subcommand_registered():
    parser = build_parser()
    args = parser.parse_args(["download-data"])
    assert args.command == "download-data"
    assert args.dataset is None
    assert args.list is False
    assert args.dest is None


def test_download_data_list_flag():
    parser = build_parser()
    args = parser.parse_args(["download-data", "--list"])
    assert args.list is True


def test_download_data_dataset_positional():
    parser = build_parser()
    args = parser.parse_args(["download-data", "macula-greek"])
    assert args.dataset == "macula-greek"


def test_download_data_dest_flag():
    parser = build_parser()
    args = parser.parse_args(["download-data", "macula-greek", "--dest", "/tmp/data"])
    assert args.dataset == "macula-greek"
    assert args.dest == "/tmp/data"


# --- Module-level logic ---

from llmflow.download_data import CATALOG, get_default_data_dir, run_download_data


def test_catalog_contains_required_datasets():
    assert "macula-greek" in CATALOG
    assert "macula-hebrew" in CATALOG
    assert "berean-usx" in CATALOG
    for name, entry in CATALOG.items():
        assert "repo" in entry
        assert "license" in entry
        assert "description" in entry
        assert "approx_size" in entry


def test_default_data_dir_is_home_sp_data(monkeypatch):
    monkeypatch.delenv("SP_HOME", raising=False)  # this asserts the default
    path = get_default_data_dir()
    assert path == Path.home() / ".sp" / "data"


def test_llmflow_data_dir_env_overrides_default(monkeypatch):
    monkeypatch.setenv("LLMFLOW_DATA_DIR", "/custom/data")
    path = get_default_data_dir()
    assert path == Path("/custom/data")


def test_no_args_shows_usage_hint(capsys):
    run_download_data()
    out = capsys.readouterr().out
    assert "sp download-data --list" in out
    assert "Available datasets" in out


def test_list_shows_catalog(capsys):
    run_download_data(list_only=True)
    out = capsys.readouterr().out
    assert "macula-greek" in out
    assert "macula-hebrew" in out
    assert "berean-usx" in out
    assert "CC BY 4.0" in out


def test_unknown_dataset_exits_with_error():
    with pytest.raises(_SystemExit) as exc:
        run_download_data(dataset="nonexistent-dataset")
    assert exc.value.code == 1


def test_download_skips_if_dest_already_exists(tmp_path):
    """If dataset dir already exists, skip download without network call."""
    dest_dataset = tmp_path / "macula-greek"
    dest_dataset.mkdir()

    with patch("urllib.request.urlopen") as mock_urlopen:
        run_download_data(dataset="macula-greek", dest=str(tmp_path))
        mock_urlopen.assert_not_called()


def _make_fake_zip(repo_name: str, branch: str, files: dict[str, str]) -> bytes:
    """Build a zipball with the GitHub structure (/<repo>-<branch>/<files>)."""
    prefix = f"{repo_name}-{branch}/"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for path, content in files.items():
            zf.writestr(f"{prefix}{path}", content)
    return buf.getvalue()


def test_download_extracts_files(tmp_path):
    """Downloading a dataset fetches a zipball and strips the top-level prefix."""
    fake_zip = _make_fake_zip(
        "macula-greek", "main",
        {"README.md": "# Macula Greek", "data/example.xml": "<root/>"},
    )

    mock_response = MagicMock()
    mock_response.read.return_value = fake_zip
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        run_download_data(dataset="macula-greek", dest=str(tmp_path))

    assert (tmp_path / "macula-greek" / "README.md").exists()
    assert (tmp_path / "macula-greek" / "data" / "example.xml").exists()


def test_download_network_error_exits(tmp_path):
    with patch("urllib.request.urlopen", side_effect=OSError("Network error")):
        with pytest.raises(_SystemExit) as exc:
            run_download_data(dataset="macula-greek", dest=str(tmp_path))
    assert exc.value.code == 1


def test_download_cleans_up_on_extraction_failure(tmp_path):
    """Partial extraction dir is removed when zipfile is corrupt."""
    mock_response = MagicMock()
    mock_response.read.return_value = b"not a zip"
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        with pytest.raises(_SystemExit) as exc:
            run_download_data(dataset="macula-greek", dest=str(tmp_path))
    assert exc.value.code == 1
    # Partial dest dir should be cleaned up
    assert not (tmp_path / "macula-greek").exists()
