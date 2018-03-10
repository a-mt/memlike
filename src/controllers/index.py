import web
from _globals import GLOBALS
from requests.exceptions import HTTPError
from memrise import memrise

urls = (
  "home/leaderboard", "leaderboard",
  "home", "index",
  "", "index"
)

class index:
    def GET(self):
        return GLOBALS['render'].index("courses", False, False)

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

        return GLOBALS['render'].index("leaderboard", _GET.period, leaderboard)

app = web.application(urls, locals())