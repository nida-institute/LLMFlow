import click
from llmflow.runner import run_pipeline

@click.group()
def cli():
    """LLMFlow: Declarative LLM Pipelines"""
    pass

@cli.command()
@click.option('--pipeline', required=True, help="Path to pipeline YAML (e.g. pipelines/myflow.yaml)")
@click.option('--var', multiple=True, help="Pipeline variables as key=value pairs (e.g. --var passage=Psalm_23)")
@click.option('--dry-run', is_flag=True, help="Simulate execution without calling LLMs or writing output")
def run(pipeline, var, dry_run):
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
    # Parse vars into a dict
    vars_dict = dict(v.split("=", 1) for v in var)
    run_pipeline(pipeline, vars_dict, dry_run=dry_run)
