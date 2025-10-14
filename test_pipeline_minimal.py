#!/usr/bin/env python3
"""Minimal test to debug the pipeline hang issue"""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Enable ALL debug logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

# Import and run
from llmflow.runner import run_pipeline

print("Running minimal pipeline test...")

try:
    # Run with minimal passage
    result = run_pipeline(
        'pipelines/storyflow-psalms.yaml',
        vars={'passage': 'Psalm 1:1'},
        dry_run=False,
        skip_lint=False
    )
    print(f"Pipeline completed successfully!")
    print(f"Result keys: {list(result.keys())}")
except Exception as e:
    print(f"Pipeline failed with error: {e}")
    import traceback
    traceback.print_exc()