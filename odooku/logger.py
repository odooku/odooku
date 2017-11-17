import sys
import socket
import threading
import logging
from logging.config import dictConfig

METRIC_VAR = "metric"
VALUE_VAR = "value"
MTYPE_VAR = "mtype"
GAUGE_TYPE = "gauge"
COUNTER_TYPE = "counter"
HISTOGRAM_TYPE = "histogram"


class DBFormatter(logging.Formatter):
    def format(self, record):
        db_name = getattr(threading.current_thread(), 'dbname', None)
        record.db = ' @%s ' % db_name if db_name is not None else ' '
        return super(DBFormatter, self).format(record)


class OdookuLogger(logging.Logger):

    _statsd_host = None
    _statsd_sock = None
    _statsd_prefix = ''

    def __init__(self, name=None):
        super(OdookuLogger, self).__init__(name)
        if self._statsd_host:
            try:
                host, port = self._statsd_host.split(':')
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.connect((host, int(port)))
            except Exception:
                pass
            else:
                self._statsd_sock = sock

    def critical(self, msg, *args, **kwargs):
        self.log(logging.CRITICAL, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.log(logging.ERROR, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.log(logging.WARNING, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.log(logging.INFO, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.log(logging.DEBUG, msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.log(logging.ERROR, msg, *args, **kwargs)

    def log(self, lvl, msg, *args, **kwargs):
        try:
            extra = kwargs.get("extra", None)
            if extra is not None:
                metric = extra.get(METRIC_VAR, None)
                value = extra.get(VALUE_VAR, None)
                typ = extra.get(MTYPE_VAR, None)
                if metric and value and typ:
                    if typ == GAUGE_TYPE:
                        self.gauge(metric, value)
                    elif typ == COUNTER_TYPE:
                        self.increment(metric, value)
                    elif typ == HISTOGRAM_TYPE:
                        self.histogram(metric, value)
                    else:
                        pass
        except Exception:
            logging.Logger.warning(self, "Failed to log to statsd", exc_info=True)

        if msg:
            logging.Logger.log(self, lvl, msg, *args, **kwargs)

    def gauge(self, name, value):
        self._sock_send("{0}{1}:{2}|g".format(self._statsd_prefix, name, value))

    def increment(self, name, value, sampling_rate=1.0):
        self._sock_send("{0}{1}:{2}|c|@{3}".format(self._statsd_prefix, name, value, sampling_rate))

    def decrement(self, name, value, sampling_rate=1.0):
        self._sock_send("{0){1}:-{2}|c|@{3}".format(self._statsd_prefix, name, value, sampling_rate))

    def histogram(self, name, value):
        self._sock_send("{0}{1}:{2}|ms".format(self._statsd_prefix, name, value))

    def _sock_send(self, msg):
        try:
            if self._statsd_sock is not None:
                if isinstance(msg, str):
                    msg = msg.encode("ascii")
                self._statsd_sock.send(msg)
        except Exception:
            logging.Logger.warning(self, "Failed to log to statsd", exc_info=True)


def setup(debug=False, statsd_host=None):
    level = 'DEBUG' if debug else 'INFO'
    dictConfig(dict(
        version=1,
        disable_existing_loggers=True,
        loggers={
            '': {
                'level': level,
                'handlers': ['console']
            },
        },
        handlers={
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                # Log to stderr so that click commands can make
                # use of stdout
                'stream': sys.stderr
            },
        },
        formatters={
            'standard': {
                'format': '[%(levelname)s]%(db)s%(message)s',
                '()': 'odooku.logger.DBFormatter'
            },
        }
    ))

    OdookuLogger._statsd_host = statsd_host
    logging.setLoggerClass(OdookuLogger)
    logging.addLevelName(25, 'INFO')

    # Prevent odoo from overriding log config
    import odoo.netsvc
    odoo.netsvc._logger_init = True
