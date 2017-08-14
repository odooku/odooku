import gevent.monkey
gevent.monkey.patch_all()

import psycogreen.gevent
psycogreen.gevent.patch_psycopg()

from odooku.patch import apply_patches
apply_patches()

import csv
csv.field_size_limit(500 * 1024 * 1024)