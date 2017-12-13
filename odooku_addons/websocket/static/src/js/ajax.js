odoo.define('web.ajax', function(require) {
    'use strict';

  var core = require('web.core');
  var ajax = require('web.ajax.original');
  var websocket = require('websocket');

  // Copied from https://github.com/odoo/odoo/blob/11.0/addons/web/static/src/js/core/ajax.js
  function genericJsonRpc (fct_name, params, fct) {
    var data = {
        jsonrpc: "2.0",
        method: fct_name,
        params: params,
        id: Math.floor(Math.random() * 1000 * 1000 * 1000)
    };
    var xhr = fct(data);
    var result = xhr.pipe(function(result) {
        core.bus.trigger('rpc:result', data, result);
        if (result.error !== undefined) {
            if (result.error.data.arguments[0] !== "bus.Bus not available in test mode") {
                console.error("Server application error", JSON.stringify(result.error));
            }
            return $.Deferred().reject("server", result.error);
        } else {
            return result.result;
        }
    }, function() {
        //console.error("JsonRPC communication error", _.toArray(arguments));
        var def = $.Deferred();
        return def.reject.apply(def, ["communication"].concat(_.toArray(arguments)));
    });
    // FIXME: jsonp?
    result.abort = function () { if (xhr.abort) xhr.abort(); };
    return result;
  }

  // Override
  var _jsonRpc = ajax.jsonRpc;
  function jsonRpc(url, fct_name, params, settings) {
    var fallback = _jsonRpc.bind(this, url, fct_name, params, settings);
    // check for relative url
    if (websocket.ws && websocket.ws.enabled()) {
      return genericJsonRpc(fct_name, params, function(rpc) {
        return websocket.ws.send(_.extend({}, settings, {
          path: url,
          rpc: rpc
        }));
      });
    }

    return fallback();
  }

  function rpc(url, params, settings) {
    return jsonRpc(url, 'call', params, settings);
  }

  return _.extend(ajax, {
    jsonRpc: jsonRpc,
    rpc: rpc
  });

});
