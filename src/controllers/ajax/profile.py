import json
import web
from memrise import memrise
from requests.exceptions import HTTPError
from utils.webapi import proxied_response
from utils import validator


class user_dashboard:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        input_data = validator.validate(
            fields={
                "offset": validator.field(
                    validator.schema.int_schema(),
                    default=0,
                ),
            },
            data=web.input(),
        )
        _GET = web.storage(input_data)
        offset = _GET.offset

        web.header("Content-type", "text/plain")
        web.header("Transfer-Encoding", "chunked")

        try:
            for page in memrise.whatistudy(offset=offset):
                courses = page["courses"]
                content = web.config.template.prender.ajax_dashboard(courses, offset)["__body__"]

                yield json.dumps({"content": content.strip()}) + "$"
                offset += len(courses)

                # Take this opportunity to sync courses in session
                # for course in courses:
                #     data = {}
                #     for k in ["progress"]:
                #         data[k] = course[k]

            if page and page.get("next_offset", 0):
                yield json.dumps({"next_offset": page["next_offset"]}) + "$"

        except HTTPError as e:
            if e.response.status_code == 403:
                raise web.Unauthorized()
            else:
                raise web.NotFound()

        return ""


class user_leaderboard:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

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
        return proxied_response(lambda: memrise.my_leaderboard(_GET.period))


class user_sync:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        try:
            data = memrise.user(web.ctx.session["loggedin"]["username"], True)
        except HTTPError as e:
            if e.response.status_code == 403:
                raise web.Unauthorized()
            else:
                raise web.NotFound()

        return data
