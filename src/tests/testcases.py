from app import app
from functools import partial
from re import compile
import json
import unittest

JSON_CONTENT_TYPE_RE = compile(r"^application\/(.+\+)?json")


class Client:
    def _parse_json(self, response, **extra):
        if not hasattr(response, "_json"):
            if not JSON_CONTENT_TYPE_RE.match(response.headers.get("Content-Type")):
                raise ValueError(
                    'Content-Type header is "%s", not "application/json"'
                    % response.headers.get("Content-Type")
                )
            try:
                raw = response.data
                response._json = json.loads(raw, **extra)
            except json.JSONDecodeError:
                raise ValueError(
                    "Response is not valid JSON: %r" % raw
                )
        return response._json

    def request(self, *args, **kwargs):
        response = app.request(*args, **kwargs)
        response.json = partial(self._parse_json, response)
        response.status_code = int(response.status.split(' ', 2)[0])
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
