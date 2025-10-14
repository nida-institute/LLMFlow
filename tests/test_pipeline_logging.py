"""
Test suite for pipeline logging functionality.

This tests:
- PipelineLogger class behavior
- Verbose flag functionality
- Log file output
"""

import pytest
from src.llmflow.modules.logger import Logger
import os
import tempfile
import sys
from io import StringIO
from unittest.mock import patch, MagicMock
from llmflow.runner import PipelineLogger


class TestPipelineLogger:
    """Test the PipelineLogger class functionality"""

    def test_logger_initialization(self):
        """Test logger is created with correct handlers"""
        logger = PipelineLogger(verbose=False)

        # Should have 2 handlers: console and file
        assert len(logger.logger.handlers) == 2

        # Check handler types
        handlers = logger.logger.handlers
        console_handler = next((h for h in handlers if hasattr(h, 'stream') and h.stream in (sys.stdout, sys.stderr)), None)
        file_handler = next((h for h in handlers if hasattr(h, 'baseFilename')), None)

        assert console_handler is not None, "Console handler not found"
        assert file_handler is not None, "File handler not found"

        # Console should be INFO by default
        assert console_handler.level == logging.INFO
        # File should be DEBUG
        assert file_handler.level == logging.DEBUG

    def test_verbose_flag_changes_console_level(self):
        """Test that verbose=True sets console to DEBUG"""
        logger = PipelineLogger(verbose=True)

        # Find console handler
        console_handler = next(h for h in logger.logger.handlers if hasattr(h, 'stream'))
        assert console_handler.level == logging.DEBUG

    def test_set_verbose_method(self):
        """Test that set_verbose() changes console handler level"""
        logger = PipelineLogger(verbose=False)

        # Initially INFO - find the StreamHandler that's not a FileHandler
        console_handler = next(h for h in logger.logger.handlers
                               if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler))
        assert console_handler.level == logging.INFO

        # Change to verbose
        logger.set_verbose(True)
        assert console_handler.level == logging.DEBUG

        # Change back
        logger.set_verbose(False)
        assert console_handler.level == logging.INFO

    def test_log_step_messages(self):
        """Test step execution message methods"""
        logger = PipelineLogger(verbose=False)

        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_step_start('test_step', 'function')
            mock_info.assert_called_with('🚀 Executing: test_step (function)')

            logger.log_step_complete('test_step')
            mock_info.assert_called_with('✅ Completed: test_step')

    def test_debug_messages_only_in_verbose(self):
        """Test that DEBUG messages only appear with verbose=True"""
        # Non-verbose: DEBUG should not appear on console
        captured_output = StringIO()
        logger = PipelineLogger(verbose=False)

        # Replace console handler stream - find the StreamHandler that's not a FileHandler
        console_handler = next(h for h in logger.logger.handlers
                               if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler))
        original_stream = console_handler.stream
        console_handler.stream = captured_output

        logger.logger.debug("DEBUG: This should not appear")
        logger.logger.info("INFO: This should appear")

        output = captured_output.getvalue()
        # With INFO level console handler, DEBUG messages should not appear
        assert "DEBUG: This should not appear" not in output
        assert "INFO: This should appear" in output

        # Verbose: DEBUG should appear
        captured_output = StringIO()
        logger.set_verbose(True)
        console_handler.stream = captured_output

        logger.logger.debug("DEBUG: This should appear")
        logger.logger.info("INFO: This should also appear")

        output = captured_output.getvalue()
        assert "DEBUG: This should appear" in output
        assert "INFO: This should also appear" in output

    def test_log_file_always_gets_debug(self):
        """Test that log file always receives DEBUG messages"""
        # Save current working directory
        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Change to temp directory
                os.chdir(tmpdir)

                logger = PipelineLogger(verbose=False)

                logger.logger.debug("DEBUG: Test debug message")
                logger.logger.info("INFO: Test info message")

                # Force flush
                for handler in logger.logger.handlers:
                    handler.flush()

                # Read log file (it's created as llmflow.log)
                with open('llmflow.log', 'r') as f:
                    content = f.read()

                assert "DEBUG: Test debug message" in content
                assert "INFO: Test info message" in content

            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])