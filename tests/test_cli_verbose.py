import os
import sys
import subprocess
import tempfile

import yaml


def test_verbose_flag_dry_run():
    """Test that --verbose and --dry-run flags work together"""
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
        cmd = [
            sys.executable,
            "-m",
            "llmflow.cli",
            "run",
            "--pipeline",
            pipeline_file,
            "--var",
            "test=123",
            "--dry-run",
            "-v",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        # Check that the command succeeded
        assert result.returncode == 0
    finally:
        os.remove(pipeline_file)


def test_verbose_short_flag():
    """Test that -v short flag is accepted"""
    test_pipeline = {"name": "test_verbose", "vars": {"test": "value"}, "steps": []}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(test_pipeline, f)
        pipeline_file = f.name
    try:
        cmd = [
            sys.executable,
            "-m",
            "llmflow.cli",
            "run",
            "--pipeline",
            pipeline_file,
            "-v",
            "--dry-run",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        # Check that the command succeeded with verbose flag
        assert result.returncode == 0
    finally:
        os.remove(pipeline_file)
