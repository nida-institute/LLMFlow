"""
Test suite for execution output messages.

This tests that execution progress messages appear correctly.
"""

import pytest
from io import StringIO
from unittest.mock import patch, MagicMock
import tempfile
import yaml
from src.llmflow.modules.logger import Logger
from llmflow.runner import run_pipeline
import logging


class TestExecutionOutput:
    """Test output during pipeline execution"""

    def test_dry_run_shows_would_run(self, caplog):
        """Test that dry run shows 'Would run:' messages"""
        test_pipeline = {
            "name": "test_dryrun",
            "steps": [
                {"name": "step1", "type": "function", "function": "print", "inputs": {"args": ["test1"]}},
                {"name": "step2", "type": "function", "function": "print", "inputs": {"args": ["test2"]}}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_pipeline, f)
            pipeline_file = f.name

        try:
            with caplog.at_level(logging.INFO, logger='llmflow'):
                run_pipeline(pipeline_file, dry_run=True, skip_lint=True)

            # Check log messages
            log_messages = [record.message for record in caplog.records]
            log_text = "\n".join(log_messages)

            assert "Would run: step1" in log_text
            assert "Would run: step2" in log_text
            # Should not have execution messages
            assert "🚀 Executing:" not in log_text
            assert "✅ Completed:" not in log_text

        finally:
            import os
            os.unlink(pipeline_file)

    def test_execution_shows_progress_messages(self, caplog):
        """Test that real execution shows progress messages"""
        test_pipeline = {
            "name": "test_progress",
            "steps": [{
                "name": "test_step",
                "type": "function",
                "function": "tests.test_execution_output.simple_function",
                "outputs": ["result"]
            }]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_pipeline, f)
            pipeline_file = f.name

        try:
            # Mock our test function
            with patch('tests.test_execution_output.simple_function', return_value="OK"):
                with caplog.at_level(logging.INFO, logger='llmflow'):
                    run_pipeline(pipeline_file, skip_lint=True)

            # Check log messages
            log_messages = [record.message for record in caplog.records]
            log_text = "\n".join(log_messages)

            # Check for execution messages (updated to match current format)
            assert "🔧 Starting function step: test_step" in log_text
            assert "✅ Completed function step: test_step" in log_text
            assert "🎯 Starting pipeline execution..." in log_text
            assert "Pipeline complete." in log_text

        finally:
            import os
            os.unlink(pipeline_file)

    def test_no_duplicate_messages(self, caplog):
        """Test that messages don't appear twice"""
        test_pipeline = {
            "name": "test_duplicates",
            "steps": [{
                "name": "unique_step",
                "type": "function",
                "function": "tests.test_execution_output.simple_function",
                "outputs": ["result"]
            }]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_pipeline, f)
            pipeline_file = f.name

        try:
            with patch('tests.test_execution_output.simple_function', return_value="OK"):
                with caplog.at_level(logging.INFO):
                    run_pipeline(pipeline_file, skip_lint=True)

            # Get log messages
            log_messages = [record.message for record in caplog.records]
            log_text = "\n".join(log_messages)

            # Count occurrences - should be exactly 1 (updated to match current format)
            assert log_text.count("🔧 Starting function step: unique_step") == 1

        finally:
            import os
            os.unlink(pipeline_file)

    @pytest.mark.skip(reason="gpt_api functionality moved to different module")
    def test_llm_step_shows_calling_message(self):
        # This test needs to be updated to use the correct module
        pass


# Helper function for testing
def simple_function():
    """Simple function that succeeds"""
    return "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])