import gevent

from .channel import WebSocketChannel


class WebSocketApplicationWrapper(object):

    def __init__(self, application, ping_delay=None):
        self._application = application
        self._channel = WebSocketChannel()
        gevent.spawn(self._channel.run_forever, ping_delay)

    def __call__(self, environ, start_response):
        ws = environ.get('wsgi.websocket')
        if ws:
            self._channel.listen(ws, environ.copy())
            return []
        else:
            return self._application(environ, start_response)
