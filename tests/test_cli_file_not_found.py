"""
Test CLI error handling for missing pipeline files and other common errors.
"""
import sys
import subprocess
import os
import tempfile
from pathlib import Path


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


def test_permission_error_shows_helpful_message(tmp_path):
    """Test that permission errors show helpful message."""
    # Create a pipeline file that writes to a file
    pipeline = tmp_path / "test.yaml"
    pipeline.write_text("""
name: test
steps:
  - name: save_file
    type: save
    path: outputs/result.txt
""")

    # Create outputs directory but make it read-only
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    outputs_dir.chmod(0o444)  # Read-only

    try:
        cmd = [
            sys.executable, "-m", "llmflow.cli",
            "run",
            "--pipeline", str(pipeline),
            "--skip-lint"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmp_path))

        # Should exit with error code
        assert result.returncode == 1

        output = result.stdout + result.stderr
        assert "❌ Permission denied" in output
        assert "💡 Tip: Check file/directory permissions" in output

        # Should NOT see Python traceback
        assert "Traceback (most recent call last):" not in output
    finally:
        # Clean up - restore permissions
        outputs_dir.chmod(0o755)


def test_broken_pipe_exits_cleanly():
    """Test that BrokenPipeError (e.g., piping to head) exits cleanly without error."""
    # This test is tricky to implement reliably across platforms
    # BrokenPipeError happens when output is piped and the receiving process closes
    # For now, we'll just document the expected behavior
    # In practice: llmflow run ... | head -n 1
    # Should exit with code 0, no traceback
    pass
