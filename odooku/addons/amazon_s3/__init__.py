# -*- coding: utf-8 -*-

from . import models

from odoo import api, models, SUPERUSER_ID

import logging

_logger = logging.getLogger(__name__)


def _force_s3_storage(cr, registry):
    from odooku.backends import get_backend
    s3_backend = get_backend('s3')
    if s3_backend:
        env = api.Environment(cr, SUPERUSER_ID, {})
        IrAttachment = env['ir.attachment']
        # We need all attachments, bypass regular search
        ids = models.Model._search(IrAttachment, [])
        for attachment in IrAttachment.browse(ids):
            attachment._s3_put(attachment.store_fname, content_type=attachment.mimetype)
            attachment.write({ 's3_exists': True })
    else:
        _logger.warning("S3 is not enabled, dataloss for attachments is imminent")
