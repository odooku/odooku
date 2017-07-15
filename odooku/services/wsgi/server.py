from gevent.wsgi import WSGIServer as BaseWSGIServer
from werkzeug.debug import DebuggedApplication
from werkzeug.contrib.fixers import ProxyFix

import odoo.http
from odoo import conf
from odoo.service.wsgi_server import application_unproxied as odoo_application
from odoo.tools import config
from odoo.modules.module import load_openerp_module

import logging
import greenlet
import gevent


_logger = logging.getLogger(__name__)


class WSGIServer(BaseWSGIServer):

    def __init__(self, port, interface='0.0.0.0', max_accept=None,
            timeout=25, proxy_mode=False, rules=None, newrelic_agent=None,
            **kwargs):

        self.max_accept = max_accept or config['db_maxconn']
        self.timeout = timeout
        super(WSGIServer, self).__init__((interface, port), self.load(
            proxy_mode=proxy_mode,
            rules=rules,
            newrelic_agent=newrelic_agent
        ), log=_logger, **kwargs)


    def load_server_wide_modules(self):
        for module in conf.server_wide_modules:
            load_openerp_module(module)


    def load(self, proxy_mode=False, rules=None, newrelic_agent=None):
        _logger.info("Loading Odoo WSGI application")
        self.load_server_wide_modules()

        application = odoo_application

        if config['debug_mode']:
            application = DebuggedApplication(application, evalex=True)
            _logger.warning("Debugger enabled, do not use in production")

        if newrelic_agent:
            application = newrelic_agent.WSGIApplicationWrapper(application)
            _logger.info("New Relic enabled")

        if rules and rules.has_rules():
            application = rules(application)
            _logger.info("Rewrites enabled")

        if proxy_mode:
            application = ProxyFix(application)
            _logger.info("Proxy mode enabled")

        return application
