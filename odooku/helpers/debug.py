import time
import logging
import greenlet
import gevent
import contextlib


_logger = logging.getLogger(__name__)


class BlockDebugger(object):

    def __init__(self, timeout=1000):
        self.timeout = timeout
        self._active_greenlet = None
        self._greenlet_switch_counter = 0
        self._greenlet_last_switch_time = None
        greenlet.settrace(self._greenlet_switch_tracer)

    def _greenlet_switch_tracer(self, what, (origin, target)):
        self._active_greenlet = target
        self._greenlet_switch_counter += 1
        then = self._greenlet_last_switch_time
        now = self._greenlet_last_switch_time = time.time()
        if then is not None:
            blocking_time = int(round((now - then) * 1000))
            if origin is not gevent.hub.get_hub():
                if blocking_time > self.timeout:
                    _logger.warning("Greenlet blocked for %s ms" % blocking_time)

    @contextlib.contextmanager
    def check_block(self):
        # Remember the time of last switch before entering the context.
        old_switch_time = self._greenlet_last_switch_time
        yield None
        # If the time of last switch has not changed when exiting the context,
        # then we obviously didn't yield back to the event loop.
        if old_switch_time is not None:
            if old_switch_time == self._greenlet_last_switch_time:
                raise RuntimeError("Code did not yield to gevent")
