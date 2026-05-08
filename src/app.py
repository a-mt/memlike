# Load .env file
# from dotenv import load_dotenv
# load_dotenv(path.join(pwd, '..', '.env'))
import settings
import web

# Make it work no matter the current directory
import sys

sys.path.insert(0, settings.ROOTDIR)
sys.setrecursionlimit(500)

# ---
# Configure routes
import controllers
import session
import re
import logging

from requests.exceptions import HTTPError
from pydantic_core import ValidationError


logger = logging.getLogger(__name__)


class logout:
    def GET(self):
        web.ctx.session["loggedin"] = False
        web.ctx.session["learning"] = {}
        raise web.seeother("/")


class switchLang:
    def GET(self, slug):
        # Check that languages exists
        for locale in web.config.template.LOCALES:
            if locale["slug"] == slug:
                web.ctx.session["lang_slug"] = slug
                break

        # Redirect to referer
        if "HTTP_REFERER" in web.ctx.environ:
            referer = re.search(r"(https?://[^/]+)(.*)$", web.ctx.environ["HTTP_REFERER"])

            if referer.group(1) == web.ctx.homedomain or referer.group(1) + ":80" == web.ctx.home:
                raise web.seeother(referer.group(2))

        raise web.seeother("/")


def notfound():
    return web.notfound(web.config.template.prender._404())


class designSystem:
    def GET(self):
        return web.config.template.render.design_system()


# fmt: off
urls = (
    "/community/courses", controllers.courses.app,
    "/community/course", controllers.course.app,
    "/courses", controllers.courses.app,
    "/course", controllers.course.app,
    "/aprender", controllers.learn.app,
    "/user", controllers.user.app,
    "/ajax", controllers.ajax.app,
    "/login", controllers.login.app,
    "/logout", "logout",
    "/lang/(.*)", "switchLang",
    "/design-system", "designSystem",
    "", controllers.index.app,
)
# fmt: on


# ---
# Worker-wide settings
app = web.application(
    mapping=urls,
    fvars=globals(),
    autoreload=False,
)
app.notfound = notfound

if settings.DEBUG:
    app.debug = True

    from debug import init_debug_route, init_debug_template

    init_debug_route(app)
    init_debug_template(web.config.template)
else:
    app.debug = False

# ---
# Session processor
if settings.IS_TEST:
    store = session.MemoryStore()

elif settings.SESSION_BACKEND == "session.CookieDataStore":
    store = session.CookieDataStore("session_data")

elif settings.SESSION_BACKEND == "session.DBStore":
    store = session.DBStore(web.database(), "sessions")

else:
    store = session.DiskStore("/tmp/sessions")

session = session.Session(app=None, store=store, initializer=settings.DEFAULT_SESSION)


def session_load():
    """
    Prerequisite:
    At this point the session processor should have been called
    (cookies have been read and the associated data has been loaded)

    Note:
    We create one session store per app, which fetch the sessions from the database
    The sessions are cleaned from the store at the beginning of each request
    (if session._last_cleanup_time < session_parameters.timeout)

    web.ctx contains info about the current request
    It is cleaned at the beggining of each request
    be careful with manipulating the session object: it is both a global object
    and used as holder after reading the current context
    """

    # session._data is a threaded dict that is saved at the end of the request
    web.ctx.session = session._data
    web.ctx.session_id = session.session_id

    # Make it accessible in templates
    web.config.template["session"] = session._data


if settings.IS_TEST:
    web.test = web.storage({"session": session})

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
    # Redirect HTTP to HTTPS
    if web.ctx.environ.get("HTTP_X_FORWARDED_PROTO") == "http":
        raise web.seeother(web.ctx.home.replace("http://", "https://").replace(":80", "") + web.ctx.fullpath)

    # Handle flash messages
    if "flash" in web.ctx.session:
        web.ctx.flash = web.ctx.session.flash
        del web.ctx.session.flash
    else:
        web.ctx.flash = {}

    web.config.template["flash"] = web.storage(web.ctx.flash)

app.add_processor(web.loadhook(flash_load))


# ---
# Checking raised HTTPError exceptions (web.Unauthorized) to display template,
# unless a sub-app added a __next__ to the exception
def catch_unauthorized(handler):
    try:
        result = handler()
    except web.Unauthorized as e:
        if getattr(e, "__next__", False):
            raise

        return web.config.template.prender._403()
    return result


app.add_processor(catch_unauthorized)

# ---
# Checked raise Exception to return the right HTTPError
base_internal_error = app.internalerror


def format_badrequest(e):
    headers = {"Content-Type": "application/json"}
    return web.HTTPError(status="400 Bad request", headers=headers, data=e.json())


def catch_generic_exception():
    exc_type, exc_value, tback = sys.exc_info()
    if exc_type is ValidationError:
        return format_badrequest(exc_value)

    if exc_type is HTTPError:
        if exc_value.response.status_code == 403:
            return web.Unauthorized()
        else:
            logger.warning(exc_value)
            return web.NotFound()

    return base_internal_error()


app.internalerror = catch_generic_exception


# ---
# Run app
if __name__ == "__main__" and not settings.IS_TEST:
    print(f"web2py: {web.__version__}")
    print(f"Autoreload: {settings.AUTORELOAD}")
    print(f"Debug: app={app.debug} web={web.config.debug} sql={web.config.debug_sql}")
    print(f"Memrise backend: {settings.MEMRISE_BACKEND}")

    # Reload modules that have changed
    # Is checked at the beginning of each request
    # Note that the main app isn't reloaded (so if the URLs mapping is updated, you should restart the entrypoint)
    if settings.AUTORELOAD:
        from autoreload import AutoreloadMagics

        auto_reload_extension = AutoreloadMagics()
        app.processors.insert(0, web.loadhook(auto_reload_extension.pre_execute_hook))
        app.processors.append(web.loadhook(auto_reload_extension.post_execute_hook))
        auto_reload_extension.autoreload(mode="all", log=settings.DEBUG)

    print("App processors:", app.processors)

    # Ensure all templates can be compiled
    from debug import check_load_templates

    check_load_templates(web.config.template.render._loc)

    # Check memcache status
    from cache import memcache_client

    try:
        print("Checking memcache servers...")

        stats = memcache_client.get_stats()
        print("Stats:", dict(stats))

    except Exception as e:
        print("ERR:", e)

    # Start the app
    print("Running...")
    app.run()
