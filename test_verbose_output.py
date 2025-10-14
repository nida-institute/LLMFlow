#!/usr/bin/env python3
"""Test verbose output functionality"""

import os
import sys
sys.path.insert(0, 'src')

from llmflow.runner import run_pipeline

print("Testing with verbose=False (default):", flush=True)
print("-" * 50, flush=True)
try:
    result = run_pipeline(
        'pipelines/storyflow-psalms.yaml',
        vars={'passage': 'Psalm 1:1'},
        dry_run=True,
        skip_lint=True,
        verbose=False
    )
except Exception as e:
    print(f"Error: {e}")

print("\n\nTesting with verbose=True:", flush=True)
print("-" * 50, flush=True)
try:
    result = run_pipeline(
        'pipelines/storyflow-psalms.yaml',
        vars={'passage': 'Psalm 1:1'},
        dry_run=True,
        skip_lint=True,
        verbose=True
    )
except Exception as e:
    print(f"Error: {e}")