import click
import os.path
import odooku

from odooku.params import params


DEFAULT_ADDONS = [
    os.path.join(os.path.dirname(odooku.__file__), 'addons')
]

def resolve_addons(ctx, param, value):
    addons = value.split(',')
    addons = list(set(addons) | set(DEFAULT_ADDONS) | set(params.addon_paths))
    return ','.join(addons)


def resolve_db_name(ctx, param, value):
    from odoo.service.db import list_dbs

    config = (
        ctx.obj['config']
    )

    dbs = config['db_name'].split(',') if config['db_name'] else None
    if dbs is None:
        dbs = list_dbs(True)

    if value:
        if dbs is not None and value not in dbs:
            raise click.BadParameter(
                "No such db '%s'." % value
            )
        return value
    elif dbs is not None and len(dbs) == 1:
        # Running in single db mode, safe to assume the db.
        return dbs[0]

    raise click.BadParameter(
        "no db name given."
    )

def resolve_db_name_multiple(ctx, param, value):
    from odoo.service.db import list_dbs

    config = (
        ctx.obj['config']
    )

    dbs = config['db_name'].split(',') if config['db_name'] else None
    if dbs is None:
        dbs = list_dbs(True)

    if value:
        invalid = [db for db in value if db not in dbs]
        if invalid:
            raise click.BadParameter(
                "No such db '%s'." % invalid[0]
            )

        return value

    return dbs
