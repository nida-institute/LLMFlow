import subprocess
import sys
from pathlib import Path

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
    assert "❌ Pipeline has errors" in r.stdout

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