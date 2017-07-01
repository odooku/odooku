odoo.define('websocket.Session', function(require) {
    'use strict';

  var core = require('web.core');
  var WebSocket = require('websocket.WebSocket');
  var Session = require('web.Session');

  Session.include({

    setup: function() {
      this._super.apply(this, arguments);
      if (this.ws) this.ws.destroy();
      var uri = this.origin.replace('http://', 'ws://').replace('https://', 'wss://');
      this.ws = new WebSocket(uri);
    },

    ws_rpc_call: function(path, params, options) {
      var data = {
        path: path,
        headers: options.headers,
        rpc: {
          jsonrpc: "2.0",
          method: "call",
          params: params,
          id: Math.floor(Math.random() * 1000 * 1000 * 1000)
        }
      };

      return this.ws.send(data).then(
        function(result) {
          core.bus.trigger('rpc:result', data, result);
          if (result.error) {
            return $.Deferred().reject('rpc', result.error);
          }
          return result.result;
        }
      );
    },

    ws_rpc: function(url, params, options, fallback) {
      var self = this;
      options = _.clone(options || {});
      var shadow = options.shadow || false;
      options.headers = _.extend({}, options.headers)
      if (odoo.debug) {
        var debugMode = $.deparam($.param.querystring()).debug;
        options.headers["X-Debug-Mode"] = debugMode || "1";
      }

      delete options.shadow;
      return self.check_session_id().then(function() {
        if (! shadow) self.trigger('request');
        return self.ws_rpc_call(url, params, options).then(
          function(result) {
            if (! shadow) self.trigger('response');
            return result;
          },
          function(type, error) {
            if (type == 'rpc') {
              // Odoo server error
              if (! shadow) self.trigger('response');
              if (error.code == 100) {
                self.uid = false;
              }
            } else {
              // Fall back to regular rpc for this request
              if (! shadow) self.trigger('response_failed');
              return fallback();
            }

            var d = $.Deferred().reject(error, $.Event());
            d.fail(function() { // Allow deferred user to disable rpc_error call in fail
              d.fail(function(error, evt) {
                if (!evt.isDefaultPrevented()) {
                  self.trigger('error', error, evt);
                }
              });
            });
            return d;
          }
        );
      });
    },

    rpc: function(url, params, options) {
      var fallback = this._super.bind(this, url, params, options);
      if (this.ws && this.ws.enabled()) {
        return this.ws_rpc(url, params, options, fallback);
      } else {
        return fallback();
      }
    }
  });

});
