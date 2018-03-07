import web
from memrise import memrise
from _globals import GLOBALS
from requests.exceptions import HTTPError

urls = (
  # Learn
  "/(\d+)/(.*)/(\d+)/garden/(preview)", "learn",
  "/(\d+)/(.*)/(\d+)/garden/(learn)", "learn",
  "/(\d+)/(.*)/(\d+)/(\d+)", "view",
  "/(\d+)/(.*)/(\d+)/(.*)", "level",
  "/(\d+)/(.*)/(\d+)", "level",

  # View course
  "/(\d+)/(.*)/garden/(preview)", "learn",
  "/(\d+)/(.*)/garden/(learn)", "learn",
  "/(\d+)/(.*)/leaderboard", "leaderboard",
  "/(\d+)/(.*)", "course",
  "/(\d+)", "course"
)

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

        return GLOBALS['render'].learn(course, kind, lvl, False)

class view:
    def GET(self, idCourse, path, lvl, thing):
        try:
            course = memrise.course(idCourse)
        except HTTPError as e:
            print e
            return GLOBALS['prender']._404()

        return GLOBALS['render'].learn(course, "preview", lvl, thing)

class level:
    def GET(self, idCourse, path, lvl, path2=""):
        try:
            items  = memrise.level(idCourse, lvl)
            course = memrise.course(idCourse)
        except HTTPError as e:
            print e
            return GLOBALS['prender']._404()

        return GLOBALS['render'].course(course, "level", {
            "name": course['levels'][lvl],
            "index": int(lvl)
        }, items)

class course:
    def GET(self, idCourse, path=""):
        try:
            course = memrise.course(idCourse)
        except HTTPError as e:
            print e
            return GLOBALS['prender']._404()

        return GLOBALS['render'].course(course, "levels", False, False)

class leaderboard:
    def GET(self, idCourse, path=""):
        _GET = web.input(period="week")
        try:
            course      = memrise.course(idCourse)
            leaderboard = memrise.leaderboard(idCourse, _GET.period)
        except HTTPError as e:
            print e
            return GLOBALS['prender']._404()

        return GLOBALS['render'].course(course, "leaderboard", _GET.period, leaderboard)


app = web.application(urls, locals())