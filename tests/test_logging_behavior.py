"""
Tests for logging behavior: log file overwriting and output filtering.

REQUIREMENTS:
1. Log file should be overwritten with each run (not appended)
2. Detailed debugging output goes to log file
3. Screen output should only show:
   - Status of each step
   - Which files are written
"""
import logging
import pytest
import tempfile
from pathlib import Path


def test_log_file_is_overwritten_not_appended(tmp_path):
    """
    CRITICAL: Log file should be overwritten on each run, not appended.

    This prevents the log file from growing indefinitely across multiple runs.
    """
    from llmflow.modules.logger import Logger

    log_file = tmp_path / "test.log"

    # First run - write something to log
    Logger.reset()  # Reset singleton for fresh start
    logger1 = Logger(log_file=str(log_file))
    logger1.info("First run message")
    logger1.debug("First run debug")

    # Verify log file was created
    assert log_file.exists()
    first_content = log_file.read_text()
    assert "First run message" in first_content

    # Second run - log file should be overwritten
    Logger.reset()  # Reset singleton to create new log file
    logger2 = Logger(log_file=str(log_file))
    logger2.info("Second run message")
    logger2.debug("Second run debug")

    # Read log file content
    second_content = log_file.read_text()

    # Should contain second run messages
    assert "Second run message" in second_content

    # Should NOT contain first run messages (file was overwritten)
    assert "First run message" not in second_content, \
        "Log file should be overwritten, not appended. First run content still present."


def test_console_shows_only_status_and_files(tmp_path, capsys):
    """
    Screen output should show:
    - Step status (INFO level)
    - Files written

    It should NOT show:
    - Debug details
    - Verbose processing information
    """
    from llmflow.runner import run_pipeline

    # Create simple pipeline
    pipeline_file = tmp_path / "test.yaml"
    pipeline_file.write_text("""
name: Test Pipeline
steps:
  - name: step1
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: "test"
    outputs: result
""")

    # Run pipeline
    run_pipeline(str(pipeline_file))

    # Capture console output
    captured = capsys.readouterr()
    console_output = captured.err  # Logger writes to stderr

    # Should contain step status
    assert "step1" in console_output.lower() or "✅" in console_output

    # Should NOT contain debug details (these go to log file only)
    # Debug messages typically have more verbose formatting
    assert "DEBUG" not in console_output, \
        "Console should not show DEBUG level messages"


def test_debug_details_go_to_log_file(tmp_path):
    """
    Detailed debug information should be written to log file,
    even when not shown on screen.
    """
    from llmflow.runner import run_pipeline
    import os

    # Change to tmp_path so log file is created there
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        log_file = tmp_path / "llmflow.log"

        # Create pipeline with debug logging
        pipeline_file = tmp_path / "test.yaml"
        pipeline_file.write_text("""
name: Test Pipeline
linter_config:
  log_level: debug
steps:
  - name: debug_step
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: "test"
    outputs: result
    log: debug
""")

        # Run pipeline (this should create log file in current directory)
        run_pipeline(str(pipeline_file))

        # Log file should exist and contain debug information
        assert log_file.exists(), "Log file should be created"

        log_content = log_file.read_text()

        # Should contain debug-level details
        assert "DEBUG" in log_content or "debug" in log_content.lower(), \
            "Log file should contain debug information"
    finally:
        os.chdir(original_dir)


def test_file_writes_are_logged_to_screen(tmp_path, capsys):
    """
    When a file is written, it should be reported on screen.
    """
    from llmflow.runner import run_pipeline

    output_file = tmp_path / "output.txt"

    # Create pipeline that writes a file
    pipeline_file = tmp_path / "test.yaml"
    pipeline_file.write_text(f"""
name: Test Pipeline
steps:
  - name: write_file
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: "test data"
    outputs: result
    saveas: "{output_file}"
""")

    # Run pipeline
    run_pipeline(str(pipeline_file))

    # Capture console output
    captured = capsys.readouterr()
    console_output = captured.err

    # Should mention the file that was written
    assert str(output_file) in console_output or "output.txt" in console_output, \
        "Console should report which files were written"


def test_logger_file_handler_mode_is_write_not_append():
    """
    Verify that the FileHandler uses 'w' mode (write/overwrite) not 'a' (append).
    """
    from llmflow.modules.logger import Logger
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_file = f.name

    try:
        logger = Logger(log_file=log_file)

        # Find the file handler
        file_handler = None
        for handler in logger.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break

        assert file_handler is not None, "Should have a FileHandler"

        # Check that mode is 'w' (write/overwrite) not 'a' (append)
        assert file_handler.mode == 'w', \
            f"FileHandler should use mode='w' (overwrite), not '{file_handler.mode}'"
    finally:
        Path(log_file).unlink(missing_ok=True)


def test_console_handler_uses_info_level():
    """
    Console handler should be at INFO level to avoid cluttering screen with debug.
    File handler should accept DEBUG level for detailed logging.
    """
    from llmflow.modules.logger import Logger
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_file = f.name

    try:
        logger = Logger(log_file=log_file)
        logger.set_level("DEBUG")  # Enable debug logging

        # Find handlers
        console_handler = None
        file_handler = None

        for handler in logger.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                console_handler = handler
            elif isinstance(handler, logging.FileHandler):
                file_handler = handler

        assert console_handler is not None, "Should have a console handler"
        assert file_handler is not None, "Should have a file handler"

        # Console should filter to INFO level (no debug spam)
        assert console_handler.level == logging.INFO, \
            "Console handler should be at INFO level to avoid debug spam"

        # File handler should accept DEBUG for detailed logging
        assert file_handler.level == logging.DEBUG, \
            "File handler should accept DEBUG level for detailed logging"
    finally:
        Path(log_file).unlink(missing_ok=True)
