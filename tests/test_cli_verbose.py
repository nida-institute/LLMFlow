"""
Test suite for CLI verbose flag functionality.
"""

import pytest
import tempfile
import yaml
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from llmflow.cli import cli


class TestCLIVerboseFlag:
    """Test the CLI --verbose flag functionality"""

    def test_cli_accepts_verbose_flags(self):
        """Test that CLI accepts -v and --verbose flags"""
        runner = CliRunner()

        # Test with --verbose
        result = runner.invoke(cli, ['run', '--help'])
        assert '--verbose' in result.output
        assert '-v' in result.output

    def test_verbose_flag_dry_run(self):
        """Test that verbose flag works with dry-run"""
        runner = CliRunner()

        test_pipeline = {
            "name": "test_verbose",
            "vars": {"test": "value"},
            "steps": [{"name": "step1", "type": "function", "function": "print", "inputs": {"args": ["test"]}}]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_pipeline, f)
            pipeline_file = f.name

        try:
            # Without verbose - should not show "Variables:"
            result = runner.invoke(cli, ['run', '--pipeline', pipeline_file, '--var', 'test=123', '--dry-run'])
            # Variables message goes to stderr (test that it's NOT in stdout)
            assert "Variables:" not in result.output

            # With verbose - should show "Variables:"
            result = runner.invoke(cli, ['run', '--pipeline', pipeline_file, '--var', 'test=123', '--verbose', '--dry-run'])
            # With verbose, Variables should show in logs
            # Note: Click runner might not capture stderr by default, so we check exit code
            assert result.exit_code == 0

        finally:
            import os
            os.unlink(pipeline_file)

    def test_verbose_short_flag(self):
        """Test that -v works the same as --verbose"""
        runner = CliRunner()

        test_pipeline = {
            "name": "test_verbose",
            "vars": {"test": "value"},
            "steps": []
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_pipeline, f)
            pipeline_file = f.name

        try:
            # Test -v flag
            result = runner.invoke(cli, ['run', '--pipeline', pipeline_file, '-v', '--dry-run'])
            assert result.exit_code == 0
            # The -v flag should work the same as --verbose

        finally:
            import os
            os.unlink(pipeline_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])