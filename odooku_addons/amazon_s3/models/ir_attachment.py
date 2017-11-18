import os
import logging
import base64

from odoo import api, fields, models, tools, _

from botocore.exceptions import ClientError

from odooku.backends import get_backend


_logger = logging.getLogger(__name__)


s3_backend = get_backend('s3')



class S3Error(Exception):
    pass


class S3NoSuchKey(S3Error):
    pass


class IrAttachment(models.Model):

    _inherit = 'ir.attachment'

    s3_exists = fields.Boolean(string='Exists in S3 bucket', default=None)

    @api.depends('store_fname', 'db_datas')
    def _compute_datas(self):
        bin_size = self._context.get('bin_size')
        for attach in self:
            if attach.store_fname:
                no_data = True
                try:
                    attach.datas = self._file_read(attach.store_fname, bin_size, attach.s3_exists)
                    no_data = False
                except S3NoSuchKey:
                    # SUPERUSER_ID as probably don't have write access, trigger during create
                    _logger.warning("Preventing further s3 (%s) lookups for '%s'", s3_backend.bucket, attach.store_fname)
                    super(IrAttachment, attach.sudo()).write({ 's3_exists': False })
                except S3Error:
                    pass

                if no_data:
                    _logger.warning("Failed to read attachment %s/%s: %s", attach.id, attach.name, attach.datas_fname)

            else:
                attach.datas = attach.db_datas

    def _inverse_datas(self):
        location = self._storage()
        for attach in self:
            # compute the fields that depend on datas
            value = attach.datas
            bin_data = base64.b64decode(value) if value else b''
            vals = {
                'file_size': len(bin_data),
                'checksum': self._compute_checksum(bin_data),
                'index_content': self._index(bin_data, attach.datas_fname, attach.mimetype),
                'store_fname': False,
                'db_datas': value,
            }
            if value and location != 'db':
                # save it to the filestore
                vals['store_fname'] = self._file_write(value, vals['checksum'])
                vals['db_datas'] = False

                if s3_backend:
                    s3_exists = True
                    try:
                        self._s3_put(vals['store_fname'], content_type=attach.mimetype)
                    except S3Error:
                        s3_exists = False
                    vals.update({ 's3_exists': s3_exists })
                else:
                    _logger.warning("S3 is not enabled, dataloss for attachment [%s] is imminent", attach.id)

            # take current location in filestore to possibly garbage-collect it
            fname = attach.store_fname
            # write as superuser, as user probably does not have write access
            super(IrAttachment, attach.sudo()).write(vals)
            if fname:
                self._file_delete(fname)

    @api.model
    def _file_read(self, fname, bin_size=False, s3_exists=None):
        full_path = self._full_path(fname)
        if not os.path.exists(full_path) and s3_backend:
            if s3_exists:
                self._s3_get(fname)
            elif s3_exists is False:
                _logger.warning("S3 (%s) lookup prevented '%s'", s3_backend.bucket, fname)
        elif os.path.exists(full_path) and s3_backend and s3_exists is None:
            _logger.warning("S3 (%s) detected missing file '%s'", s3_backend.bucket, fname)
        return super(IrAttachment, self)._file_read(fname, bin_size=bin_size)

    @api.model
    def _file_delete(self, fname):
        if s3_backend:
            # using SQL to include files hidden through unlink or due to record rules
            cr = self._cr
            cr.execute("SELECT COUNT(*) FROM ir_attachment WHERE store_fname = %s", (fname,))
            count = cr.fetchone()[0]
            if not count:
                key = self._s3_key(fname)
                _logger.info("S3 (%s) delete '%s'", s3_backend.bucket, key)
                _logger.increment("s3.delete", 1)
                try:
                    s3_backend.client.delete_object(Bucket=s3_backend.bucket, Key=key)
                except ClientError as e:
                    if e.response['Error']['Code'] != "NoSuchKey":
                        _logger.warning("S3 (%s) delete '%s'", s3_backend.bucket, key, exc_info=True)
        return super(IrAttachment, self)._file_delete(fname)

    @api.model
    def _s3_key(self, fname):
        return 'filestore/%s/%s' % (self._cr.dbname, fname)

    @api.model
    def _s3_get(self, fname):
        key = self._s3_key(fname)
        _logger.info("S3 (%s) get '%s'", s3_backend.bucket, key)
        _logger.increment("s3.get", 1)

        try:
            r = s3_backend.client.get_object(Bucket=s3_backend.bucket, Key=key)
        except ClientError as e:
            _logger.warning("S3 (%s) get '%s'", s3_backend.bucket, key, exc_info=True)
            if e.response['Error']['Code'] == "NoSuchKey":
                raise S3NoSuchKey
            raise S3Error

        bin_data = r['Body'].read()
        checksum = self._compute_checksum(bin_data)
        value = base64.b64encode(bin_data)
        super(IrAttachment, self)._file_write(value, checksum)

    @api.model
    def _s3_put(self, fname, content_type='application/octet-stream'):
        value = super(IrAttachment, self)._file_read(fname)
        bin_data = base64.b64decode(value)

        key = self._s3_key(fname)
        _logger.info("S3 (%s) put '%s'", s3_backend.bucket, key)
        _logger.increment("s3.put", 1)

        try:
            s3_backend.client.put_object(
                Bucket=s3_backend.bucket,
                Key=key,
                Body=bin_data,
                ContentType=content_type,
                ACL='public-read',
                CacheControl=('max-age=%d, public' % (s3_backend.cache_time))
            )
        except ClientError:
            _logger.warning("S3 (%s) put '%s'", s3_backend.bucket, key, exc_info=True)
            raise S3Error
