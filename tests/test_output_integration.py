"""
Integration tests for output functionality.

These tests run llmflow as a subprocess to test actual output behavior.
"""

import pytest
import subprocess
import tempfile
import yaml
import sys
import os


class TestOutputIntegration:
    """Test that output routing works correctly in integration"""

    def test_execution_shows_progress_messages(self):
        """Test that execution shows progress messages in stderr"""
        test_pipeline = {
            "name": "test_progress",
            "steps": [{
                "name": "test_step",
                "type": "function",
                "function": "tests.test_output_integration.simple_test_func",
                "outputs": ["result"]
            }]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_pipeline, f)
            pipeline_file = f.name

        try:
            # Run llmflow and capture output
            result = subprocess.run(
                ["llmflow", "run", "--pipeline", pipeline_file],
                capture_output=True,
                text=True
            )

            # Progress messages should be in stderr (updated to match current format)
            assert "🔧 Starting function step: test_step" in result.stderr
            assert "✅ Completed: test_step" in result.stderr
            assert "🎯 Starting pipeline execution" in result.stderr

        finally:
            os.unlink(pipeline_file)

    def test_verbose_flag_shows_debug_output(self):
        """Test that --verbose shows debug messages"""
        test_pipeline = {
            "name": "test_verbose",
            "vars": {"test": "value"},
            "steps": [{
                "name": "step1",
                "type": "function",
                "function": "builtins.print",
                "inputs": {"args": ["{{test}}"]}
            }]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_pipeline, f)
            pipeline_file = f.name

        try:
            # Run without verbose
            result = subprocess.run(
                ["llmflow", "run", "--pipeline", pipeline_file],
                capture_output=True,
                text=True
            )
            assert "DEBUG" not in result.stderr

            # Run with verbose
            result = subprocess.run(
                ["llmflow", "run", "--pipeline", pipeline_file, "--verbose"],
                capture_output=True,
                text=True
            )
            # Should see DEBUG messages
            assert "DEBUG" in result.stderr or "Variables:" in result.stderr

        finally:
            os.unlink(pipeline_file)

    def test_dry_run_shows_would_run_messages(self):
        """Test that dry run shows 'Would run:' messages"""
        test_pipeline = {
            "name": "test_dry",
            "steps": [
                {"name": "step1", "type": "function", "function": "builtins.print", "inputs": {"args": ["test1"]}},
                {"name": "step2", "type": "function", "function": "builtins.print", "inputs": {"args": ["test2"]}}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_pipeline, f)
            pipeline_file = f.name

        try:
            result = subprocess.run(
                ["llmflow", "run", "--pipeline", pipeline_file, "--dry-run"],
                capture_output=True,
                text=True
            )

            # Should show would run messages
            assert "Would run: step1" in result.stderr
            assert "Would run: step2" in result.stderr
            # Should NOT show execution messages
            assert "🚀 Executing:" not in result.stderr

        finally:
            os.unlink(pipeline_file)

    def test_no_duplicate_messages(self):
        """Test that messages don't appear multiple times"""
        test_pipeline = {
            "name": "test_dup",
            "steps": [{
                "name": "unique",
                "type": "function",
                "function": "builtins.print",
                "inputs": {"args": ["test"]}
            }]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_pipeline, f)
            pipeline_file = f.name

        try:
            result = subprocess.run(
                ["llmflow", "run", "--pipeline", pipeline_file],
                capture_output=True,
                text=True
            )

            # Count occurrences - should be exactly 1 each (updated to match current format)
            assert result.stderr.count("🔧 Starting function step: unique") == 1

        finally:
            os.unlink(pipeline_file)


def simple_test_func():
    """Simple function for testing"""
    return "OK"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])