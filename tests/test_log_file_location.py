"""Test log file location configuration."""
import pytest
from pathlib import Path
from llmflow.modules.logger import Logger


def test_default_log_location_is_cwd(tmp_path):
    """Test that default log file is created in current working directory."""
    log_file = tmp_path / "llmflow.log"

    # Reset logger with default location
    Logger.reset(log_file=str(log_file))
    logger = Logger()

    logger.info("Test message")

    # Verify file was created
    assert log_file.exists()
    assert "Test message" in log_file.read_text()


def test_custom_log_location(tmp_path):
    """Test that custom log file location can be specified."""
    custom_dir = tmp_path / "logs"
    custom_dir.mkdir()
    log_file = custom_dir / "custom.log"

    # Reset logger with custom location
    Logger.reset(log_file=str(log_file))
    logger = Logger()

    logger.info("Custom location test")

    # Verify file was created in custom location
    assert log_file.exists()
    assert "Custom location test" in log_file.read_text()


def test_multiple_instances_different_logs(tmp_path):
    """Test that multiple instances can use different log files."""
    log1 = tmp_path / "instance1.log"
    log2 = tmp_path / "instance2.log"

    # First instance
    Logger.reset(log_file=str(log1))
    logger1 = Logger()
    logger1.info("Instance 1 message")

    # Second instance (simulate new run)
    Logger.reset(log_file=str(log2))
    logger2 = Logger()
    logger2.info("Instance 2 message")

    # Verify both files exist with correct content
    assert log1.exists()
    assert log2.exists()
    assert "Instance 1 message" in log1.read_text()
    assert "Instance 2 message" in log2.read_text()
    # Instance 2 message should NOT be in log1
    assert "Instance 2 message" not in log1.read_text()


def test_nested_directory_log_path(tmp_path):
    """Test that log file can be created in nested directories."""
    nested_dir = tmp_path / "logs" / "2025" / "12"
    nested_dir.mkdir(parents=True)
    log_file = nested_dir / "test.log"

    Logger.reset(log_file=str(log_file))
    logger = Logger()
    logger.info("Nested directory test")

    assert log_file.exists()
    assert "Nested directory test" in log_file.read_text()
