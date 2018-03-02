import web, json
from memrise import memrise
from requests.exceptions import HTTPError

urls = (
  "", "api",
  "/courses", "courses",
  "/course/(\d+)/(\d+)", "level",
  "/course/(\d+)", "course",
  "/user/([^/]+)", "user",
  "/user/([^/]+)/(followers)", "user_mempals",
  "/user/([^/]+)/(following)", "user_mempals"
)

class api:
    def GET(self):
        web.header('Content-Type', 'application/json')

        return json.dumps({
            "courses": "/ajax/courses?{lang, cat, q, page}",
            "course": "/ajax/course/{id}",
            "course_level": "/ajax/course/{id}/{level}",
            "user": "/ajax/user/{username}",
            "user_followers": "/ajax/user/{username}/followers?{page}",
            "user_following": "/ajax/user/{username}/following?{page}"
        })

def _response(call):
    try:
        data = call()
    except HTTPError as e:
        # https://github.com/webpy/webpy/blob/master/web/webapi.py#L15
        print e
        if e.response.status_code == 403:
            return web.Forbidden()
        else:
            return web.NotFound()

    web.header('Content-Type', 'application/json')
    if isinstance(data, basestring):
        return data
    else:
        return json.dumps(data)

class courses:
    def GET(self):
        _GET = web.input(lang="french", cat="", q="", page=1)

        return _response(lambda: memrise.courses(_GET.lang, _GET.page, _GET.cat, _GET.q))

class course:
    def GET(self, id):
        return _response(lambda: memrise.course(id))

class level:
    def GET(self, idCourse, lvl):
        return _response(lambda: memrise.level(idCourse, lvl))

class user:
    def GET(self, username):
        return _response(lambda: memrise.user(username))

class user_mempals:
    def GET(self, username, tab):
        _GET = web.input(page=1)

        return _response(lambda: getattr(memrise, 'user_' + tab)(username, _GET.page))

app = web.application(urls, locals())