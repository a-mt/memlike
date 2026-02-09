import web
from os import getenv
from _globals import GLOBALS
from memrise import memrise
from requests.exceptions import HTTPError

urls = (
  r".*", "login"
)

class login:
    def GET(self):
        _GET = web.input(redirect="")
        err  = web.flash['err'] if 'err' in web.flash else {}
        data = web.flash['data'] if 'data' in web.flash else {}

        return GLOBALS['render'].login(_GET.redirect, err, data)

    def TEST(self):
        data = memrise.login('admin','pass')

        GLOBALS['session'].loggedin = data

        raise web.seeother('/', absolute=True)

    def POST(self):
        _POST = web.input(username="", password="", redirect="")
        err   = {}

        # Check required fields
        if not _POST['username']:
            err['username'] = 'required'
        if not _POST['password']:
            err['password'] = 'required'

        if err:
            GLOBALS['session'].flash = {"err": err, "data": _POST}
            raise web.seeother('')

        # Try login
        try:
            data = memrise.login(_POST['username'], _POST['password'])
            if data == None:
                GLOBALS['session'].loggedin = False
            else:
                GLOBALS['session'].loggedin = data

            redirect = _POST.redirect
            if not redirect:
                redirect = "/"

            raise web.seeother(redirect, absolute=True)

        # Wrong credentials
        except HTTPError as e:
            print(e)
            err['username'] = 'wrong_credentials'

            GLOBALS['session'].flash = {"err": err, "data": _POST}
            raise web.seeother('')

app = web.application(urls, locals(), autoreload=getenv('AUTORELOAD', None))
