import web
from memrise import memrise
from _globals import GLOBALS
from requests.exceptions import HTTPError

urls = (
  "/(\d+)/(.*)/(\d+)/(.*)", "level",
  "/(\d+)/(.*)/(\d+)", "level",
  "/(\d+)/(.*)", "course",
  "/(\d+)", "course"
)

class level:
    def GET(self, idCourse, path, lvl, path2=""):
        try:
            items  = memrise.level(idCourse, lvl)
            course = memrise.course(idCourse)
        except HTTPError as e:
            print e
            return GLOBALS['prender']._404()

        return GLOBALS['render'].course(course, {
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

        return GLOBALS['render'].course(course, False, False)

app = web.application(urls, locals())