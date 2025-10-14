#!/usr/bin/env python3
"""Test if linter exits the process"""

import sys
sys.path.insert(0, '.')

# Monkey-patch sys.exit to trace
original_exit = sys.exit
def traced_exit(code=0):
    print(f"\n=== sys.exit({code}) called ===", file=sys.stderr)
    import traceback
    traceback.print_stack(file=sys.stderr)
    print("===========================\n", file=sys.stderr)
    original_exit(code)

sys.exit = traced_exit

# Also trace SystemExit
original_systemexit = SystemExit
class TracedSystemExit(original_systemexit):
    def __init__(self, *args, **kwargs):
        print(f"\n=== SystemExit raised ===", file=sys.stderr)
        import traceback
        traceback.print_stack(file=sys.stderr)
        print("========================\n", file=sys.stderr)
        super().__init__(*args, **kwargs)

import builtins
builtins.SystemExit = TracedSystemExit

# Now run the linter
from src.llmflow.utils.linter import lint_pipeline_full

try:
    print("Starting lint...", file=sys.stderr)
    lint_pipeline_full('pipelines/storyflow-psalms.yaml')
    print("Lint completed successfully!", file=sys.stderr)
except SystemExit as e:
    print(f"Caught SystemExit: {e}", file=sys.stderr)
    # Don't re-raise
except Exception as e:
    print(f"Caught exception: {type(e).__name__}: {e}", file=sys.stderr)