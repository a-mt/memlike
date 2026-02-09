# Make it work no matter the current directory
from os import path, environ, getenv
import sys

pwd = path.dirname(path.realpath(__file__))
sys.path.insert(0, pwd)

# Import app
from dotenv import load_dotenv
from variables import menu, locales
from _globals import GLOBALS

# Import web server
import web, controllers
from lang import Lang
import pprint, re, time, json
from math import ceil
from datetime import datetime

# Load .env file
dotenv_path = path.join(pwd, '..', '.env')
load_dotenv(dotenv_path)

IS_TEST = getenv('WEBPY_ENV', '') == 'test'

# Configure web server
if getenv('DEBUG', False):
    web.config.debug = True # debug trace error
    web.config.debug_sql = not IS_TEST # flag to enable/disable printing queries
else:
    web.config.debug = False # to be able to use session
    web.config.debug_sql = False

web.config.session_parameters.secret_key = web.utils.storage(
    {
        "cookie_name": "session_id",
        "cookie_domain": None,
        "cookie_path": '/',
        "samesite": None,
        "timeout": 86400,  # 24 * 60 * 60, # 24 hours in seconds
        "ignore_expiry": True,
        "ignore_change_ip": True,
        "secret_key": "fLjUfxqXtfNoIldA0A0K",
        "expired_message": "Session expired",
        "httponly": True,
        "secure": False,
    }
)

urls = (
    '/fr/courses', controllers.courses.app,
    '/course', controllers.course.app,
    '/user', controllers.user.app,
    '/ajax', controllers.ajax.app,
    '/login', controllers.login.app,
    '/logout', 'logout',
    '/lang/(.*)', 'switchLang',
    '', controllers.index.app
)

app = web.application(mapping=urls, fvars=globals(), autoreload=getenv('AUTORELOAD', None))
if getenv('DEBUG', False):
    app.debug = True
else:
    app.debug = False

# Save session to database or to disk
if IS_TEST:
    session_store =  web.session.MemoryStore()
elif environ.get('DATABASE_URL', ''):
    session_store = web.session.DBStore(web.database(), 'sessions')
else:
    session_store = web.session.DiskStore('sessions')

session = web.session.Session(app, session_store, initializer=GLOBALS['defaults'])

lang     = Lang(app, session, pwd)
render   = web.template.render(pwd + '/templates/', base='_layout', globals=GLOBALS)
prender  = web.template.render(pwd + '/templates/', globals=GLOBALS)

def debug(x):
    return '<pre class="debug">' + pprint.pformat(x, indent=4) \
        .replace('\\n', '\n') \
        .replace('&', '&amp;') \
        .replace("<", "&lt;") \
        .replace(">", "&gt;") \
        .replace('"', '&quot;') + '</pre>';

# Methods accessible globally in templates
GLOBALS['render']        = render
GLOBALS['prender']       = prender

GLOBALS['sorted']        = sorted
GLOBALS['str']           = str
GLOBALS['ceil']          = ceil
GLOBALS['now']           = lambda: datetime.now()
GLOBALS['time']          = lambda: int(datetime.now().timestamp())
GLOBALS['date']          = lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")
GLOBALS['json']          = lambda x: json.dumps(x, sort_keys=True, indent=4, separators=(',', ': '))
GLOBALS['number_format'] = lambda x: "{:,}".format(x)
GLOBALS['floatval']      = lambda x: float(re.sub(r'[^\d]', '', x))
GLOBALS['debug']         = debug

# Variables accessible globally in templates
GLOBALS['session']       = session
GLOBALS['LANG']          = lang
GLOBALS['env']           = {
    "GITHUB_REPO": environ.get("GITHUB_REPO"),
}
GLOBALS['MENU']          = menu
GLOBALS['locales']       = locales

class logout():
    def GET(self):
        GLOBALS['session'].loggedin = False
        GLOBALS['session'].learning = {}
        raise web.seeother('/')

class switchLang():
    def GET(self, name):

        # Check that languages exists
        for l in locales:
            if l['slug'] == name:
                session['lang'] = name
                break

        # Redirect to referer
        if 'HTTP_REFERER' in web.ctx.environ:
            referer = re.search('(https?://[^/]+)(.*)$', web.ctx.environ['HTTP_REFERER'])

            if referer.group(1) + ':80' == web.ctx.home:
                raise web.seeother(referer.group(2))

        raise web.seeother('/')

def notfound():
    return web.notfound(prender._404())

app.notfound = notfound

def flash():
    # Redirect HTTP ot HTTPS
    if web.ctx.environ.get('HTTP_X_FORWARDED_PROTO') == 'http':
        raise web.seeother(web.ctx.home.replace('http://', 'https://').replace(':80', '') + web.ctx.fullpath)

    # Handle flash messages
    if "flash" in session:
        web.flash = session.flash
        del session.flash
    else:
        web.flash = {}

app.add_processor(web.loadhook(flash))

if __name__ == "__main__" and not IS_TEST:
    autoreload = 'true' if getenv('AUTORELOAD', None) else 'false'

    print(f'Run app (web2py={web.__version__}, debug={app.debug}, autoreload={autoreload})...')
    app.run()

# Translations: https://d2rhekw5qr4gcj.cloudfront.net/dist/locales/fr/translation-54de43979713.json
