"""Tests for llmflow setup and models commands."""
import json
import sys
from unittest.mock import MagicMock, patch
from llmflow.cli import build_parser


def test_setup_subcommand_is_registered():
    parser = build_parser()
    args = parser.parse_args(["setup"])
    assert args.command == "setup"
    assert args.update is False


def test_setup_update_flag():
    parser = build_parser()
    args = parser.parse_args(["setup", "--update"])
    assert args.command == "setup"
    assert args.update is True


def test_models_subcommand_is_registered():
    parser = build_parser()
    args = parser.parse_args(["models"])
    assert args.command == "models"


# --- llmflow models output tests ---

def _make_keys_path(tmp_path, keys: dict):
    """Write a keys.json to tmp_path and return a mock llm module pointing to it."""
    keys_file = tmp_path / "keys.json"
    keys_file.write_text(json.dumps(keys))
    mock_llm = MagicMock()
    mock_llm.user_dir.return_value = tmp_path
    return mock_llm


def test_models_shows_checkmark_for_configured_provider(tmp_path, capsys):
    from llmflow.setup_command import run_models
    mock_llm = _make_keys_path(tmp_path, {"openai": "sk-test"})
    with patch.dict("sys.modules", {"llm": mock_llm}):
        run_models()
    out = capsys.readouterr().out
    assert "OpenAI" in out
    assert "✅" in out
    assert "gpt-4o" in out


def test_models_shows_no_key_hint_for_unconfigured_provider(tmp_path, capsys):
    from llmflow.setup_command import run_models
    mock_llm = _make_keys_path(tmp_path, {})
    with patch.dict("sys.modules", {"llm": mock_llm}):
        run_models()
    out = capsys.readouterr().out
    assert "no key" in out.lower() or "llmflow setup" in out


def test_models_shows_pip_user_footer(tmp_path, capsys):
    from llmflow.setup_command import run_models
    mock_llm = _make_keys_path(tmp_path, {})
    with patch.dict("sys.modules", {"llm": mock_llm}):
        run_models()
    out = capsys.readouterr().out
    assert "llm.datasette.io" in out or "pip install" in out
