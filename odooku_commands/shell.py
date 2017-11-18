import click
import bpython

from odooku.cli.resolve import resolve_db_name


__all__ = [
    'shell'
]


@click.command()
@click.argument('input_file', type=click.Path(exists=True), required=False)
@click.option(
    '--db-name',
    callback=resolve_db_name
)
@click.pass_context
def shell(ctx, input_file, db_name):
    from odoo.modules.registry import Registry
    from odooku.api import environment
    registry = Registry(db_name)

    with registry.cursor() as cr:
        with environment(cr) as env:
            context = {
                'env': env,
                'self': env.user
            }

            args = []
            if input_file is not None:
                args = [input_file]

            bpython.embed(context, args=args, banner='Odooku shell')
