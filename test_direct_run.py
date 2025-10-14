#!/usr/bin/env python3
"""Run the pipeline directly in Python to debug"""

import sys
sys.path.insert(0, '.')

# Redirect all output to ensure we see it
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s', stream=sys.stderr)

print("Starting direct run test...", file=sys.stderr)

from src.llmflow.runner import run_pipeline

try:
    print("\nAbout to call run_pipeline...", file=sys.stderr)
    result = run_pipeline(
        'pipelines/storyflow-psalms.yaml',
        {'passage': 'Psalm 88'},
        dry_run=False,
        verbose=True
    )
    print(f"\nPipeline completed! Keys: {list(result.keys())}", file=sys.stderr)
except Exception as e:
    print(f"\nError: {type(e).__name__}: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()