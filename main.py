import click
from pathlib import Path


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """AI Research Planner — manage projects, tasks, literature, and daily plans."""
    if ctx.invoked_subcommand is None:
        from planner.app import PlannerApp
        app = PlannerApp()
        app.run()


@cli.command()
@click.argument("research_dir", required=False)
def init(research_dir):
    """Initialize or reconfigure the planner (sets research directory)."""
    from planner import config
    default = config._DEFAULT_RESEARCH_DIR
    if research_dir:
        path = Path(research_dir).expanduser()
    else:
        raw = click.prompt("Research directory", default=str(default))
        path = Path(raw).expanduser()
    config.initialize(path)
    click.echo(f"Initialized. Research directory: {path}")


if __name__ == "__main__":
    cli()
