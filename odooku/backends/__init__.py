import logging


_logger = logging.getLogger(__name__)


_backends = {}


def get_backend(name):
    return _backends.get(name, None)


def register_backend(name, backend):
    test = backend.test_backend()
    if test is NotImplemented or test is True:
        _backends[name] = backend
        _logger.info("Registered backend '%s'", name)
        if test is True:
            _logger.info("Backend '%s' was successfully tested", name)
    else:
        _logger.warning("Backend '%s' is unavailable", name)
