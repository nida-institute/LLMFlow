#!/usr/bin/env python3
"""Debug the hanging issue with pdb"""

import sys
sys.path.insert(0, '.')

# Set breakpoint in run_pipeline
import pdb
from src.llmflow import runner

# Monkey-patch to add breakpoint
original_run_pipeline = runner.run_pipeline

def debug_run_pipeline(pipeline_path, inputs, dry_run=False, verbose=False, skip_lint=False):
    print("\n=== Entering run_pipeline, starting debugger ===\n", file=sys.stderr)
    pdb.set_trace()  # Start debugger here
    return original_run_pipeline(pipeline_path, inputs, dry_run, verbose, skip_lint)

runner.run_pipeline = debug_run_pipeline

# Run the CLI
from src.llmflow.cli import cli
sys.argv = ['llmflow', 'run', '--pipeline', 'pipelines/storyflow-psalms.yaml', '--var', 'passage=Psalm 88', '--verbose']

cli()