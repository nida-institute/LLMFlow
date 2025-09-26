import pytest
import logging
from llmflow.utils.linter import configure_linter_logging

class TestLoggingConfiguration:
    """Test the logging configuration from pipeline config"""

    def test_configure_linter_logging_from_config(self):
        """Test that log_level in linter_config works"""
        linter_config = {"log_level": "debug"}
        logger = configure_linter_logging(linter_config)

        assert logger.level == logging.DEBUG

    def test_default_log_level(self):
        """Test default log level if not specified"""
        linter_config = {}
        logger = configure_linter_logging(linter_config)

        assert logger.level == logging.INFO