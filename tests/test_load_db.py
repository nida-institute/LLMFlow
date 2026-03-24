"""Tests for sp load-db command."""
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# tests/__init__.py captures the real SystemExit before test_lint_exit.py patches
# builtins.SystemExit.  test_load_db.py sorts after test_lint_exit.py
# alphabetically ("load" > "lint"), so _SystemExit = SystemExit here would
# capture TracedSystemExit instead of the real C-level class.
from tests import _real_system_exit as _SystemExit

from llmflow.cli import build_parser


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def test_load_db_subcommand_registered():
    parser = build_parser()
    args = parser.parse_args(["load-db"])
    assert args.command == "load-db"
    assert args.driver is None
    assert args.dataset is None
    assert args.db_name is None
    assert args.force is False
    assert args.source is None
    assert args.list_drivers is False


def test_load_db_positional_args():
    parser = build_parser()
    args = parser.parse_args(["load-db", "basex", "acai"])
    assert args.driver == "basex"
    assert args.dataset == "acai"


def test_load_db_name_flag():
    parser = build_parser()
    args = parser.parse_args(["load-db", "basex", "acai", "--name", "my_acai"])
    assert args.db_name == "my_acai"


def test_load_db_force_flag():
    parser = build_parser()
    args = parser.parse_args(["load-db", "basex", "acai", "--force"])
    assert args.force is True


def test_load_db_source_flag():
    parser = build_parser()
    args = parser.parse_args(["load-db", "basex", "acai", "--source", "/data/acai"])
    assert args.source == "/data/acai"


def test_load_db_list_drivers_flag():
    parser = build_parser()
    args = parser.parse_args(["load-db", "--list-drivers"])
    assert args.list_drivers is True


# ---------------------------------------------------------------------------
# run_load_db — driver registry
# ---------------------------------------------------------------------------

def test_list_drivers_includes_basex():
    from llmflow.load_db import list_drivers
    assert "basex" in list_drivers()


def test_register_custom_driver():
    from llmflow.load_db import _DRIVERS, register_driver
    dummy = MagicMock()
    register_driver("_test_driver", dummy)
    assert "_test_driver" in _DRIVERS
    del _DRIVERS["_test_driver"]


# ---------------------------------------------------------------------------
# run_load_db — error paths
# ---------------------------------------------------------------------------

def test_missing_driver_exits(tmp_path):
    from llmflow.load_db import run_load_db
    with pytest.raises(_SystemExit):
        run_load_db(driver=None, dataset="acai")


def test_unknown_driver_exits(tmp_path):
    from llmflow.load_db import run_load_db
    with pytest.raises(_SystemExit):
        run_load_db(driver="postgres", dataset="acai")


def test_missing_dataset_exits(tmp_path):
    from llmflow.load_db import run_load_db
    with pytest.raises(_SystemExit):
        run_load_db(driver="basex", dataset=None)


def test_missing_source_dir_exits(tmp_path):
    from llmflow.load_db import run_load_db
    with patch("llmflow.load_db.get_default_data_dir", return_value=tmp_path):
        with pytest.raises(_SystemExit):
            run_load_db(driver="basex", dataset="acai")


def test_list_drivers_only_returns():
    from llmflow.load_db import run_load_db
    # Should not raise and should not call any driver
    run_load_db(driver=None, dataset=None, list_drivers_only=True)


# ---------------------------------------------------------------------------
# BaseX driver — happy path
# ---------------------------------------------------------------------------

def test_basex_driver_calls_create_db(tmp_path):
    """Successful load: CREATE DB is called with correct args."""
    source = tmp_path / "acai"
    source.mkdir()

    completed = MagicMock()
    completed.returncode = 0
    completed.stderr = ""

    with patch("llmflow.load_db.subprocess.run", return_value=completed) as mock_run:
        from llmflow.load_db import _load_basex
        _load_basex(source, "acai", force=False)

    # Last call must be CREATE DB with the db name in the command string
    last_call_args = mock_run.call_args_list[-1][0][0]
    last_cmd = " ".join(last_call_args)
    assert "CREATE DB" in last_cmd
    assert "acai" in last_cmd


def test_basex_driver_force_drops_then_creates(tmp_path):
    """--force: DROP DB is called before CREATE DB."""
    source = tmp_path / "acai"
    source.mkdir()

    completed = MagicMock()
    completed.returncode = 0
    completed.stderr = ""

    with patch("llmflow.load_db.subprocess.run", return_value=completed) as mock_run:
        from llmflow.load_db import _load_basex
        _load_basex(source, "acai", force=True)

    cmds = [" ".join(c[0][0]) for c in mock_run.call_args_list]
    assert any("DROP DB" in c for c in cmds)
    assert any("CREATE DB" in c for c in cmds)
    # DROP must come before CREATE
    drop_idx = next(i for i, c in enumerate(cmds) if "DROP DB" in c)
    create_idx = next(i for i, c in enumerate(cmds) if "CREATE DB" in c)
    assert drop_idx < create_idx


def test_basex_driver_exits_on_create_failure(tmp_path):
    """Non-zero basex exit → sys.exit(1)."""
    source = tmp_path / "acai"
    source.mkdir()

    completed = MagicMock()
    completed.returncode = 1
    completed.stderr = "database error"

    # First run() is the basex availability check (returncode 0 is fine),
    # second run() is the CREATE DB (returncode 1).
    ok = MagicMock(returncode=0, stderr="")

    with patch("llmflow.load_db.subprocess.run", side_effect=[ok, completed]):
        from llmflow.load_db import _load_basex
        with pytest.raises(_SystemExit):
            _load_basex(source, "acai", force=False)


def test_basex_not_on_path_exits(tmp_path):
    """FileNotFoundError from subprocess → sys.exit(1)."""
    source = tmp_path / "acai"
    source.mkdir()

    with patch("llmflow.load_db.subprocess.run", side_effect=FileNotFoundError):
        from llmflow.load_db import _load_basex
        with pytest.raises(_SystemExit):
            _load_basex(source, "acai", force=False)


# ---------------------------------------------------------------------------
# run_load_db — uses custom db_name and --source
# ---------------------------------------------------------------------------

def test_custom_db_name_is_passed_to_driver(tmp_path):
    source = tmp_path / "acai"
    source.mkdir()

    captured = {}

    def _fake_driver(src, name, force):
        captured["name"] = name

    from llmflow.load_db import _DRIVERS, run_load_db
    _DRIVERS["_custom"] = _fake_driver
    try:
        run_load_db(driver="_custom", dataset="acai", db_name="acai_v2", source=str(source))
        assert captured["name"] == "acai_v2"
    finally:
        del _DRIVERS["_custom"]


def test_source_override_used_instead_of_default(tmp_path):
    source = tmp_path / "custom_path"
    source.mkdir()

    captured = {}

    def _fake_driver(src, name, force):
        captured["src"] = src

    from llmflow.load_db import _DRIVERS, run_load_db
    _DRIVERS["_custom2"] = _fake_driver
    try:
        run_load_db(driver="_custom2", dataset="acai", source=str(source))
        assert captured["src"] == source
    finally:
        del _DRIVERS["_custom2"]
