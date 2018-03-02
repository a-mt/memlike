# Import app
from os import path, environ
from dotenv import load_dotenv
from subprocess import Popen, PIPE
from variables import menu
from _globals import GLOBALS

# Import web server
import web, controllers
import imp
import pprint, re

# Load .env file
pwd = path.dirname(__file__)
dotenv_path = path.join(pwd, '.env')
load_dotenv(dotenv_path)

# Configure web server
web.config.debug = False # to be able to use session
urls = (
    '/fr/courses', controllers.courses.app,
    '/course', controllers.course.app,
    '/user', controllers.user.app,
    '/ajax', controllers.ajax.app,
    '/', controllers.index.app
)

app      = web.application(urls, globals())
session  = web.session.Session(app, web.session.DiskStore('sessions'), initializer={"lang": "french"})
render   = web.template.render('src/templates/', base='_layout', globals=GLOBALS)
prender  = web.template.render('src/templates/', globals=GLOBALS)

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
GLOBALS['number_format'] = lambda x: "{:,}".format(x)
GLOBALS['floatval']      = lambda x: float(re.sub('[^\d]', '', x))
GLOBALS['debug']         = debug

# Variables accessible globally in templates
GLOBALS['session']       = session
GLOBALS['MENU']          = menu
GLOBALS['LANG']          = imp.load_source('french', 'src/locales/french.py')

def notfound():
    return web.notfound(prender._404())

app.notfound = notfound

if __name__ == "__main__":

    # Start memcache if down
    stdout, stderr = Popen('(service memcached status | grep "not running") && sudo service memcached start || service memcached status', shell=True, stdout=PIPE).communicate()
    print stdout

    app.run()

# Translations: https://d2rhekw5qr4gcj.cloudfront.net/dist/locales/fr/translation-54de43979713.json