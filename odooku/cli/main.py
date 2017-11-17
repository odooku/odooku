import click
import importlib
import pkgutil
from urllib.parse import urlparse

from odooku.params import params
from odooku.helpers.env import prefix_envvar
from odooku.cli.resolve import resolve_addons

import logging

try:
    import ptvsd
except ImportError:
    ptvsd = None


@click.group()
@click.option(
    '--database-url',
    envvar="DATABASE_URL",
    help="[database type]://[username]:[password]@[host]:[port]/[database name]"
)
@click.option(
    '--database-maxconn',
    default=20,
    envvar=prefix_envvar("DATABASE_MAXCONN"),
    type=click.INT,
    help="Maximum number of database connections per worker."
)
@click.option(
    '--redis-url',
    envvar="REDIS_URL",
    help="redis://[password]@[host]:[port]/[database number]"
)
@click.option(
    '--redis-maxconn',
    default=20,
    envvar=prefix_envvar("REDIS_MAXCONN"),
    type=click.INT,
    help="Maximum number of redis connections per worker."
)
@click.option(
    '--aws-access-key-id',
    envvar="AWS_ACCESS_KEY_ID",
    help="Your AWS access key id."
)
@click.option(
    '--aws-secret-access-key',
    envvar="AWS_SECRET_ACCESS_KEY",
    help="Your AWS secret access key."
)
@click.option(
    '--aws-region',
    envvar="AWS_REGION",
    help="Your AWS region."
)
@click.option(
    '--s3-bucket',
    envvar="S3_BUCKET",
    help="S3 bucket for filestore."
)
@click.option(
    '--s3-endpoint-url',
    envvar="S3_ENDPOINT_URL",
    help="S3 endpoint url."
)
@click.option(
    '--s3-custom-domain',
    envvar="S3_CUSTOM_DOMAIN",
    help="S3 custom domain."
)
@click.option(
    '--s3-addressing-style',
    envvar="S3_ADDRESSING_STYLE",
    type=click.Choice(['path', 'virtual']),
    help="S3 addressing style."
)
@click.option(
    '--addons',
    callback=resolve_addons,
    envvar=prefix_envvar('ADDONS'),
    help="Addon directory path(s)."
)
@click.option(
    '--tmp-dir',
    default='/tmp/odooku',
    envvar=prefix_envvar('TMP_DIR'),
    help="Temporary directory for caching filestore."
)
@click.option(
    '--debug',
    is_flag=True,
    envvar=prefix_envvar('DEBUG')
)
@click.option(
    '--ptvsd-url',
    envvar=prefix_envvar('PTVSD_URL')
)
@click.option(
    '--statsd-host',
    envvar=prefix_envvar('STATSD_HOST')
)
@click.pass_context
def main(ctx, database_url, database_maxconn, redis_url, redis_maxconn,
        aws_access_key_id, aws_secret_access_key, aws_region, s3_bucket,
        s3_endpoint_url, s3_custom_domain, s3_addressing_style,
        addons, tmp_dir, debug, ptvsd_url, statsd_host):

    # Setup logger first, then import further modules
    import odooku.logger
    odooku.logger.setup(debug=debug, statsd_host=statsd_host)

    logger = logging.getLogger(__name__)

    from odooku.backends import register_backend
    from odooku.backends.s3 import S3Backend
    from odooku.backends.redis import RedisBackend

    # Setup S3
    if s3_bucket:
        register_backend('s3', S3Backend(
            bucket=s3_bucket,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_region=aws_region,
            endpoint_url=s3_endpoint_url,
            custom_domain=s3_custom_domain,
            addressing_style=s3_addressing_style,
        ))

    # Setup Redis
    if redis_url:
        redis_url = urlparse(redis_url)
        register_backend('redis', RedisBackend(
            host=redis_url.hostname,
            port=redis_url.port,
            password=redis_url.password,
            db_number=redis_url.path[1:] if redis_url.path else None,
            maxconn=redis_maxconn
        ))

    # Setup PTVSD
    if ptvsd_url:
        if ptvsd:
            ptvsd_url = urlparse(ptvsd_url)
            ptvsd.enable_attach(ptvsd_url.password, address = (ptvsd_url.hostname, ptvsd_url.port))
            logger.warning("PTVSD Enabled")
        else:
            logger.warning("PTVSD_URL configured but PTVSD not found.")

    # Setup Odoo
    import odoo
    from odoo.tools import config

    # Always account for multiple processes:
    # - we can run multiple dyno's consisting of:
    #    - web
    #    - worker
    odoo.multi_process = True

    # Patch odoo config
    config.parse_config()
    config['data_dir'] = tmp_dir
    config['addons_path'] = addons
    config['demo'] = {}
    config['without_demo'] = 'all'
    config['debug_mode'] = debug

    if database_url:
        database_url = urlparse(database_url)
        db_name = database_url.path[1:] if database_url.path else False
        config['db_name'] = db_name
        config['db_user'] = database_url.username
        config['db_password'] = database_url.password
        config['db_host'] = database_url.hostname
        config['db_port'] = database_url.port
        config['db_maxconn'] = database_maxconn
        config['list_db'] = not bool(db_name)
    else:
        params.no_db = True

    ctx.obj.update({
        'debug': debug,
        'config': config,
        'params': params,
        'logger': logger
    })


def entrypoint():
    import odooku_commands
    cli_commands = []
    for importer, name, ispkg in pkgutil.iter_modules(odooku_commands.__path__):
        module = importlib.import_module('%s.%s' % (odooku_commands.__name__, name))
        cli_commands += [
            getattr(module, name)
            for name in dir(module)
            if isinstance(getattr(module, name), click.BaseCommand)
        ]

    for command in cli_commands:
        main.add_command(command)

    main(obj={})


if __name__ == '__main__':
    entrypoint()
