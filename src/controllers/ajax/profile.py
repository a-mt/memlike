import json
import web
from memrise import memrise
from requests.exceptions import HTTPError
from utils.ajax import proxied_response


class user_dashboard:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        _GET = web.input(offset=0)
        offset = _GET.offset
        if type(offset) is not int and not offset.isdigit():
            offset = 0
        else:
            offset = int(offset)

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

        _GET = web.input(period="week")
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
