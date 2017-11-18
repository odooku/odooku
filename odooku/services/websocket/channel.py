import time
import json
import gevent

import psycopg2
import werkzeug.wrappers
from geventwebsocket.exceptions import WebSocketError

import odoo
from odoo.tools import ustr

from .requests import WebSocketRpcRequest


class WebSocketChannel(object):

    def __init__(self):
        self._wss = {}

    def _add(self, ws):
        self._wss[ws] = {}

    def _remove(self, ws):
        del self._wss[ws]

    def get_request(self, httprequest, payload):
        if 'path' in payload:
            httprequest.environ.update({
                'PATH_INFO': payload.get('path')
            })

        if 'headers' in payload:
            httprequest.environ.update({
                'HTTP_%s' % key.replace('-', '_').upper(): val
                for key, val
                in payload.get('headers').items()
            })

        if 'rpc' in payload:
            return WebSocketRpcRequest(httprequest, payload.get('rpc'))

    def run_forever(self, ping_delay):
        while True:
            for ws, state in dict(self._wss).items():
                if ws.closed:
                    self._remove(ws)
                    continue

                # Keep socket alive on Heroku (or other platforms).
                last_ping = state.get('last_ping', None)
                now = int(round(time.time()))
                if not last_ping or last_ping + ping_delay < now:
                    state['last_ping'] = now
                    try:
                        ws.send(json.dumps({'ping': now}))
                    except WebSocketError:
                        self._remove(ws)
                        continue

            gevent.sleep(1)

    def dispatch(self, request):
        with odoo.api.Environment.manage():
            with request:
                try:
                    odoo.registry(request.session.db).check_signaling()
                    with odoo.tools.mute_logger('odoo.sql_db'):
                        ir_http = request.registry['ir.http']
                except (AttributeError, psycopg2.OperationalError, psycopg2.ProgrammingError):
                    result = {}
                else:
                    result = ir_http._dispatch()

        return result

    def respond(self, ws, httprequest, message):
        if any(key not in message for key in ['id', 'payload']):
            # Invalid message, close connection and abort
            ws.close()
            return

        response = {
            'id': message.get('id'),
        }

        request = self.get_request(httprequest, message.get('payload'))
        if request:
            payload = self.dispatch(request)
            response.update({
                'payload': payload
            })
        else:
            response.update({
                'error': {
                    'message': "Unknown payload"
                }
            })

        try:
            ws.send(json.dumps(response, default=ustr))
        except WebSocketError:
            pass

    def listen(self, ws, environ):
        self._add(ws)
        while not ws.closed:
            try:
                message = ws.receive()
            except WebSocketError:
                break

            if message is not None:
                try:
                    message = json.loads(message)
                except json.JSONDecodeError:
                    break

                # Odoo heavily relies on httprequests, for each message
                # a new httprequest will be created. This request will be
                # based on the original environ from the socket initialization
                # request.
                httprequest = werkzeug.wrappers.Request(environ.copy())
                odoo.http.root.setup_session(httprequest)
                odoo.http.root.setup_db(httprequest)
                odoo.http.root.setup_lang(httprequest)
                gevent.spawn(self.respond, ws, httprequest, message)

        self._remove(ws)
