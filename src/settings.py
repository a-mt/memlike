from os import environ, getenv, path

ROOTDIR = path.dirname(path.realpath(__file__))
IS_TEST = getenv("WEBPY_ENV", "") == "test" or getenv("PYTEST_VERSION", None) is not None

AUTORELOAD = bool(getenv("AUTORELOAD", None))
DEBUG = bool(getenv("DEBUG", False))

USE_HTTPS = bool(getenv("USE_HTTPS", ""))
MEMRISE_BACKEND = "memrise.backends.CachedApiMemrise"
SESSION_BACKEND = getenv("SESSION_BACKEND", "")
MEMCACHE_KEY_PREFIX = ""
MEMCACHE_SERVERS = environ.get("MEMCACHIER_SERVERS", "").split(",")
MEMCACHE_USERNAME = environ.get("MEMCACHIER_USERNAME", "")
MEMCACHE_PASSWORD = environ.get("MEMCACHIER_PASSWORD", "")

MEMRISE_ANON_USERNAME = environ.get("MEMRISE_ANON_USERNAME", "66b1d91e8e")
MEMRISE_ANON_PASSWORD = environ.get("MEMRISE_ANON_PASSWORD", "66b1d91e8e66b1d91e8e!")
DUMMY_SINGLE_LEVEL = "6618687"

DATABASE_URL = getenv("DATABASE_URL", "")
DEFAULT_LANG_SLUG = getenv("DEFAULT_LANG_SLUG", "french")

if IS_TEST:
    MEMRISE_BACKEND = "memrise.backends.DummyApiMemrise"
    MEMCACHE_KEY_PREFIX = "test_"

    DEBUG = False
    DEFAULT_LANG_SLUG = "english"

# Import global web object to hold web.py config
import web

# ---
# Configure debug
if DEBUG:
    debug_sql = getenv("DEBUG_SQL", None)
    debug_sql = not IS_TEST if debug_sql is None else bool(debug_sql)

    web.config.debug = True  # debug trace error
    web.config.debug_sql = debug_sql  # flag to enable/disable printing queries
else:
    web.config.debug = False  # to be able to use session
    web.config.debug_sql = False

# ---
# Configure simple translation system
if web.config.get("lang", None) is None:
    from lang import Lang

    lang = Lang()
    web.config.lang = lang
else:
    lang = web.config.lang

# ---
# Configure session
web.config.session_parameters = web.utils.storage(
    {
        "cookie_name": "session_id",
        "cookie_domain": None,
        "cookie_path": "/",
        "samesite": None,
        "timeout": 86400,  # 24 * 60 * 60, # 24 hours in seconds
        "ignore_expiry": True,
        "ignore_change_ip": True,
        "secret_key": "fLjUfxqXtfNoIldA0A0K",
        "expired_message": "Session expired",
        "httponly": True,
        "secure": USE_HTTPS,
    }
)

# Save session to database or to disk
DEFAULT_SESSION = {
    "lang_slug": DEFAULT_LANG_SLUG,
    "loggedin": False,
    "learning": {},
}

# ---
# Configure templating system

# Modules that need to stay in scope after reloading the settings (used in lambdas)
import datetime
import pprint
import re
import json
from unidecode import unidecode

if web.config.get("template", None) is None:
    from variables import MENU, LOCALES
    from math import ceil

    def debug(x):
        # fmt: off
        return (
            '<pre class="debug">' +
                pprint.pformat(x, indent=4)
                    .replace('\\n', '\n')
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace("'", '&quot;')
            + '</pre>'
        )
        # fmt: on

    # Methods accessible globally in templates
    template = web.storage({})
    template["render"] = web.template.render(ROOTDIR + "/templates/", base="_layout", globals=template)
    template["prender"] = web.template.render(ROOTDIR + "/templates/", globals=template)
    template["debug"] = debug
    template["flash"] = web.storage({})

    template["sorted"] = sorted
    template["unidecode"] = unidecode
    template["str"] = str
    template["ceil"] = ceil
    template["min"] = min
    template["max"] = max
    template["now"] = lambda: datetime.datetime.now()
    template["time"] = lambda: int(datetime.datetime.now().timestamp())
    template["date"] = lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")
    template["json"] = lambda x: json.dumps(x, sort_keys=True, indent=4, separators=(",", ": "))
    template["number_format"] = lambda x: "{:,}".format(x)
    template["floatval"] = lambda x: float(re.sub(r"[^\d]", "", x))

    # Variables accessible globally in templates
    template["LOCALES"] = LOCALES
    template["ENV"] = {"GITHUB_REPO": environ.get("GITHUB_REPO")}
    template["MENU"] = MENU
    template["LANG"] = ""
    template["I18N"] = {}

    web.config.template = template

    # Add a flash message in session
    web.config.FLASH_MESSAGES_TAGS = web.storage(
        {
            "DEBUG": "debug",
            "INFO": "info",
            "SUCCESS": "success",
            "WARNING": "warning",
            "ERROR": "danger",
        }
    )


# ---
# Configure logging
import logging
import logging.config


class DebugLinksFilter(logging.Filter):
    def filter(self, record):
        """
        Determine if the specified record is to be logged.

        Is the specified record to be logged? Returns 0 for no, nonzero for
        yes. If deemed appropriate, the record may be modified in-place.
        """

        """
        Keep DEBUG request URL (msg == %s://%s:%s "%s %s %s" %s %s)
        {
            'name': 'urllib3.connectionpool',
            'msg': '%s://%s:%s "%s %s %s" %s %s',
            'args': (
                'https',
                'community-courses.memrise.com',
                443,
                'POST',
                '/v1.25/learning_sessions/preview/',
                'HTTP/1.1',
                200,
                None,
            ),
            'levelname': 'DEBUG',
            'levelno': 10,
            'pathname': '/usr/local/lib/python3.12/site-packages/urllib3/connectionpool.py',
            'filename': 'connectionpool.py',
            'module': 'connectionpool',
            'exc_info': None,
            'exc_text': None,
            'stack_info': None,
            'lineno': 544,
            'funcName': '_make_request',
            'created': 1771956062.8577926,
            'msecs': 857.0,
            'relativeCreated': 4002.8045177459717,
            'thread': 129189639874240,
            'threadName': 'CP Server Thread-5',
            'processName': 'MainProcess',
            'process': 283,
            'taskName': None
        }
        """
        if record.levelno == logging.DEBUG:
            return record.msg[0] == "%"
        return True


# Sets the root logger level to write to stdout (default is WARNING)
# logging.basicConfig()
conf = {
    "version": 1,
    "formatters": {
        "form1": {
            "format": "%(asctime)s ++ %(levelname)s ++ %(name)s ++ %(message)s",
            "datefmt": "%H:%M:%S",  #'%Y-%m-%d %H:%M:%S',
        },
    },
    "handlers": {
        "hand1": {
            "class": "logging.StreamHandler",
            "formatter": "form1",
            "level": "NOTSET",
            "stream": "ext://sys.stdout",
        },
    },
    "filters": {
        "keepDebugLinks": {
            "()": DebugLinksFilter,
        },
    },
    "root": {
        "level": logging.DEBUG if DEBUG else logging.WARNING,
        "handlers": ["hand1"],
    },
    "loggers": {
        "session": {
            "level": logging.DEBUG if getenv("DEBUG_SESSION", "") else logging.WARNING,
        },
        "autoreload": {
            "level": logging.WARNING,
        },
        "debug.template": {
            "level": logging.WARNING,
        },
        "urllib3.connectionpool": {
            "filters": ["keepDebugLinks"],
        },
    },
}
logging.config.dictConfig(conf)
