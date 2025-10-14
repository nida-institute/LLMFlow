#!/usr/bin/env python3
"""Trace exactly what happens in CLI mode"""

import sys
sys.path.insert(0, '.')

# Monkey-patch to trace execution
import src.llmflow.runner as runner
original_run_pipeline = runner.run_pipeline

def traced_run_pipeline(pipeline_path, inputs, dry_run=False, verbose=False, skip_lint=False):
    print(f"\n=== run_pipeline called ===", file=sys.stderr)
    print(f"  pipeline_path: {pipeline_path}", file=sys.stderr)
    print(f"  inputs: {inputs}", file=sys.stderr)
    print(f"  dry_run: {dry_run}", file=sys.stderr)
    print(f"  verbose: {verbose}", file=sys.stderr)
    print(f"  skip_lint: {skip_lint}", file=sys.stderr)
    print(f"===================\n", file=sys.stderr)

    return original_run_pipeline(pipeline_path, inputs, dry_run, verbose, skip_lint)

runner.run_pipeline = traced_run_pipeline

# Also patch the CLI command
from src.llmflow.cli import run as cli_run
original_cli_run = cli_run.callback

def traced_cli_run(pipeline, var, dry_run, verbose):
    print(f"\n=== CLI run called ===", file=sys.stderr)
    print(f"  pipeline: {pipeline}", file=sys.stderr)
    print(f"  var: {var}", file=sys.stderr)
    print(f"  dry_run: {dry_run}", file=sys.stderr)
    print(f"  verbose: {verbose}", file=sys.stderr)
    print(f"===================\n", file=sys.stderr)

    return original_cli_run(pipeline, var, dry_run, verbose)

cli_run.callback = traced_cli_run

# Now run the CLI
from src.llmflow.cli import cli
import click

if __name__ == '__main__':
    # Simulate the CLI call
    sys.argv = ['llmflow', 'run', '--pipeline', 'pipelines/storyflow-psalms.yaml', '--var', 'passage=Psalm 88', '--verbose']
    cli()