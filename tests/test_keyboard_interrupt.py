"""
Test keyboard interrupt handling.
"""
import sys
import subprocess
import signal
import time
import pytest


def test_keyboard_interrupt_shows_helpful_message(tmp_path):
    """Test that Ctrl+C during pipeline execution shows helpful message."""
    # Create a pipeline that sleeps
    pipeline = tmp_path / "test.yaml"
    pipeline.write_text("""
name: interrupt_test
steps:
  - name: sleep_step
    type: function
    function: subprocess.run
    inputs:
      args: ["sleep", "10"]
""")

    # Start the pipeline process
    cmd = [
        sys.executable, "-m", "llmflow.cli",
        "run",
        "--pipeline", str(pipeline),
        "--skip-lint"
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(tmp_path)
    )

    # Wait for pipeline to start executing (past module loading)
    time.sleep(1.5)

    # Send keyboard interrupt
    proc.send_signal(signal.SIGINT)

    # Get output
    stdout, stderr = proc.communicate()
    output = stdout + stderr
    assert "⚠️  Execution interrupted by user (Ctrl+C)" in output
    assert "Pipeline stopped" in output

    # Should NOT see Python traceback
    assert "Traceback (most recent call last):" not in output
    assert "KeyboardInterrupt" not in output
