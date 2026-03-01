import web
from memrise import memrise
from requests.exceptions import HTTPError

# fmt: off
urls = (
    r"/(preview|learn|classic_review|speed_review)", "learn",
)
# fmt: on


class learn:
    def GET(self, kind):
        _GET = web.input(course_id="", level_index="")

        try:
            course = memrise.course(_GET["course_id"], slugCourse="")
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.learn(course, kind, _GET["level_index"], False, 1)


app = web.application(urls, locals(), autoreload=False)
