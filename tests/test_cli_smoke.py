import os
import sys
import subprocess
import tempfile

import yaml

def test_cli_version_flag():
    """llmflow --version should exit 0 and print version (used by binary smoke tests)."""
    cmd = [sys.executable, "-m", "llmflow.cli", "--version"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0
    assert "llmflow" in (r.stdout + r.stderr)


def test_cli_lint_valid(tmp_path):
    p = tmp_path / "pipe.yaml"
    p.write_text("""
name: test
variables:
  passage: Psalm 23
steps: []
""", encoding="utf-8")
    cmd = [sys.executable, "-m", "llmflow.cli", "lint", "--pipeline", str(p)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0
    assert "✅ Pipeline OK" in r.stdout

def test_cli_lint_invalid(tmp_path):
    p = tmp_path / "pipe_bad.yaml"
    p.write_text("""
name: bad
steps:
  - name: s1
    type: llm
    prompt:
      file: missing.gpt
      inputs: {}
    outputs: content
""", encoding="utf-8")
    cmd = [sys.executable, "-m", "llmflow.cli", "lint", "--pipeline", str(p)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 1

def test_cli_lint_json(tmp_path):
    p = tmp_path / "pipe.yaml"
    p.write_text("""
name: test
steps: []
""", encoding="utf-8")
    cmd = [sys.executable, "-m", "llmflow.cli", "lint", "--pipeline", str(p), "--json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0
    assert '"valid": true' in r.stdout

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
        cmd = [sys.executable, "-m", "llmflow.cli", "run", "--pipeline", pipeline_file, "--var", "test=123", "--dry-run", "-v"]
        result = subprocess.run(cmd, capture_output=True, text=True)
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
        cmd = [sys.executable, "-m", "llmflow.cli", "run", "--pipeline", pipeline_file, "-v", "--dry-run"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0
    finally:
        os.remove(pipeline_file)