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


@cli.command("config")
@click.argument("key", required=False)
@click.argument("value", required=False)
def config_cmd(key, value):
    """View or set configuration values.

    \b
    Examples:
      planner config               # show all settings
      planner config hours         # show current default hours
      planner config hours 8       # set default working hours to 8
      planner config hours 7.5     # decimals are fine
    """
    from planner import config as cfg

    if key is None:
        data = cfg.load()
        click.echo(f"Research directory : {cfg.research_dir()}")
        click.echo(f"Default hours/day  : {cfg.default_hours()}")
        click.echo(f"Editor             : {cfg.editor()}")
        return

    if key in ("hours", "default_hours"):
        if value is None:
            click.echo(f"default_hours = {cfg.default_hours()}")
        else:
            try:
                h = float(value)
                if h <= 0:
                    raise ValueError
            except ValueError:
                click.echo("Error: hours must be a positive number.", err=True)
                raise SystemExit(1)
            cfg.set_value("default_hours", h)
            click.echo(f"Default hours set to {h}.")
    else:
        click.echo(f"Unknown key '{key}'. Available keys: hours", err=True)
        raise SystemExit(1)
