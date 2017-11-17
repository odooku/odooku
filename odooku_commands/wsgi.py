import os
import click

import gevent

from werkzeug._reloader import run_with_reloader

from odooku.helpers.env import prefix_envvar
from odooku.cli.resolve import resolve_comma_seperated

try:
    from newrelic import agent as newrelic_agent
except ImportError:
    newrelic_agent = None


__all__ = [
    'wsgi'
]


@click.command()
@click.argument('port', nargs=1, type=int)
@click.option(
    '--timeout',
    default=25,
    envvar=prefix_envvar('TIMEOUT'),
    type=click.INT,
    help="Longpolling timeout"
)
@click.option(
    '--cdn',
    is_flag=True,
    envvar=prefix_envvar('CDN'),
    help="Enables Content Delivery through S3 endpoint or S3 custom domain."
)
@click.option(
    '--proxy-mode',
    is_flag=True,
    envvar=prefix_envvar('PROXY_MODE')
)
@click.option(
    '--admin-password',
    envvar=prefix_envvar('ADMIN_PASSWORD'),
    help="Odoo admin password."
)
@click.option(
    '--db-filter',
    default='.*',
    envvar=prefix_envvar('DB_FILTER')
)
@click.option(
    '--ws',
    is_flag=True,
    envvar=prefix_envvar('WS')
)
@click.option(
    '--cron',
    is_flag=True,
    envvar=prefix_envvar('CRON')
)
@click.option(
    '--cron-interval',
    default=30,
    envvar=prefix_envvar('CRON_INTERVAL'),
    type=click.INT,
    help="Time between cron cycles."
)
@click.option(
    '--server-wide-modules',
    default='web',
    callback=resolve_comma_seperated,
    envvar=prefix_envvar('SERVER_MODULES'),
    help="Server-wide modules to load."
)
@click.option(
    '--dev',
    is_flag=True,
    envvar=prefix_envvar('DEV')
)
@click.pass_context
def wsgi(ctx, port, timeout, cdn, proxy_mode, admin_password,
        db_filter, ws, cron, cron_interval, server_wide_modules, dev):

    debug, config, params, logger = (
        ctx.obj['debug'],
        ctx.obj['config'],
        ctx.obj['params'],
        ctx.obj['logger']
    )

    # Patch odoo config, since we run with gevent
    # we do not need multiple workers, but Odoo needs
    # to be fooled.
    config['workers'] = 2
    config['dev_mode'] = ['all']
    config['admin_passwd'] = admin_password
    config['dbfilter'] = db_filter
    config['server_wide_modules'] = ','.join(server_wide_modules)
    # Odoo still uses a deprecated conf module for server_wide_modules
    import odoo.conf
    odoo.conf.server_wide_modules = server_wide_modules

    if ws:
        from odooku.services.websocket import WebSocketServer as Server
    else:
        from odooku.services.wsgi import WSGIServer as Server
    from odooku.services.wsgi import WSGIApplicationRulesWrapper
    from odooku.services.cron import CronRunner

    # Initialize newrelic_agent
    global newrelic_agent
    if newrelic_agent and any(key in os.environ for key in [
                'NEW_RELIC_LICENSE_KEY',
                'NEW_RELIC_CONFIG_FILE'
            ]):

        newrelic_agent.initialize()
    else:
        newrelic_agent = None

    # Keep track of custom config params
    params.TIMEOUT = timeout
    params.CDN_ENABLED = cdn
    params.WS_ENABLED = ws

    # Load wsgi rules
    rules = WSGIApplicationRulesWrapper.load()

    def serve():
        max_accept = config['db_maxconn']
        if cron:
            cron_runner = CronRunner()
            max_accept -= 1
            gevent.spawn(cron_runner.run_forever, interval=cron_interval)

        server = Server(
            port,
            max_accept=max_accept,
            proxy_mode=proxy_mode,
            rules=rules,
            newrelic_agent=newrelic_agent,
            timeout=timeout
        )

        server.serve_forever()

    if dev:
        logger.warning("Running in development mode")
        run_with_reloader(serve)
    else:
        serve()
