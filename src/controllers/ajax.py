import json
import web
from memrise import memrise
from requests.exceptions import HTTPError
from math import ceil


# fmt: off
# /ajax/level/...
urls_level = (
  r"/(\d+)", "level_edit",
    r"/(\d+)/alt", "level_alt",
    r"/(\d+)/alt_edit", "level_editalt",
    r"/(\d+)/add", "level_addrow",
    r"/(\d+)/edit", "level_editcell",
    r"/(\d+)/remove", "level_removerow",
    r"/(\d+)/upload", "level_uploadfile",
    r"/(\d+)/upload_remove", "level_removefile",
    r"/(\d+)/edit_multimedia", "level_editmultimedia",
)
# /ajax/course/...
urls_course = (
    r"/(\d+)/([^/]+)/edit", "course_edit",
    r"/(\d+)/([^/]+)/(\d+)/media", "course_level_multimedia",
    r"/(\d+)/([^/]+)/(\d+|all)/(preview|learn|classic_review|speed_review)", "course_level",
    r"/(\d+)/([^/]+)/leaderboard", "course_leaderboard",
    r"/(\d+)/([^/]+)", "course",
)
subapp_course = web.application(urls_course, locals(), autoreload=False)

urls = (
    "", "api",

    r"/courses", "courses",
    r"/community/course", subapp_course,
    r"/course", subapp_course,
    r"/level", web.application(urls_level, locals(), autoreload=False),

    r"/user/([^/]+)", "user",
    r"/user/([^/]+)/(followers)", "user_mempals",
    r"/user/([^/]+)/(following)", "user_mempals",
    r"/user/([^/]+)/(teaching)", "user_courses",
    r"/user/([^/]+)/(learning)", "user_courses",

    # logged-in user only
    r"/dashboard", "user_dashboard",
    r"/leaderboard", "user_leaderboard",
    r"/sync", "user_sync",
    r"/session", "debug_session",

    r"/(register)", "track_progress",
    r"/(session_end)", "track_progress",
)
NBPERPAGE = 15
# fmt: on


class api:
    def GET(self):
        web.header("Content-Type", "application/json")

        # fmt: off
        return json.dumps({
            "courses": "/ajax/courses?{lang, cat, q, page}",
            "course": "/ajax/course/{id}/{slug}",
            "course_leaderboard": "/ajax/course/{id}/{slug}/leaderboard?{period}",
            "course_level_preview": "/ajax/course/{id}/{slug}/{level}/preview",
            "course_level_multimedia": "/ajax/course/{id}/{slug}/{level}/media",
            "course_level_learn": "/ajax/course/{id}/{slug}/{level}/learn {cookies.sessionid}",

            "user": "/ajax/user/{username}",
            "user_followers": "/ajax/user/{username}/followers?{page}",
            "user_following": "/ajax/user/{username}/following?{page}",
            "user_teaching": "/ajax/user/{username}/teaching?{page}",
            "user_learning": "/ajax/user/{username}/learning?{page}",

            "user_dashboard": "/ajax/dashboard {cookies.sessionid}",
            "user_leaderboard": "/ajax/leaderboard {cookies.sessionid}",
            "user_sync": "/ajax/sync {cookies.sessionid}",
            "debug_session": "/ajax/session",
        })
        # fmt: on


def _error(e):
    # https://github.com/webpy/webpy/blob/master/web/webapi.py#L15
    if e.response.status_code == 403:
        return web.Forbidden()
    elif e.response.status_code == 404:
        return web.NotFound()
    else:
        print(e)
        # traceback.print_exc()
        return web.NotFound()


def _response(call):
    try:
        data = call()
    except HTTPError as e:
        return _error(e)

    web.header("Content-Type", "application/json")
    if isinstance(data, str):
        return data
    else:
        return json.dumps(data)


class courses:
    def GET(self):
        _GET = web.input(lang=web.ctx.session.lang, cat="", q="", page=1)

        return _response(lambda: memrise.courses(_GET.lang, _GET.page, _GET.cat, _GET.q))


class course:
    def GET(self, idCourse, slug):
        _GET = web.input(session=False)

        if _GET.session and _GET.session != "0":
            if not web.ctx.session.get("loggedin", False):
                return web.Forbidden()

        return _response(lambda: memrise.course(idCourse, slug))


class course_level:
    def GET(self, idCourse, slugCourse, lvl, kind="preview"):
        _GET = web.input(session=False)

        if _GET.session and _GET.session != "0":
            if not web.ctx.session.get("loggedin", False):
                return web.Forbidden()

        if slugCourse == "":
            slugCourse = "-"

        return _response(lambda: memrise.level(idCourse, slugCourse, lvl, kind))


class course_level_multimedia:
    def GET(self, idCourse, slug, lvl):
        try:
            data = memrise.level_multimedia(idCourse, slug, lvl)
        except HTTPError as e:
            return _error(e)

        web.header("Content-Type", "text/plain")
        return data


class course_leaderboard:
    def GET(self, idCourse, slug):
        _GET = web.input(period="week")
        return _response(lambda: memrise.course_leaderboard(idCourse, _GET.period))


class course_edit:
    def GET(self, idCourse, slug):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        return _response(lambda: memrise.course_edit_get(idCourse, slug))


class level_edit:
    def GET(self, idLevel):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        return _response(lambda: memrise.level_edit_get(idLevel))


class level_getcell:
    def GET(self, idThing):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _GET = web.input()
        return _response(
            lambda: memrise.level_thing_get(
                idThing,
                referer=_GET.referer,
            )
        )


class level_addrow:
    def POST(self, idLevel):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input()
        return _response(
            lambda: memrise.level_thing_add(
                idLevel,
                _POST.data,
                referer=_POST.referer,
            )
        )


class level_editcell:
    def POST(self, idThing):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input()
        return _response(
            lambda: memrise.level_thing_edit(
                idThing,
                _POST.cellId,
                _POST.cellValue,
                referer=_POST.referer,
            )
        )


class level_uploadfile:
    def POST(self, idThing):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input(file={})
        return _response(
            lambda: memrise.level_thing_upload(
                idThing,
                _POST.cellId,
                _POST.file,
                referer=_POST.referer,
            )
        )


class level_removefile:
    def POST(self, idThing):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input(file={})
        return _response(
            lambda: memrise.level_thing_upload_remove(
                idThing,
                _POST.cellId,
                _POST.fileId,
                referer=_POST.referer,
            )
        )


class level_alt:
    def POST(self, idThing):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input()
        return _response(
            lambda: memrise.level_thing_get(
                idThing,
                referer=_POST.referer,
            )
        )


class level_editalt:
    def POST(self, idThing):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input()
        return _response(
            lambda: memrise.level_thing_alt_edit(
                idThing,
                _POST.alts,
                _POST.cellId,
                referer=_POST.referer,
            )
        )


class level_editmultimedia:
    def POST(self, idLevel):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input()
        return _response(
            lambda: memrise.level_multimedia_edit(
                idLevel,
                _POST.txt,
                referer=_POST.referer,
            )
        )


class level_removerow:
    def POST(self, idLevel):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input()
        return _response(
            lambda: memrise.level_thing_remove(
                idLevel,
                _POST.id_thing,
                referer=_POST.referer,
            )
        )


class user:
    def GET(self, username):
        return _response(lambda: memrise.user(username))


class user_mempals:
    def GET(self, username, tab):
        _GET = web.input(page=1)

        return _response(lambda: getattr(memrise, "user_" + tab)(username, _GET.page))


class user_courses:
    def GET(self, username, tab):
        try:
            data = memrise.user_courses(tab, username)
        except HTTPError as e:
            return _error(e)

        web.header("Content-Type", "application/json")

        # Pagination
        _GET = web.input(page=1)
        page = int(_GET.page)

        if not isinstance(page, int) and not page.isdigit():
            page = 1

        lastpage = int(ceil(data["nbCourse"] / NBPERPAGE)) or 1
        if page > lastpage:
            page = lastpage
        offset = (page - 1) * NBPERPAGE

        data["lastpage"] = lastpage
        data["page"] = page
        data["has_next"] = page != lastpage
        data["content"] = data["content"][offset : offset + 1 + NBPERPAGE]

        return json.dumps(data)


class user_dashboard:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

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
            print("HTTPError", e)

            if e.response.status_code == 403:
                raise web.Forbidden()
            else:
                raise web.NotFound()

        return ""


class user_leaderboard:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _GET = web.input(period="week")
        return _response(lambda: memrise.my_leaderboard(_GET.period))


class user_sync:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        try:
            data = memrise.user(web.ctx.session["loggedin"]["username"], True)
        except HTTPError as e:
            if e.response.status_code == 403:
                raise web.Forbidden()
            else:
                raise web.NotFound()

        return data


class debug_session:
    def GET(self):
        session = dict(web.ctx.session)
        web.header("Content-Type", "application/json")
        return json.dumps(session)


class track_progress:
    def POST(self, path):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        progress = memrise.track_progress(
            path,
            web.input(),
            csrftoken=web.ctx.env.get("HTTP_X_CSRFTOKEN"),
            referer=web.ctx.env.get("HTTP_X_REFERER"),
        )
        return _response(lambda: progress)


app = web.application(urls, locals(), autoreload=False)
