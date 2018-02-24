import web, json
from memrise import memrise

urls = (
  "", "api",
  "/courses", "courses"
)

class api:
    def GET(self):
        web.header('Content-Type', 'application/json')

        return json.dumps({
            "courses": "/ajax/courses {lang, cat, q, page}"
        })

class courses:
    def GET(self):
        _GET = web.input(lang="french", cat="", q="", page=1)

        web.header('Content-Type', 'application/json')
        return memrise.courses(_GET.lang, _GET.page, _GET.cat, _GET.q)

app = web.application(urls, locals())