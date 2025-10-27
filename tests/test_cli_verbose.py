import os
import tempfile

import yaml
from click.testing import CliRunner

from llmflow.cli import cli


def test_verbose_flag_dry_run():
    """Test that --verbose and --dry-run flags work together"""
    runner = CliRunner()
    test_pipeline = {
        "name": "test_verbose",
        "vars": {"test": "value"},
        "steps": [
            {"name": "step1", "type": "function", "function": "llmflow.utils.data.identity"}
        ],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(test_pipeline, f)
        pipeline_file = f.name
    try:
        result = runner.invoke(
            cli,
            ["run", "--pipeline", pipeline_file, "--var", "test=123", "--dry-run"],
            standalone_mode=False,
        )
        # Check that the command succeeded
        assert result.exit_code == 0
    finally:
        os.remove(pipeline_file)


def test_verbose_short_flag():
    """Test that -v short flag is accepted"""
    runner = CliRunner()
    test_pipeline = {"name": "test_verbose", "vars": {"test": "value"}, "steps": []}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(test_pipeline, f)
        pipeline_file = f.name
    try:
        result = runner.invoke(
            cli,
            ["run", "--pipeline", pipeline_file, "-v", "--dry-run"],
            standalone_mode=False,
        )
        # Check that the command succeeded with verbose flag
        assert result.exit_code == 0
    finally:
        os.remove(pipeline_file)
