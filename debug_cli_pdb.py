#!/usr/bin/env python3
"""Debug the CLI command directly"""

import sys
sys.path.insert(0, '.')

# Patch the CLI run command to add breakpoint
from src.llmflow.cli import run
original_callback = run.callback

def debug_callback(pipeline, var, dry_run, verbose):
    print("\n=== CLI run command called, starting debugger ===\n", file=sys.stderr)
    import pdb
    pdb.set_trace()  # Start debugger here
    return original_callback(pipeline, var, dry_run, verbose)

run.callback = debug_callback

# Run the CLI
from src.llmflow.cli import cli
sys.argv = ['llmflow', 'run', '--pipeline', 'pipelines/storyflow-psalms.yaml', '--var', 'passage=Psalm 88', '--verbose']

cli()