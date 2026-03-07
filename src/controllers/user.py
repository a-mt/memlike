import web
from memrise import memrise
from variables import USER_RANKS
from requests.exceptions import HTTPError

# fmt: off
urls = (
    r"/([^/]+)/courses/(teaching)/?", "user",
    r"/([^/]+)/courses/(learning)/?", "user",
    r"/([^/]+)/mempals/(followers)/?", "user",
    r"/([^/]+)/mempals/(following)/?", "user",
    r"/(.*)", "user",
)
# fmt: on


class user:
    def GET(self, username, tab="stats"):
        username = username.strip("/").split("/")[0]

        try:
            user = memrise.user(username)
        except HTTPError as e:
            print(e)
            if web.ctx.session.get("loggedin", False) and web.ctx.session["loggedin"]["username"] == username:
                return web.config.template.prender._403()

            return web.config.template.prender._404()

        return web.config.template.render.user(user, tab, USER_RANKS)


app = web.application(urls, locals(), autoreload=False)
