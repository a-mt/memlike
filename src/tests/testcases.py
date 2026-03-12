from app import app
from functools import partial, cached_property
from re import compile
from utils.datastructures import CaseInsensitiveMapping, SimpleCookie
from unittest.util import safe_repr

import json
import unittest
import types
import os
import web


JSON_CONTENT_TYPE_RE = compile(r"^application\/(.+\+)?json")


class Client:
    def _parse_json(self, response, **extra):
        if not hasattr(response, "_json"):
            content_type = response.headers.get("Content-Type")
            if not content_type or not JSON_CONTENT_TYPE_RE.match(content_type):
                raise ValueError('Content-Type header is "%s", not "application/json"' % content_type)
            try:
                raw = response.data
                response._json = json.loads(raw, **extra)
            except json.JSONDecodeError:
                raise ValueError("Response is not valid JSON: %r" % raw)
        return response._json

    def _parse_headers(self, response, **extra):
        if not hasattr(response, "_headers"):
            try:
                response._headers = CaseInsensitiveMapping(response.headers)
            except Exception:
                raise ValueError("Response headers is not a valid enumerable")
        return response._headers

    def _parse_cookies(self, response, **extra):
        """
        A Python :class:`~http.cookies.SimpleCookie` object, containing the current
        values of all the client cookies. See the documentation of the
        :mod:`http.cookies` module for more.
        """
        if not hasattr(response, "_cookies"):
            response._cookies = SimpleCookie([x[1] for x in response.header_items if x[0].lower() == "set-cookie"])
        return response._cookies

    def app(self, raw_data):
        base_load = app.load

        def load(self, env):
            base_load(env)
            web.ctx.data = raw_data
            #web.ctx.environ["wsgi.errors"] = open(os.devnull, 'w')

        app.load = types.MethodType(load, app)
        return app

    def request(self, *args, **kwargs):
        response = app.request(*args, **kwargs)
        response.json = partial(self._parse_json, response)
        response.get_headers = partial(self._parse_headers, response)
        response.get_cookies = partial(self._parse_cookies, response)
        response.status_code = int(response.status.split(" ", 2)[0])
        return response


class SimpleTestCase(unittest.TestCase):
    client_class = Client
    _pre_setup_ran_eagerly = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not issubclass(cls, unittest.TestCase):
            cls._pre_setup()
            cls._pre_setup_ran_eagerly = True

    def __call__(self, result=None):
        """
        Wrapper around default __call__ method to perform common Django test
        set up. This means that user-defined TestCases aren't required to
        include a call to super().setUp().
        """
        self._setup_and_call(result)

    def _setup_and_call(self, result, debug=False):
        """
        Perform the following in order: pre-setup, run test, post-teardown,
        skipping pre/post hooks if test is set to be skipped.

        If debug=True, reraise any errors in setup and use super().debug()
        instead of __call__() to run the test.
        """
        if self.__class__._pre_setup_ran_eagerly:
            self.__class__._pre_setup_ran_eagerly = False
        else:
            self._pre_setup()
        super().__call__(result)

    @classmethod
    def _pre_setup(cls):
        cls.client = cls.client_class()

    def get_auth_cookies(self):
        response = self.client.request("/login", method="TEST")

        assert response.status_code == 303
        return response.get_cookies()

    def assertEndsWith(self, s, suffix, msg=None):
        try:
            if s.endswith(suffix):
                return
        except (AttributeError, TypeError):
            self._tail_type_check(s, suffix, msg)
            raise
        a = safe_repr(s, short=True)
        b = safe_repr(suffix)
        if isinstance(suffix, tuple):
            standardMsg = f"{a} doesn't end with any of {b}"
        else:
            standardMsg = f"{a} doesn't end with {b}"
        self.fail(self._formatMessage(msg, standardMsg))
