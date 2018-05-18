odoo.define('websocket.session', function(require) {
    'use strict';

  var Session = require('web.Session');
  var websocket = require('websocket');
  var WebSocket = require('websocket.WebSocket');

  Session.include({
    setup: function() {
      this._super.apply(this, arguments);
      if (websocket.ws) websocket.ws.destroy();
      var uri = this.origin.replace('http://', 'ws://').replace('https://', 'wss://');
      if (odoo.debug) {
        uri += '?debug=' + $.deparam($.param.querystring()).debug;
      }
      websocket.ws = new WebSocket(uri);
    }
  });

});
