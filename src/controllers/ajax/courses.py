import json
import settings
import web
from math import ceil
from memrise import memrise
from requests.exceptions import HTTPError
from utils.ajax import proxied_response


class courses:
    def GET(self):
        _GET = web.input(lang=web.ctx.session.get("lang_slug", settings.DEFAULT_LANG_SLUG), cat="", q="", page=1)

        return proxied_response(lambda: memrise.courses(_GET.lang, _GET.page, _GET.cat, _GET.q))


class course:
    def GET(self, course_id, course_slug):
        _GET = web.input(session=False)

        if _GET.session and _GET.session != "0":
            if not web.ctx.session.get("loggedin", False):
                return web.Unauthorized()

        return proxied_response(lambda: memrise.course(course_id, course_slug))


class course_level:
    def GET(self, course_id, course_slug, level_index, session_type="preview"):
        _GET = web.input(session=False)

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
            return _error(e)

        web.header("Content-Type", "text/plain")
        return data


class course_leaderboard:
    def GET(self, course_id, course_slug):
        _GET = web.input(period="week")
        return proxied_response(lambda: memrise.course_leaderboard(course_id, _GET.period))
