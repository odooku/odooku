import click
import tempfile
import sys
import os

from odooku.cli.resolve import (
    resolve_db_name,
    resolve_db_name_new,
    resolve_db_name_multiple
)


__all__ = [
    'database'
]


CHUNK_SIZE = 16 * 1024


@click.command()
@click.option(
    '--db-name',
    callback=resolve_db_name
)
@click.option(
    '--module',
    multiple=True
)
@click.option(
    '--demo-data',
    is_flag=True,
)
@click.pass_context
def preload(ctx, db_name, module, demo_data):
    config = (
        ctx.obj['config']
    )

    from odoo.modules.registry import Registry

    if module:
        modules = {
            module_name: 1
            for module_name in module
        }
        config['init'] = dict(modules)

    registry = Registry.new(db_name, force_demo=demo_data, update_module=True)


@click.command()
@click.option(
    '--db-name',
    multiple=True,
    callback=resolve_db_name_multiple
)
@click.option(
    '--module',
    multiple=True
)
@click.option(
    '--init',
    is_flag=True
)
@click.pass_context
def update(ctx, db_name, module, init):
    config = (
        ctx.obj['config']
    )

    from odoo.modules.registry import Registry
    config['init' if init else 'update'] = {
        module_name: 1
        for module_name in  module or ['all']
    }
    
    for db in db_name:
        registry = Registry.new(db, update_module=True)


@click.command()
@click.option(
    '--db-name',
    callback=resolve_db_name
)
@click.pass_context
def newdbuuid(ctx, db_name):
    config = (
        ctx.obj['config']
    )

    from odoo.modules.registry import Registry
    from odooku.api import environment

    registry = Registry(db_name)
    with registry.cursor() as cr:
        with environment(cr) as env:
            env['ir.config_parameter'].init(force=True)


@click.command()
@click.option(
    '--db-name',
    callback=resolve_db_name
)
@click.option(
    '--s3-file'
)
@click.pass_context
def dump(ctx, db_name, s3_file):
    config = (
        ctx.obj['config']
    )

    from odooku.backends import get_backend
    from odoo.api import Environment
    from odoo.service.db import dump_db

    s3_backend = get_backend('s3')

    with tempfile.TemporaryFile() as t:
        with Environment.manage():
            dump_db(db_name, t)

        t.seek(0)
        if s3_file:
            s3_backend.client.upload_fileobj(t, s3_backend.bucket, s3_file)
        else:
            # Pipe to stdout
            while True:
                chunk = t.read(CHUNK_SIZE)
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)


@click.command()
@click.option(
    '--db-name',
    callback=resolve_db_name_new
)
@click.option(
    '--copy',
    is_flag=True
)
@click.option(
    '--s3-file'
)
@click.pass_context
def restore(ctx, db_name, copy, s3_file):
    config = (
        ctx.obj['config']
    )

    if update:
        config['update']['all'] = 1

    from odooku.backends import get_backend
    from odoo.api import Environment
    from odoo.service.db import restore_db

    s3_backend = get_backend('s3')

    with tempfile.NamedTemporaryFile(delete=False) as t:
        if s3_file:
            s3_backend.client.download_fileobj(s3_backend.bucket, s3_file, t)
        else:
            # Read from stdin
            while True:
                chunk = sys.stdin.buffer.read(CHUNK_SIZE)
                if not chunk:
                    break
                t.write(chunk)
        t.close()

        with Environment.manage():
            restore_db(
                db_name,
                t.name,
                copy=copy
            )

        os.unlink(t.name)


@click.group()
@click.pass_context
def database(ctx):
    pass


database.add_command(preload)
database.add_command(update)
database.add_command(newdbuuid)
database.add_command(dump)
database.add_command(restore)
