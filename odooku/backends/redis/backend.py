import redis
import logging

from odooku.backends.base import BaseBackend

_logger = logging.getLogger(__name__)


class RedisBackend(BaseBackend):

    def __init__(self, host, port, password=None, db_number=None,
            maxconn=None, maxconn_timeout=None):

        self._pool = redis.BlockingConnectionPool(
            host=host,
            port=port,
            password=password,
            db=db_number or 0,
            max_connections=maxconn or 50,
            timeout=maxconn_timeout or 20
        )

        self._client = redis.StrictRedis(
            connection_pool=self._pool
        )

    @property
    def client(self):
        return self._client
