from os import environ, getenv, path

ROOTDIR = path.dirname(path.realpath(__file__))

AUTORELOAD = bool(getenv('AUTORELOAD', None))
DEBUG = bool(getenv('DEBUG', False))
IS_TEST = getenv('WEBPY_ENV', '') == 'test'

DATABASE_URL = getenv('DATABASE_URL', '')

MEMRISE_BACKEND = 'memrise.backends.ApiMemrise'
if True or IS_TEST:
    MEMRISE_BACKEND = 'memrise.backends.DummyApiMemrise'

# Import global web object to hold web.py config
import web

# ---
# Configure debug
if DEBUG:
    debug_sql = getenv('DEBUG_SQL', None)
    debug_sql = not IS_TEST if debug_sql is None else bool(debug_sql)

    web.config.debug = True # debug trace error
    web.config.debug_sql = debug_sql # flag to enable/disable printing queries
else:
    web.config.debug = False # to be able to use session
    web.config.debug_sql = False

# ---
# Configure simple translation system
DEFAULT_LANG = getenv('DEFAULT_LANG', 'french')

if web.config.get('lang', None) is None:
    from lang import Lang

    lang = Lang()
    web.config.lang = lang
else:
    lang = web.config.lang

# ---
# Configure session
web.config.session_parameters = web.utils.storage({
    'cookie_name': 'session_id',
    'cookie_domain': None,
    'cookie_path': '/',
    'samesite': None,
    'timeout': 86400,  # 24 * 60 * 60, # 24 hours in seconds
    'ignore_expiry': True,
    'ignore_change_ip': False,
    'secret_key': 'fLjUfxqXtfNoIldA0A0K',
    'expired_message': 'Session expired',
    'httponly': True,
    'secure': False,
})

# Save session to database or to disk
DEFAULT_SESSION = {
    'lang': DEFAULT_LANG,
    'loggedin': False,
    'learning': {},
}

# ---
# Configure templating system
if web.config.get('template', None) is None:
    from variables import menu, locales
    from math import ceil
    from datetime import datetime
    import pprint, re, json

    def debug(x):
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

    # Methods accessible globally in templates
    template = web.storage({})
    template['render']        = web.template.render(ROOTDIR + '/templates/', base='_layout', globals=template)
    template['prender']       = web.template.render(ROOTDIR + '/templates/', globals=template)
    template['debug']         = debug

    template['sorted']        = sorted
    template['str']           = str
    template['ceil']          = ceil
    template['now']           = lambda: datetime.now()
    template['time']          = lambda: int(datetime.now().timestamp())
    template['date']          = lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")
    template['json']          = lambda x: json.dumps(x, sort_keys=True, indent=4, separators=(',', ': '))
    template['number_format'] = lambda x: "{:,}".format(x)
    template['floatval']      = lambda x: float(re.sub(r'[^\d]', '', x))

    # Variables accessible globally in templates
    template['locales']       = locales
    template['env']           = {
        'GITHUB_REPO': environ.get('GITHUB_REPO'),
    }
    template['MENU']          = menu

    web.config.template = template

# ---
# Configure logging
import logging

# Sets the root logger level to write to stdout (default is WARNING)
# It's equivalent to both previous statements combined:
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.WARNING)
