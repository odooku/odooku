import logging
import odoo
import werkzeug.exceptions

_logger = logging.getLogger(__name__)


IGNORE_EXCEPTIONS = (
    odoo.osv.orm.except_orm,
    odoo.exceptions.AccessError,
    odoo.exceptions.ValidationError,
    odoo.exceptions.MissingError,
    odoo.exceptions.AccessDenied,
    odoo.exceptions.Warning,
    odoo.exceptions.RedirectWarning,
    werkzeug.exceptions.HTTPException
)


class WebRequestMixin(object):

    def _handle_exception(self, exception):
        if not isinstance(exception, IGNORE_EXCEPTIONS):
            _logger.exception("Exception caught", exc_info=True)
        return super(WebRequestMixin, self)._handle_exception(exception)
