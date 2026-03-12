import web
from utils import validator
from memrise import memrise
from requests.exceptions import HTTPError

# fmt: off
urls = (
    r".*", "login",
)
# fmt: on


class login:
    def GET(self):
        input_data = validator.validate(
            fields={
                "redirect": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=web.input(),
        )

        _GET = web.storage(input_data)
        err = web.ctx.flash["err"] if "err" in web.ctx.flash else {}
        data = web.ctx.flash["data"] if "data" in web.ctx.flash else {}

        return web.config.template.render.login(_GET.redirect, err, data)

    def TEST(self):
        """
        Is used in tests to force a login
        """
        data = memrise.login("bob", "pass")

        web.ctx.session.loggedin = data

        raise web.seeother("/", absolute=True)

    def POST(self):
        input_data = validator.validate(
            fields={
                "redirect": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
                "username": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
                "password": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=web.input(),
        )

        _POST = web.storage(input_data)
        err = {}

        # Check required fields
        if not _POST["username"]:
            err["username"] = "required"
        if not _POST["password"]:
            err["password"] = "required"

        if err:
            web.ctx.session.flash = {"err": err, "data": _POST}
            raise web.seeother("")

        # Try login
        try:
            data = memrise.login(_POST["username"], _POST["password"])
            if data is None:
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
            err["username"] = "wrong_credentials"

            web.ctx.session.flash = {"err": err, "data": _POST}
            raise web.seeother("")


app = web.application(urls, locals(), autoreload=False)
