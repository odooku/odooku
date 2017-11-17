import gevent

from odoo.service.db import list_dbs
from odoo.sql_db import close_db
from odoo.modules.registry import Registry

import logging

_logger = logging.getLogger(__name__)


class CronRunner(object):

    def _acquire_job(self, db_name, cleanup=False):
        import odoo.addons.base as base
        acquired = base.ir.ir_cron.ir_cron._acquire_job(db_name)
        if cleanup:
            Registry.delete(db_name)
            close_db(db_name)
        return acquired

    def _run_next(self):
        db_names = list_dbs(True)
        if len(db_names):
            db_name = db_names[self.db_index]
            self._acquire_job(db_name)
            self.db_index = (self.db_index + 1) % len(db_names)
        else:
            self.db_index = 0

    def run_forever(self, interval=30, number=0):
        self.db_index = 0
        while True:
            self._run_next()
            gevent.sleep(interval + number)

    def run_once(self):
        for db_name in list_dbs(True):
            self._acquire_job(db_name, cleanup=True)
