from odoo import models, api
from odooku.params import params

def get_ws_enabled():
    return 'true' if getattr(params, 'WS_ENABLED', False) else 'false';

class IrQWeb(models.AbstractModel):

    _inherit = 'ir.qweb'

    def default_values(self):
        default = super(IrQWeb, self).default_values()
        default.update(get_ws_enabled=get_ws_enabled)
        return default
