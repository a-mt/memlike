import web
from _globals import GLOBALS
from memrise import memrise
from requests.exceptions import HTTPError

urls = (
  ".*", "login"
)

class login:
    def GET(self):
        _GET = web.input(redirect="")
        err  = web.flash['err'] if 'err' in web.flash else {}
        data = web.flash['data'] if 'data' in web.flash else {}

        return GLOBALS['render'].login(_GET.redirect, err, data)

    def POST(self):
        _POST = web.input()
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
            sessionid = memrise.login(_POST['username'], _POST['password'])
            data      = memrise.whoami(sessionid)
            GLOBALS['session'].loggedin = data

            redirect = _POST.redirect
            if not redirect:
                redirect = "/"

            raise web.seeother(redirect, absolute=True)

        # Wrong credentials
        except HTTPError:
            err['username'] = 'wrong_credentials'

            GLOBALS['session'].flash = {"err": err, "data": _POST}
            raise web.seeother('')

app = web.application(urls, locals())