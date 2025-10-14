#!/usr/bin/env python3
"""Debug where the pipeline is hanging when run from CLI"""

import sys
import subprocess
import threading
import time

def run_with_timeout():
    """Run the pipeline and see where it hangs"""
    print("Starting llmflow command...")

    # Start the process
    proc = subprocess.Popen(
        ['llmflow', 'run', '--pipeline', 'pipelines/storyflow-psalms.yaml', '--var', 'passage=Psalm 88'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

    # Read output line by line
    last_line = ""
    for line in proc.stdout:
        print(f"OUTPUT: {line.rstrip()}")
        last_line = line.rstrip()

        # If we see validation completed, wait a bit then check what happens
        if "Pipeline validation completed successfully" in line:
            print("\n>>> VALIDATION COMPLETED - Waiting to see what happens next...")
            time.sleep(2)

    # Wait for process to complete
    proc.wait()
    print(f"\nProcess exited with code: {proc.returncode}")
    print(f"Last line was: {last_line}")

if __name__ == "__main__":
    run_with_timeout()