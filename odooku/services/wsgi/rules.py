import os.path
import json
import re
from urllib.parse import urlparse, urlunparse
import logging

from werkzeug.wsgi import get_current_url
from werkzeug.utils import redirect


_logger = logging.getLogger(__name__)


class BadMatchPattern(Exception):
    pass


def build_url_regex(pattern):

    regex = "^"

    # Build protocol regex
    result = re.match(r'^(\*|https?):\/\/', pattern)
    if not result:
        raise BadMatchPattern("Invalid scheme: {}".format(pattern))
    elif result.group(1) == "*":
        regex += "(https?)"
    else:
        regex += result.group(1)

    regex += ":\/\/"
    pattern = pattern[len(result.group(0)):]
    regex += "(.+)".join(map(re.escape, pattern.split("*")))
    regex += "$"

    return regex


class Rule(object):

    def __init__(self, pattern, redirect=None):
        self._regex = re.compile(build_url_regex(pattern))
        self._redirect = redirect

    def _match_url(self, url):
        parts = urlparse(url)
        return self._regex.match('%s://%s' % (parts[0], parts[1]))

    def match(self, environ):
        url = get_current_url(environ)
        return bool(self._match_url(url))

    def execute(self, environ, start_response):
        url = get_current_url(environ)
        if self._redirect:
            groups = self._match_url(url).groups()
            parts = urlparse(url)
            new_parts = urlparse(self._redirect.format(*groups))
            response = redirect(urlunparse(new_parts[:2] + parts[2:]))
            return response(environ, start_response)

class WSGIApplicationRulesWrapper(object):

    DEFAULT_PATH = os.path.abspath('rules.json')
    _rules = []

    def __init__(self, application):
        self._application = application

    def __call__(self, environ, start_response):
        for rule in self._rules:
            if(rule.match(environ)):
                result = rule.execute(environ, start_response)
                if result:
                    return result
        return self._application(environ, start_response)

    @classmethod
    def has_rules(cls):
        return bool(cls._rules)

    @classmethod
    def factory(cls, rules):
        return type(cls.__name__, (cls,), {
            '_rules': [Rule(pattern, **options) for (pattern, options) in rules.items()]
        })

    @classmethod
    def load(cls, path=DEFAULT_PATH):
        rules = {}
        if os.path.isfile(path):
            with open(path) as f:
                rules = json.load(f)
        return cls.factory(rules)
