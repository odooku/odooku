odoo.define('web.ajax', function(require) {
    'use strict';

  var core = require('web.core');
  var ajax = require('web.ajax.original');
  var websocket = require('websocket');

  // Copied from https://github.com/odoo/odoo/blob/11.0/addons/web/static/src/js/core/ajax.js
  function genericJsonRpc(fct_name, params, settings, fct) {
    var shadow = settings.shadow || false;
    delete settings.shadow;
    if (!shadow)
      core.bus.trigger('rpc_request');
  
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
    result.abort = function() {
      if (xhr.abort) xhr.abort();
    };
  
    var p = result.then(function(result) {
      if (!shadow) {
        core.bus.trigger('rpc_response');
      }
      return result;
    }, function(type, error, textStatus, errorThrown) {
      if (type === "server") {
        if (!shadow) {
          core.bus.trigger('rpc_response');
        }
        if (error.code === 100) {
          core.bus.trigger('invalidate_session');
        }
        return $.Deferred().reject(error, $.Event());
      } else {
        if (!shadow) {
          core.bus.trigger('rpc_response_failed');
        }
        var nerror = {
          code: -32098,
          message: "XmlHttpRequestError " + errorThrown,
          data: {
            type: "xhr" + textStatus,
            debug: error.responseText,
            objects: [error, errorThrown]
          },
        };
        return $.Deferred().reject(nerror, $.Event());
      }
    });
    return p.fail(function() { // Allow deferred user to disable rpc_error call in fail
      p.fail(function(error, event) {
        if (!event.isDefaultPrevented()) {
          core.bus.trigger('rpc_error', error, event);
        }
      });
    });
  }

  // Override
  var _jsonRpc = ajax.jsonRpc;
  function jsonRpc(url, fct_name, params, settings) {
    settings = settings || {};
    var fallback = _jsonRpc.bind(this, url, fct_name, params, settings);
    // check for relative url
    if (websocket.ws && websocket.ws.enabled()) {
      return genericJsonRpc(fct_name, params, settings, function(rpc) {
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
