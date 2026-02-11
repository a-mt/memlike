import settings
import web
from os import getenv
from memrise import memrise
from variables import levels
from requests.exceptions import HTTPError

urls = (
  r"/([^/]+)/courses/(teaching)/?", "user",
  r"/([^/]+)/courses/(learning)/?", "user",
  r"/([^/]+)/mempals/(followers)/?", "user",
  r"/([^/]+)/mempals/(following)/?", "user",
  r"/(.*)", "user"
)

class user:
    def GET(self, username, tab="stats"):
        username = username.strip('/').split('/')[0]

        try:
            user = memrise.user(username)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.user(user, tab, levels)

app = web.application(urls, locals(), autoreload=settings.AUTORELOAD)

