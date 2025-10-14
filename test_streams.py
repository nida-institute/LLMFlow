#!/usr/bin/env python3
"""Check stdout vs stderr streams"""

import subprocess
import threading
import sys

def read_stream(stream, prefix):
    """Read from a stream and print with prefix"""
    for line in stream:
        print(f"{prefix}: {line.rstrip()}")
        sys.stdout.flush()

print("Starting pipeline with separate stdout/stderr capture...")

proc = subprocess.Popen(
    ['llmflow', 'run', '--pipeline', 'pipelines/storyflow-psalms.yaml', '--var', 'passage=Psalm 88'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True
)

# Create threads to read both streams
stdout_thread = threading.Thread(target=read_stream, args=(proc.stdout, "STDOUT"))
stderr_thread = threading.Thread(target=read_stream, args=(proc.stderr, "STDERR"))

stdout_thread.start()
stderr_thread.start()

# Wait for both threads
stdout_thread.join()
stderr_thread.join()

# Wait for process
proc.wait()
print(f"\nProcess exited with code: {proc.returncode}")