import os


def prefix_envvar(envvar):
    return 'ODOOKU_%s' % envvar


def get_envvar(envvar, default=None):
    return os.environ.get(prefix_envvar(envvar), default)
