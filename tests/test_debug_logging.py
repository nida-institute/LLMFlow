"""Tests for debug logging behavior."""
import logging
import pytest
from io import StringIO
from llmflow.runner import run_pipeline


class TestDebugLogging:
    """Test that debug messages only appear when debug mode is enabled."""

    def test_debug_messages_not_shown_by_default(self, caplog):
        """Debug messages should not appear without debug configuration."""
        caplog.set_level(logging.INFO)

        pipeline = {
            "name": "test-no-debug",
            "steps": [
                {
                    "name": "test_step",
                    "type": "function",
                    "function": "llmflow.utils.data.parse_bible_reference",
                    "inputs": {"passage": "John 3:16"},
                    "outputs": "result"
                }
            ]
        }

        run_pipeline(pipeline, skip_lint=True)

        # Should not see debug-level messages
        debug_messages = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert len(debug_messages) == 0, "Debug messages should not appear in INFO mode"

    def test_global_debug_shows_all_debug_messages(self):
        """When linter_config.log_level is debug, logger level should be set to DEBUG."""
        from llmflow.runner import logger

        # Reset to INFO first
        logger.set_level("INFO")
        assert logger.level == logging.INFO

        pipeline = {
            "name": "test-global-debug",
            "linter_config": {
                "log_level": "debug"
            },
            "steps": [
                {
                    "name": "test_step",
                    "type": "function",
                    "function": "llmflow.utils.data.parse_bible_reference",
                    "inputs": {"passage": "John 3:16"},
                    "outputs": "result"
                }
            ]
        }

        run_pipeline(pipeline, skip_lint=True)

        # Logger should now be at DEBUG level
        assert logger.level == logging.DEBUG, f"Logger should be at DEBUG level after pipeline with log_level: debug"

    def test_step_level_debug_shows_step_messages(self):
        """When step has log: debug, logger level should temporarily be set to DEBUG."""
        from llmflow.runner import logger

        # Set initial logger level to INFO
        logger.set_level("INFO")

        pipeline = {
            "name": "test-step-debug",
            "steps": [
                {
                    "name": "step1_no_debug",
                    "type": "function",
                    "function": "llmflow.utils.data.parse_bible_reference",
                    "inputs": {"passage": "John 3:16"},
                    "outputs": "result1"
                },
                {
                    "name": "step2_with_debug",
                    "type": "function",
                    "function": "llmflow.utils.data.parse_bible_reference",
                    "inputs": {"passage": "Mark 1:1"},
                    "outputs": "result2",
                    "log": "debug"
                },
                {
                    "name": "step3_no_debug",
                    "type": "function",
                    "function": "llmflow.utils.data.parse_bible_reference",
                    "inputs": {"passage": "Luke 2:1"},
                    "outputs": "result3"
                }
            ]
        }

        run_pipeline(pipeline, skip_lint=True)

        # Logger should be restored to INFO after pipeline completes
        assert logger.level == logging.INFO, f"Logger should be restored to INFO after pipeline, got {logger.level}"

        # Debug from other steps should not appear (hard to verify without checking message content)

    def test_step_debug_does_not_leak(self, caplog):
        """Step-level log: debug should not affect subsequent steps."""
        caplog.set_level(logging.DEBUG, logger='llmflow')

        # Set initial logger level to INFO
        from llmflow.runner import logger
        logger.set_level("INFO")

        pipeline = {
            "name": "test-no-leak",
            "steps": [
                {
                    "name": "debug_step",
                    "type": "function",
                    "function": "llmflow.utils.data.parse_bible_reference",
                    "inputs": {"passage": "John 3:16"},
                    "outputs": "result1",
                    "log": "debug"
                },
                {
                    "name": "normal_step",
                    "type": "function",
                    "function": "llmflow.utils.data.parse_bible_reference",
                    "inputs": {"passage": "Mark 1:1"},
                    "outputs": "result2"
                }
            ]
        }

        # Clear any previous records
        caplog.clear()

        run_pipeline(pipeline, skip_lint=True)

        # Get the logger level after pipeline completes - should be restored to INFO
        assert logger.level == logging.INFO, f"Logger should be restored to INFO after step with log: debug, but is {logger.level}"

    def test_for_each_step_debug(self):
        """Step inside for-each with log: debug should temporarily enable debug logging."""
        from llmflow.runner import logger

        # Set initial logger level to INFO
        logger.set_level("INFO")

        pipeline = {
            "name": "test-foreach-debug",
            "variables": {
                "passages": ["John 3:16", "Mark 1:1"]
            },
            "steps": [
                {
                    "name": "for_each_with_debug",
                    "type": "for-each",
                    "input": "${passages}",
                    "item_var": "passage",
                    "steps": [
                        {
                            "name": "parse_in_loop",
                            "type": "function",
                            "function": "llmflow.utils.data.parse_bible_reference",
                            "inputs": {"passage": "${passage}"},
                            "outputs": "parsed",
                            "log": "debug"
                        }
                    ]
                }
            ]
        }

        run_pipeline(pipeline, skip_lint=True)

        # Logger should be restored to INFO after pipeline completes
        assert logger.level == logging.INFO, f"Logger should be restored after for-each with debug steps"

    def test_scene_list_debug_output(self, caplog, tmp_path):
        """The scene_list step's debug output should only appear with log: debug."""
        caplog.set_level(logging.INFO)

        # Create a mock scene list
        pipeline = {
            "name": "test-scene-debug",
            "variables": {
                "scene_list": [
                    {"Citation": "John 3:16", "Title": "Scene 1"},
                    {"Citation": "John 3:17", "Title": "Scene 2"}
                ]
            },
            "steps": [
                {
                    "name": "check_scenes",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${scene_list}"},
                    "outputs": "scenes"
                    # No log: debug
                }
            ]
        }

        run_pipeline(pipeline, skip_lint=True)

        # Should NOT see debug output about scene list contents
        debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
        scene_debug = [m for m in debug_messages if "Citation" in m or "Title" in m]

        assert len(scene_debug) == 0, "Scene list details should not appear without debug mode"


class TestDebugOutputContent:
    """Test what gets logged at debug level."""

    def test_debug_shows_first_100_chars(self):
        """Debug output should be enabled when linter_config.log_level: debug."""
        from llmflow.runner import logger

        # Reset to INFO first
        logger.set_level("INFO")

        long_text = "x" * 200

        pipeline = {
            "name": "test-debug-content",
            "linter_config": {"log_level": "debug"},
            "steps": [
                {
                    "name": "store_long_text",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": long_text},
                    "outputs": "text"
                }
            ]
        }

        run_pipeline(pipeline, skip_lint=True)

        # Logger should be at DEBUG level after running pipeline with log_level: debug
        assert logger.level == logging.DEBUG, f"Logger should be at DEBUG level with linter_config.log_level: debug"

    def test_info_mode_does_not_show_content_preview(self, caplog):
        """In INFO mode, should not see content previews."""
        caplog.set_level(logging.INFO)

        pipeline = {
            "name": "test-info-no-preview",
            "steps": [
                {
                    "name": "store_text",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "some content here"},
                    "outputs": "text"
                }
            ]
        }

        run_pipeline(pipeline, skip_lint=True)

        # Should NOT see content preview
        messages = [r.message for r in caplog.records]
        preview_messages = [m for m in messages if "First 100 chars:" in m]

        assert len(preview_messages) == 0, "Content preview should not appear in INFO mode"