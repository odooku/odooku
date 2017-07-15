from contextlib import contextmanager

from odoo.api import Environment, Environments
from odoo import SUPERUSER_ID


class FakeLocal(object):
    environments = Environments()


@contextmanager
def environment(cr):
    old_local = Environment._local
    Environment._local = FakeLocal()

    uid = SUPERUSER_ID
    ctx = Environment(cr, uid, {})['res.users'].context_get()
    yield  Environment(cr, uid, ctx)
    Environment._local = old_local