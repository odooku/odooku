import sys
import os
import tempfile
import click

from odooku.cli.resolve import resolve_db_name, resolve_db_name_multiple


__all__ = [
    'trans'
]


CHUNK_SIZE = 16 * 1024


@click.command()
@click.argument('language', nargs=1)
@click.option(
    '--db-name',
    callback=resolve_db_name
)
@click.option(
    '--module',
    multiple=True
)
@click.option(
    '--fix',
    is_flag=True
)
@click.pass_context
def export(ctx, language, db_name, module, fix):
    modules = module or ['all']

    from odoo.modules.registry import Registry
    from odooku.api import environment
    from odoo.tools import trans_export

    with tempfile.TemporaryFile() as t:

        # Perform checks (and possible fixes)
        registry = Registry(db_name)
        with registry.cursor() as cr:
            with environment(cr) as env:
                lang = env['res.lang'].with_context(dict(active_test=False)).search([('code', '=', language)])
                if not lang:
                    raise ValueError("Language %s does not exist" % language)
                if not lang[0].active:
                    if not fix:
                        raise ValueError("Language %s is not activated" % language)
                    else:
                        installed = env['ir.module.module'].search([('state', '=', 'installed')])
                        installed._update_translations(language)

                if module:
                    installed = env['ir.module.module'].search([('name', 'in', module), ('state', '=', 'installed')])
                    missing = set(module) - set([mod.name for mod in installed])
                    if missing:
                        if not fix:
                            raise ValueError("Modules '%s' are not installed" % ", ".join(missing))
                        else:
                            ctx.obj['config']['init'] = {
                                module_name: 1
                                for module_name in module
                            }
                        
        # Export
        registry = Registry.new(db_name, update_module=fix)
        with registry.cursor() as cr:
            with environment(cr) as env:
                trans_export(language, modules, t, 'po', cr)
                
        t.seek(0)
        # Pipe to stdout
        while True:
            chunk = t.read(CHUNK_SIZE)
            if not chunk:
                break
            sys.stdout.buffer.write(chunk)


@click.command('import')
@click.argument('language', nargs=1)
@click.option(
    '--db-name',
    callback=resolve_db_name
)
@click.option(
    '--overwrite',
    is_flag=True
)
@click.pass_context
def import_(ctx, language, db_name, overwrite):
    context = {
        'overwrite': overwrite
    }

    from odoo.modules.registry import Registry
    from odooku.api import environment
    from odoo.tools import trans_load

    with tempfile.NamedTemporaryFile(suffix='.po', delete=False) as t:
        registry = Registry(db_name)

        # Read from stdin
        while True:
            chunk = sys.stdin.buffer.read(CHUNK_SIZE)
            if not chunk:
                break
            t.write(chunk)
        t.close()

        with registry.cursor() as cr:
            with environment(cr) as env:
                trans_load(cr, t.name, language, context=context)

        os.unlink(t.name)


@click.command('update')
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
    '--language',
    multiple=True
)
@click.option(
    '--overwrite',
    is_flag=True
)
@click.pass_context
def update(ctx, db_name, module, language, overwrite):
    context = {
        'overwrite': overwrite
    }

    from odoo.modules.registry import Registry
    from odooku.api import environment

    domain = [('state', '=', 'installed')]
    if module:
        domain = [('name', 'in', module)]


    for db in db_name:
        registry = Registry(db)
        with registry.cursor() as cr:
            with environment(cr) as env:
                mods = env['ir.module.module'].search(domain)
                mods.with_context(overwrite=overwrite)._update_translations(language)


@click.group()
@click.pass_context
def trans(ctx):
    pass


trans.add_command(export)
trans.add_command(import_)
trans.add_command(update)
