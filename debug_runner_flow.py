#!/usr/bin/env python3
"""Debug the runner flow"""

import sys
sys.path.insert(0, '.')

# Add debugging to runner
from src.llmflow import runner
import logging

# Configure logging to see everything
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s', stream=sys.stderr)

# Patch run_pipeline to add debug output
original_run_pipeline = runner.run_pipeline

def debug_run_pipeline(pipeline_path, inputs, dry_run=False, verbose=False, skip_lint=False):
    print(f"\n=== ENTERING run_pipeline ===", file=sys.stderr)
    print(f"  pipeline_path: {pipeline_path}", file=sys.stderr)
    print(f"  inputs: {inputs}", file=sys.stderr)
    print(f"  dry_run: {dry_run}", file=sys.stderr)
    print(f"  verbose: {verbose}", file=sys.stderr)
    print(f"  skip_lint: {skip_lint}", file=sys.stderr)

    try:
        result = original_run_pipeline(pipeline_path, inputs, dry_run, verbose, skip_lint)
        print(f"\n=== EXITING run_pipeline normally ===", file=sys.stderr)
        print(f"  result keys: {list(result.keys()) if result else 'None'}", file=sys.stderr)
        return result
    except Exception as e:
        print(f"\n=== EXITING run_pipeline with exception ===", file=sys.stderr)
        print(f"  exception: {type(e).__name__}: {e}", file=sys.stderr)
        raise

runner.run_pipeline = debug_run_pipeline

# Run via CLI
from src.llmflow.cli import cli
sys.argv = ['llmflow', 'run', '--pipeline', 'pipelines/storyflow-psalms.yaml', '--var', 'passage=Psalm 88', '--verbose']

try:
    cli()
except Exception as e:
    print(f"\nCLI exited with exception: {type(e).__name__}: {e}", file=sys.stderr)