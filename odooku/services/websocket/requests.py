import logging
import odoo.http
from odooku.request import WebRequestMixin


_logger = logging.getLogger(__name__)


class WebSocketRequest(WebRequestMixin, odoo.http.WebRequest):

    def __init__(self, httprequest):
        super(WebSocketRequest, self).__init__(httprequest)

    def dispatch(self):
        raise NotImplementedError()


class WebSocketRpcRequest(WebSocketRequest):

    _request_type = 'json'

    def __init__(self, httprequest, data):
        super(WebSocketRpcRequest, self).__init__(httprequest)
        self.params = data.get('params', {})
        self.id = data.get('id')
        self.context = self.params.pop('context', dict(self.session.context))

    def dispatch(self):
        try:
            result = self._call_function(**self.params)
        except Exception as exception:
            return self._handle_exception(exception)
        return self._json_response(result)

    def _json_response(self, result=None, error=None):
        response = {
            'jsonrpc': '2.0',
            'id': self.id
        }

        if error is not None:
            response['error'] = error
        if result is not None:
            response['result'] = result

        return response

    def _handle_exception(self, exception):
        """Called within an except block to allow converting exceptions
           to arbitrary responses. Anything returned (except None) will
           be used as response."""
        try:
            return super(WebSocketRpcRequest, self)._handle_exception(exception)
        except Exception:
            if not isinstance(exception, (odoo.exceptions.Warning, odoo.http.SessionExpiredException, odoo.exceptions.except_orm)):
                _logger.exception("Exception during JSON request handling.")
            error = {
                    'code': 200,
                    'message': "Odoo Server Error",
                    'data': odoo.http.serialize_exception(exception)
            }
            if isinstance(exception, odoo.http.AuthenticationError):
                error['code'] = 100
                error['message'] = "Odoo Session Invalid"
            if isinstance(exception, odoo.http.SessionExpiredException):
                error['code'] = 100
                error['message'] = "Odoo Session Expired"
            return self._json_response(error=error)
