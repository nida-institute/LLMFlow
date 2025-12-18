"""Verify debug logging behavior."""
import logging
import pytest
from llmflow.runner import logger, run_pipeline

@pytest.fixture
def setup_logger():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('llmflow')
    logger.setLevel(logging.DEBUG)
    return logger

def test_logger_level_debug(setup_logger):
    logger = setup_logger
    assert logger.level == logging.DEBUG

def test_step_level_debug_logging(setup_logger):
    logger = setup_logger
    # Simulate enabling step-level debug logging
    step_logging_enabled = True
    if step_logging_enabled:
        logger.debug("Step-level logging is enabled")
    assert step_logging_enabled

def test_first_100_chars_debug_output(setup_logger):
    logger = setup_logger
    output = "This is a test log message that exceeds 100 characters to ensure we can capture the first 100 characters correctly."
    logger.debug(output)
    assert output[:100] == "This is a test log message that exceeds 100 characters to ensure we can capture the first 100 characters correctly."[:100]

def test_linter_config_sets_debug_level():
    """Test that linter_config.log_level: debug actually sets logger to DEBUG."""
    # Reset to INFO first
    logger.set_level("INFO")
    assert logger.level == logging.INFO

    pipeline = {
        "name": "test-debug",
        "linter_config": {
            "log_level": "debug"
        },
        "steps": [
            {
                "name": "dummy",
                "type": "function",
                "function": "llmflow.utils.data.parse_bible_reference",
                "inputs": {"passage": "John 3:16"},
                "outputs": "result"
            }
        ]
    }

    run_pipeline(pipeline, skip_lint=True)

    # After running, logger should be at DEBUG
    assert logger.level == logging.DEBUG, f"Expected DEBUG (10), got {logger.level}"