# Load .env file
# from dotenv import load_dotenv
# load_dotenv(path.join(pwd, '..', '.env'))
import settings
import web

# Make it work no matter the current directory
import sys
sys.path.insert(0, settings.ROOTDIR)

# ---
# Configure routes
import controllers
import session
import re

class logout():
    def GET(self):
        web.ctx.session['loggedin'] = False
        web.ctx.session['learning'] = {}
        raise web.seeother('/')

class switchLang():
    def GET(self, name):

        # Check that languages exists
        for l in web.config.template.locales:
            if l['slug'] == name:
                web.ctx.session['lang'] = name
                break

        # Redirect to referer
        if 'HTTP_REFERER' in web.ctx.environ:
            referer = re.search(r'(https?://[^/]+)(.*)$', web.ctx.environ['HTTP_REFERER'])

            if referer.group(1) + ':80' == web.ctx.home:
                raise web.seeother(referer.group(2))

        raise web.seeother('/')

def notfound():
    return web.notfound(web.config.template.prender._404())

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

# ---
# Worker-wide settings
app = web.application(
    mapping=urls,
    fvars=globals(),
    autoreload=settings.AUTORELOAD,
)
app.notfound = notfound

if settings.DEBUG:
    app.debug = True
else:
    app.debug = False

# ---
# Session processor
if settings.IS_TEST:
    store =  session.MemoryStore()
else:
    # if settings.DATABASE_URL: store = session.DBStore(web.database(), 'sessions')
    store = session.DiskStore('/tmp/sessions')

session = session.Session(app=None, store=store, initializer=settings.DEFAULT_SESSION)

def session_load():
    """
    Prerequisite:
    At this point the session processor should habe been called
    (cookies have been read and the associated data has been loaded)

    Note:
    We create one session store per app, which fetch the sessions
    The sessions are cleaned from the store at the beginning of each request
    (if session._last_cleanup_time < session_parameters.timeout)

    web.ctx contains info about the current request
    It is cleaned at the beggining of each request
    be careful with manipulating the session object: it is both a global object
    and used as holder after reading the current context
    """
    web.ctx.session = session
    web.ctx.session_id = session.session_id

    # Make it accessible in templates
    web.config.template['session'] = session

# Processors are run at each request
app.add_processor(session._processor)
app.add_processor(web.loadhook(session_load))

# ---
# Lang processor
lang = web.config.lang
app.add_processor(lang._processor)

# ---
# Flash messages processor
def flash_load():

    # Redirect HTTP ot HTTPS
    if web.ctx.environ.get('HTTP_X_FORWARDED_PROTO') == 'http':
        raise web.seeother(web.ctx.home.replace('http://', 'https://').replace(':80', '') + web.ctx.fullpath)

    # Handle flash messages
    if 'flash' in web.ctx.session:
        web.ctx.flash = web.ctx.session.flash
        del web.ctx.session.flash
    else:
        web.ctx.flash = {}

app.add_processor(web.loadhook(flash_load))

# ---
# Run app
if __name__ == '__main__' and not settings.IS_TEST:
    print(f'web2py: {web.__version__}')
    print(f'Autoreload: {settings.AUTORELOAD}')
    print(f'Debug: app={app.debug} web={web.config.debug} sql={web.config.debug_sql}')

    print('Running...')
    app.run()

# Translations: https://d2rhekw5qr4gcj.cloudfront.net/dist/locales/fr/translation-54de43979713.json
