import click

from llmflow.runner import run_pipeline


@click.group()
def cli():
    """LLMFlow: Declarative LLM Pipelines"""
    pass


@cli.command()
@click.option(
    "--pipeline",
    required=True,
    help="Path to pipeline YAML (e.g. pipelines/myflow.yaml)",
)
@click.option(
    "--var",
    multiple=True,
    help="Pipeline variables as key=value pairs (e.g. --var passage=Psalm_23)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Simulate execution without calling LLMs or writing output",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show debug output on screen (in addition to log file)",
)
def run(pipeline, var, dry_run, verbose):
    """
    Run a pipeline YAML file.

    Examples:

      # Run a pipeline with no variables
      llmflow run --pipeline pipelines/storyflow-psalms.yaml

      # Run with multiple variables
      llmflow run --pipeline pipelines/storyflow-psalms.yaml --var passage=Psalm_23 --var exegetical_culture=western

      # Dry run to preview steps
      llmflow run --pipeline pipelines/storyflow-psalms.yaml --dry-run
    """
    # Prominent startup banner to confirm which codebase is running
    try:
        import inspect
        import os
        import sys

        import llmflow.runner as runner_mod

        runner_path = (
            os.path.abspath(inspect.getsourcefile(runner_mod))
            if hasattr(inspect, "getsourcefile")
            else str(runner_mod)
        )
        click.secho("\n=== LLMFlow (LOCAL) START ===", fg="cyan", bold=True, err=True)
        click.secho(f"Runner module: {runner_path}", fg="cyan", err=True)
        click.secho(f"CWD: {os.getcwd()}", fg="cyan", err=True)
        click.secho(f"Python: {sys.executable}", fg="cyan", err=True)
        click.secho("============================\n", fg="cyan", bold=True, err=True)
    except Exception:
        # Non-fatal if introspection fails
        pass

    # Parse vars into a dict
    vars_dict = dict(v.split("=", 1) for v in var)
    run_pipeline(pipeline, vars_dict, dry_run=dry_run, verbose=verbose)
