import web, json
from memrise import memrise
from requests.exceptions import HTTPError

urls = (
  "", "api",
  "/courses", "courses",
  "/course/(\d+)/(\d+)", "level",
  "/course/(\d+)", "course"
)

class api:
    def GET(self):
        web.header('Content-Type', 'application/json')

        return json.dumps({
            "courses": "/ajax/courses?{lang, cat, q, page}",
            "course": "/ajax/course/{id}",
            "course_level": "/ajax/course/{id}/{level}"
        })

class courses:
    def GET(self):
        _GET = web.input(lang="french", cat="", q="", page=1)

        web.header('Content-Type', 'application/json')
        return memrise.courses(_GET.lang, _GET.page, _GET.cat, _GET.q)

class course:
    def GET(self, id):
        try:
            course = memrise.course(id)
        except HTTPError as e:
            print e
            # https://github.com/webpy/webpy/blob/master/web/webapi.py#L15
            return web.Forbidden()

        web.header('Content-Type', 'application/json')
        return json.dumps(course)

class level:
    def GET(self, idCourse, lvl):
        try:
            level = memrise.level(idCourse, lvl)
        except HTTPError as e:
            print e
            return web.Forbidden()

        web.header('Content-Type', 'application/json')
        return json.dumps(level)

app = web.application(urls, locals())