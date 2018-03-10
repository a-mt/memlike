import web
from _globals import GLOBALS
from requests.exceptions import HTTPError
from memrise import memrise

urls = (
  "home/leaderboard", "leaderboard",
  "home", "index",
  "about", "about",
  "", "index"
)

class index:
    def GET(self):
        if not GLOBALS['session']['loggedin']:
            return GLOBALS['render'].index()
        else:
            return GLOBALS['render'].dashboard("courses", False, False)

class leaderboard:
    def GET(self):
        if not GLOBALS['session']['loggedin']:
            return GLOBALS['render'].Forbidden()

        _GET = web.input(period="alltime")
        try:
            sessionid   = GLOBALS['session']['loggedin']['sessionid']
            leaderboard = memrise.user_leaderboard(sessionid, _GET.period)
        except HTTPError as e:
            print e
            return GLOBALS['render'].Forbidden()

        return GLOBALS['render'].dashboard("leaderboard", _GET.period, leaderboard)

class about:
    def GET(self):
        return GLOBALS['render'].about()

app = web.application(urls, locals())