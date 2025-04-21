
import click
from llmflow.runner import run_pipeline

@click.group()
def cli():
    '''LLMFlow: Declarative LLM Pipelines'''
    pass

@cli.command()
@click.option('--pipeline', default="pipelines/storyflow_psalms.yaml", help='Path to pipeline YAML')
@click.option('--var', multiple=True, help='key=value pipeline variables')
@click.option('--dry_run', is_flag=True)
def run(pipeline, var, dry_run):
    '''Run a pipeline YAML file'''
    vars_dict = dict(v.split("=", 1) for v in var)
    run_pipeline(pipeline, vars_dict, dry_run)

@cli.command()
def version():
    '''Show version information'''
    click.echo("LLMFlow v0.1")
