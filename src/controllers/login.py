import settings
import web
from os import getenv
from memrise import memrise
from requests.exceptions import HTTPError

urls = (
  r".*", "login"
)

class login:
    def GET(self):
        _GET = web.input(redirect="")
        err  = web.ctx.flash['err'] if 'err' in web.ctx.flash else {}
        data = web.ctx.flash['data'] if 'data' in web.ctx.flash else {}

        return web.config.template.render.login(_GET.redirect, err, data)

    def TEST(self):
        """
        Is used in tests to force a login
        """
        data = memrise.login('bob','pass')

        web.ctx.session.loggedin = data

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
            web.ctx.session.flash = {"err": err, "data": _POST}
            raise web.seeother('')

        # Try login
        try:
            data = memrise.login(_POST['username'], _POST['password'])
            if data == None:
                web.ctx.session.loggedin = False
            else:
                web.ctx.session.loggedin = data

            redirect = _POST.redirect
            if not redirect:
                redirect = "/"

            raise web.seeother(redirect, absolute=True)

        # Wrong credentials
        except HTTPError as e:
            print(e)
            err['username'] = 'wrong_credentials'

            web.ctx.session.flash = {"err": err, "data": _POST}
            raise web.seeother('')

app = web.application(urls, locals(), autoreload=False)
