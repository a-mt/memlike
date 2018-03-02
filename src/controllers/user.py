import web
from memrise import memrise
from _globals import GLOBALS
from variables import levels
from requests.exceptions import HTTPError

urls = (
  "/([^/]+)/mempals/(followers)/", "user",
  "/([^/]+)/mempals/(following)/", "user",
  "/(.*)", "user"
)

class user:
    def GET(self, username, tab="stats"):
        username = username.strip('/').split('/')[0]

        try:
            user = memrise.user(username)
            user['url'] = web.ctx['homepath'] + '/' + username
        except HTTPError as e:
            print e
            return GLOBALS['prender']._404()

        return GLOBALS['render'].user(user, tab, levels)

app = web.application(urls, locals())