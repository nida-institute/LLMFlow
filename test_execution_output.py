#!/usr/bin/env python3
"""Test to ensure we see execution output"""

import os
import sys
sys.path.insert(0, 'src')

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

from llmflow.runner import run_pipeline

print("Starting test pipeline run...", flush=True)

try:
    result = run_pipeline(
        'pipelines/storyflow-psalms.yaml',
        vars={'passage': 'Psalm 1:1'},
        dry_run=False,
        skip_lint=True  # Skip lint to get to execution faster
    )
    print(f"\nPipeline completed successfully!", flush=True)
    print(f"Generated files should be in outputs/", flush=True)
except Exception as e:
    print(f"\nPipeline failed: {e}", flush=True)
    import traceback
    traceback.print_exc()