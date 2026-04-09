import settings
import web
import variables
from memrise import memrise
from requests.exceptions import HTTPError
from utils.webapi import proxied_response, error_response
from utils import validator
from pydantic_core import PydanticCustomError


class courses:
    def GET(self):
        def check_lang_slug(value):
            if value not in variables.source_languages:
                raise PydanticCustomError(
                    "invalid",
                    "Expected a valid language, got '{wrong_value}'",
                    {"wrong_value": value},
                )
            return value

        input_data = validator.validate(
            fields={
                "lang": validator.field(
                    validator.schema.str_schema(),
                    validator=check_lang_slug,
                    default=web.ctx.session.get("lang_slug", settings.DEFAULT_LANG_SLUG),
                ),
                "cat": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
                "q": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
                "page": validator.field(
                    validator.schema.int_schema(gt=0),
                    default=1,
                ),
            },
            data=web.input(),
        )
        _GET = web.storage(input_data)

        return proxied_response(lambda: memrise.courses(_GET.lang, _GET.page, _GET.cat, _GET.q))


class course:
    def GET(self, course_id, course_slug):
        input_data = validator.validate(
            fields={
                "session": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=web.input(),
        )
        _GET = web.storage(input_data)

        if _GET.session and _GET.session != "0":
            if not web.ctx.session.get("loggedin", False):
                return web.Unauthorized()

        return proxied_response(lambda: memrise.course(course_id, course_slug))


class course_level:
    def GET(self, course_id, course_slug, level_index, session_type="preview"):
        input_data = validator.validate(
            fields={
                "session": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=web.input(),
        )
        _GET = web.storage(input_data)

        if _GET.session and _GET.session != "0":
            if not web.ctx.session.get("loggedin", False):
                return web.Unauthorized()

        if course_slug == "":
            course_slug = "-"

        return proxied_response(lambda: memrise.level(course_id, course_slug, level_index, session_type))


class course_level_multimedia:
    def GET(self, course_id, course_slug, level_index):
        try:
            data = memrise.level_multimedia(course_id, course_slug, level_index)
        except HTTPError as e:
            return error_response(e)

        web.header("Content-Type", "text/plain")
        return data


class course_leaderboard:
    def GET(self, course_id, course_slug):
        input_data = validator.validate(
            fields={
                "period": validator.field(
                    validator.str_choices_schema(["month", "week", "alltime"]),
                    default="week",
                ),
            },
            data=web.input(),
        )

        _GET = web.storage(input_data)
        return proxied_response(lambda: memrise.course_leaderboard(course_id, _GET.period))
