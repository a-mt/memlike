import web
from memrise import memrise
from _globals import GLOBALS
from requests.exceptions import HTTPError

urls = (
  # Learn
  "/(\d+)/(.*)/(\d+)/garden", "learn_fromform",
  "/(\d+)/(.*)/(\d+)/(\d+)", "view",
  "/(\d+)/(.*)/(\d+)/(.*)", "level",
  "/(\d+)/(.*)/(\d+)", "level",

  # View course
  "/(\d+)/(.*)/garden", "learn_fromform",
  "/(\d+)/(.*)/garden/(preview|learn|classic_review|speed_review)", "learn",
  "/(\d+)/(.*)/leaderboard", "leaderboard",
  "/(\d+)/(.*)", "course",
  "/(\d+)", "course"
)

class learn_fromform:
    def GET(self, idCourse, path, lvl=False):
        _GET = web.input(session="", sendresults=0)

        try:
            course = memrise.course(idCourse)
        except HTTPError as e:
            print e
            return GLOBALS['prender']._404()

        return GLOBALS['render'].learn(course, _GET.session, lvl, False, _GET.sendresults)

class learn:
    def GET(self, idCourse, path, lvl, kind=False):
        if not kind:
            kind = lvl
            lvl  = False
        try:
            course = memrise.course(idCourse)
        except HTTPError as e:
            print e
            return GLOBALS['prender']._404()

        return GLOBALS['render'].learn(course, kind, lvl, False, 1)

class view:
    def GET(self, idCourse, path, lvl, thing):
        try:
            course = memrise.course(idCourse)
        except HTTPError as e:
            print e
            return GLOBALS['prender']._404()

        return GLOBALS['render'].learn(course, "preview", lvl, thing, 0)

class level:
    def GET(self, idCourse, slugCourse, lvl, path2=""):
        try:
            course = memrise.course(idCourse)
            if lvl not in course['levels']:
                return GLOBALS['prender']._404()

            try:
                if course['levels'][lvl]['type'] == 1:
                    sessionid = False
                    if GLOBALS['session']['loggedin']:
                        sessionid = GLOBALS['session']['loggedin']['sessionid']

                    items = memrise.level(idCourse, slugCourse, lvl, "preview", sessionid)
                else:
                    # Type multimedia
                    items = memrise.level_multimedia(course['url'], lvl)
            except HTTPError as e:
                items = {"learnables":[], "thingusers":[]}

        except HTTPError as e:
            if e.response.status_code == 403:
                return GLOBALS['prender']._403()
            else:
                return GLOBALS['prender']._404()

        return GLOBALS['render'].course_level(course, {
            "name": course['levels'][lvl]['name'],
            "type": course['levels'][lvl]['type'],
            "index": int(lvl)
        }, items)

class course:
    def GET(self, idCourse, slugCourse=""):
        learning = False
        items    = False
        try:
            sessionid = False
            if GLOBALS['session']['loggedin']:
                sessionid = GLOBALS['session']['loggedin']['sessionid']

            course = memrise.course(idCourse, sessionid)

            # Course without any level ?
            if len(course["levels"]) == 0:
                items = memrise.level(idCourse, slugCourse, "1", "preview", sessionid)

        except HTTPError as e:
            print e
            return GLOBALS['prender']._404()

        if items:
            return GLOBALS['render'].course_level(course, {
                "name": False,
                "type": 1,
                "index": -1
            }, items)

        return GLOBALS['render'].course_summary(course)

class leaderboard:
    def GET(self, idCourse, path=""):
        _GET = web.input(period="week")
        try:
            course      = memrise.course(idCourse)
            leaderboard = memrise.leaderboard(idCourse, _GET.period)
        except HTTPError as e:
            print e
            return GLOBALS['prender']._404()

        return GLOBALS['render'].course_leaderboard(course, _GET.period, leaderboard)


app = web.application(urls, locals())