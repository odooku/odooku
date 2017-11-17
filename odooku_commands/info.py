import click


__all__ = [
    'info'
]


INFO_MESSAGE = """
Odooku
--------------------------------------
  available modules: {num_modules}
"""


@click.command()
@click.pass_context
def info(ctx):
    logger = (
        ctx.obj['logger']
    )

    from odoo.modules import get_modules
    print(INFO_MESSAGE.format(
        num_modules=len(get_modules())
    ))
