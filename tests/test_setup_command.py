"""Tests for llmflow setup command registration and argument parsing."""
import sys
from llmflow.cli import build_parser


def test_setup_subcommand_is_registered():
    parser = build_parser()
    # Should not raise
    args = parser.parse_args(["setup"])
    assert args.command == "setup"
    assert args.update is False


def test_setup_update_flag():
    parser = build_parser()
    args = parser.parse_args(["setup", "--update"])
    assert args.command == "setup"
    assert args.update is True
