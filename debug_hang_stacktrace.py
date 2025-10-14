#!/usr/bin/env python3
"""Debug hanging with stack trace on Ctrl+C"""

import sys
import signal
import traceback
sys.path.insert(0, '.')

# Set up signal handler to print stack trace on Ctrl+C
def signal_handler(sig, frame):
    print("\n\n=== Stack trace at interruption ===", file=sys.stderr)
    traceback.print_stack(frame, file=sys.stderr)
    print("===================================\n", file=sys.stderr)
    sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)

print("Running llmflow. Press Ctrl+C when it hangs to see the stack trace.", file=sys.stderr)

# Run the CLI
from src.llmflow.cli import cli
sys.argv = ['llmflow', 'run', '--pipeline', 'pipelines/storyflow-psalms.yaml', '--var', 'passage=Psalm 88', '--verbose']

try:
    cli()
except KeyboardInterrupt:
    # This shouldn't be reached because signal handler exits
    print("\nKeyboardInterrupt caught in main", file=sys.stderr)