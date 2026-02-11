import settings
import web
from os import getenv
from requests.exceptions import HTTPError
from memrise import memrise

urls = (
  r"/home/leaderboard", "leaderboard",
  r"/home", "index",
  r"/about", "about",
  r"/", "index"
)

class index:
    def GET(self):
        if not web.ctx.session.get('loggedin', False):
            return web.config.template.render.index()
        else:
            return web.config.template.render.dashboard("courses", False, False)

class leaderboard:
    def GET(self):
        if not web.ctx.session.get('loggedin', False):
            return web.config.template.render.Forbidden()

        _GET = web.input(period="alltime")
        try:
            sessionid   = web.ctx.session['loggedin']['sessionid']
            leaderboard = memrise.leaderboard(sessionid, _GET.period)
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

