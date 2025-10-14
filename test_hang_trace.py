#!/usr/bin/env python3
"""Run pipeline with ability to get stack trace when it hangs"""

import sys
import os
import signal
import time
import subprocess

# First, get the process ID when we start
print("Starting pipeline in subprocess...")

# Start the command
proc = subprocess.Popen(
    ['llmflow', 'run', '--pipeline', 'pipelines/storyflow-psalms.yaml', '--var', 'passage=Psalm 88'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True
)

print(f"Started process with PID: {proc.pid}")
print("Output:")
print("-" * 50)

# Read output until we see validation complete
found_validation = False
while True:
    line = proc.stdout.readline()
    if not line:
        break
    print(line.rstrip())
    if "Pipeline validation completed successfully" in line:
        found_validation = True
        print("\n>>> Validation completed. Waiting 3 seconds to see if execution starts...")
        time.sleep(3)

        # Check if process is still running
        if proc.poll() is None:
            print(f"\n>>> Process {proc.pid} is still running. Sending SIGUSR1 to get stack trace...")
            # Try to get a stack trace
            try:
                os.kill(proc.pid, signal.SIGUSR1)
                time.sleep(1)
            except:
                pass

            print("\n>>> Terminating process...")
            proc.terminate()
            proc.wait()
            print(f">>> Process terminated with code: {proc.returncode}")
        break

if not found_validation:
    print("\n>>> Never saw validation complete message")
    proc.terminate()

print("\n>>> Done")