import web
from utils import validator
from memrise import memrise
from requests.exceptions import HTTPError

# fmt: off
urls = (
    r"/(preview|learn|review|classic_review|speed_review)", "learn",
)
# fmt: on


class learn:
    def GET(self, session_type):
        input_data = validator.validate(
            fields={
                "course_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "level_index": validator.field(
                    validator.schema.int_schema(),
                    default=False,
                    on_error="default",
                ),
            },
            data=web.input(),
        )

        _GET = web.storage(input_data)
        try:
            course = memrise.course(_GET["course_id"], course_slug="")
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.learn(course, session_type, _GET["level_index"], False, 1, 0)


app = web.application(urls, locals(), autoreload=False)
