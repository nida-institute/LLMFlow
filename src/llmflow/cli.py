import click

@click.group()
def cli():
    '''LLMFlow: Declarative LLM Pipelines'''
    pass

@cli.command()
@click.argument('pipeline_file')
@click.option('--var', multiple=True)
@click.option('--dry_run', is_flag=True)
def run(pipeline_file, var, dry_run):
    '''Run a pipeline YAML file'''
    vars_dict = dict(v.split("=", 1) for v in var)
    click.echo(f"[{'DRY' if dry_run else 'LIVE'} RUN] Would run: {pipeline_file}")
    click.echo(f"Variables: {vars_dict}")

@cli.command()
def version():
    '''Show version information'''
    click.echo("LLMFlow v0.1")
