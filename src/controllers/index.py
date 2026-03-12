import web
from requests.exceptions import HTTPError
from memrise import memrise
from utils import validator

# fmt: off
urls = (
    r"/home/leaderboard", "leaderboard",
    r"/home", "index",
    r"/about", "about",
    r"/", "index",
)
# fmt: on


class index:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            return web.config.template.render.index()
        else:
            return web.config.template.render.dashboard("courses", False, False)


class leaderboard:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        input_data = validator.validate(
            fields={
                "period": validator.field(
                    validator.str_choices_schema(["month", "week", "alltime"]),
                    default="week",
                    on_error="default",
                ),
            },
            data=web.input(),
        )

        _GET = web.storage(input_data)
        try:
            leaderboard = memrise.my_leaderboard(_GET.period)
        except HTTPError as e:
            if e.response.status_code == 403:
                return web.config.template.prender._403()
            else:
                print(e)
                return web.config.template.prender._404()

        return web.config.template.render.dashboard("leaderboard", _GET.period, leaderboard)


class about:
    def GET(self):
        return web.config.template.render.about()


app = web.application(urls, locals(), autoreload=False)
