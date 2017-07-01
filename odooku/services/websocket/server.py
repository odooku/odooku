import logging

from odooku.services.wsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler


from .application import WebSocketApplicationWrapper


_logger = logging.getLogger(__name__)


class WebSocketServer(WSGIServer):

    def __init__(self, *args, **kwargs):
        kwargs['handler_class'] = WebSocketHandler
        super(WebSocketServer, self).__init__(*args, **kwargs)

    def load(self, *args, **kwargs):
        application = super(WebSocketServer, self).load(*args, **kwargs)
        _logger.info("Websockets enabled")
        return WebSocketApplicationWrapper(application, self.timeout)
