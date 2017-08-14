import click

from odooku.helpers.env import prefix_envvar


__all__ = [
    'cron'
]


@click.command()
@click.pass_context
@click.option(
    '--interval',
    default=10,
    envvar=prefix_envvar('CRON_INTERVAL'),
    type=click.INT,
    help="Time between cron cycles."
)
@click.option(
    '--once',
    is_flag=True,
    envvar=prefix_envvar('CRON_ONCE')
)
def cron(ctx, interval, once):
    config = (
        ctx.obj['config']
    )

    from odooku.services.cron import CronRunner

    cron_runner = CronRunner()
    if once:
        cron_runner.run_once()
    else:
        cron_runner.run_forever(interval=interval)
