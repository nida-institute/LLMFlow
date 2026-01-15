"""
Test CLI error handling for missing pipeline files.
"""
import sys
import subprocess
import os


def test_cli_run_file_not_found_during_lint():
    """Test that running a non-existent pipeline shows helpful error during lint phase."""
    cmd = [
        sys.executable, "-m", "llmflow.cli",
        "run",
        "--pipeline", "does_not_exist.yaml"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 1
    assert "❌ Pipeline file not found: does_not_exist.yaml" in result.stderr
    assert "Current directory:" in result.stderr
    assert "💡 Tip: Make sure you're running from the correct directory" in result.stderr
    # Should NOT see Python traceback
    assert "Traceback (most recent call last):" not in result.stderr
    assert "FileNotFoundError" not in result.stderr


def test_cli_run_file_not_found_skip_lint():
    """Test that running a non-existent pipeline shows helpful error even with --skip-lint."""
    cmd = [
        sys.executable, "-m", "llmflow.cli",
        "run",
        "--pipeline", "does_not_exist.yaml",
        "--skip-lint"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 1
    assert "❌ Pipeline file not found: does_not_exist.yaml" in result.stderr
    assert "Current directory:" in result.stderr
    assert "💡 Tip: Make sure you're running from the correct directory" in result.stderr
    # Should NOT see Python traceback
    assert "Traceback (most recent call last):" not in result.stderr
    assert "FileNotFoundError" not in result.stderr


def test_cli_run_file_not_found_shows_cwd():
    """Test that error message includes current working directory."""
    cmd = [
        sys.executable, "-m", "llmflow.cli",
        "run",
        "--pipeline", "nonexistent/path/file.yaml"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 1
    assert "Current directory:" in result.stderr
    # Should show actual current directory
    cwd = os.getcwd()
    assert cwd in result.stderr


def test_linter_file_not_found_raises():
    """Test that linter properly re-raises FileNotFoundError for CLI to handle."""
    from llmflow.utils.linter import lint_pipeline_full
    import pytest

    with pytest.raises(FileNotFoundError):
        lint_pipeline_full("totally_does_not_exist.yaml")
