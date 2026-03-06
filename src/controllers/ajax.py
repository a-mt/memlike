import json
import settings
import web
from math import ceil
from memrise import memrise
from requests.exceptions import HTTPError


# fmt: off
# /ajax/level/...
urls_level = (
    r"/add", "level_add",
    r"/delete", "level_delete",
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

urls_thing = (
    r"/cell/upload_file/", "level_uploadfile_compat",
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
    r"/courses", "courses",
    r"/community/course", subapp_course,
    r"/course", subapp_course,
    r"/level", web.application(urls_level, locals(), autoreload=False),
    r"/thing", web.application(urls_thing, locals(), autoreload=False),

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

    r"/register_progress", "learning_session_register_progress",
    r"/register_end", "learning_session_register_end",
    r"/reset_progress_level", "reset_progress_level",

    "", "index",
)
NBPERPAGE = 15
# fmt: on


class index:
    def GET(self):
        web.header("Content-Type", "application/json")

        # fmt: off
        patterns = {
            "courses": r"GET /ajax/courses?{lang, cat, q, page}",
            "course": r"GET /ajax/course/{course_id}/{course_slug}",
            "course_leaderboard": r"GET /ajax/course/{course_id}/{course_slug}/leaderboard?{period}",
            "course_level_preview": r"GET /ajax/course/{course_id}/{course_slug}/{level_index}/preview",
            "course_level_multimedia": r"GET /ajax/course/{course_id}/{course_slug}/{level_index}/media",
            "course_level_learn": r"GET /ajax/course/{course_id}/{course_slug}/{level_index}/learn {cookies.sessionid}",

            "user": r"GET /ajax/user/{username}",
            "user_followers": r"GET /ajax/user/{username}/followers?{page}",
            "user_following": r"GET /ajax/user/{username}/following?{page}",
            "user_teaching": r"GET /ajax/user/{username}/teaching?{page}",
            "user_learning": r"GET /ajax/user/{username}/learning?{page}",

            "user_dashboard": r"GET /ajax/dashboard {cookies.sessionid}",
            "user_leaderboard": r"GET /ajax/leaderboard {cookies.sessionid}",
            "user_sync": r"GET /ajax/sync {cookies.sessionid}",
            "debug_session": r"GET /ajax/session",
        }
        # fmt: on

        # Add URLs we did not bother to add in patterns
        from utils.debug import autodetect_urls

        autodetect_urls(app, prefix="/ajax", res=patterns)

        return json.dumps(patterns)


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
        _GET = web.input(lang=web.ctx.session.get("lang_slug", settings.DEFAULT_LANG_SLUG), cat="", q="", page=1)

        return _response(lambda: memrise.courses(_GET.lang, _GET.page, _GET.cat, _GET.q))


class course:
    def GET(self, course_id, course_slug):
        _GET = web.input(session=False)

        if _GET.session and _GET.session != "0":
            if not web.ctx.session.get("loggedin", False):
                return web.Forbidden()

        return _response(lambda: memrise.course(course_id, course_slug))


class course_level:
    def GET(self, course_id, course_slug, level_index, session_type="preview"):
        _GET = web.input(session=False)

        if _GET.session and _GET.session != "0":
            if not web.ctx.session.get("loggedin", False):
                return web.Forbidden()

        if course_slug == "":
            course_slug = "-"

        return _response(lambda: memrise.level(course_id, course_slug, level_index, session_type))


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
        return _response(lambda: memrise.course_leaderboard(course_id, _GET.period))


class course_edit:
    def GET(self, course_id, course_slug):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        return _response(lambda: memrise.course_edit_get(course_id, course_slug))


class level_add:
    def POST(self, *args, **kwargs):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        data = web.input()
        return _response(
            lambda: memrise.level_add(
                course_id=data["course_id"],
                pool_id=data.get("pool_id", None),
                csrftoken=web.ctx.env.get("HTTP_X_CSRFTOKEN", None),
                referer=web.ctx.env.get("HTTP_X_REFERER", None),
            )
        )


class level_delete:
    def POST(self, *args, **kwargs):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        data = web.input()
        return _response(
            lambda: memrise.level_delete(
                level_id=data["level_id"],
                csrftoken=web.ctx.env.get("HTTP_X_CSRFTOKEN", None),
                referer=web.ctx.env.get("HTTP_X_REFERER", None),
            )
        )


class level_edit:
    def GET(self, level_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        return _response(lambda: memrise.level_edit_get(level_id))


"""
class level_getcell:
    def GET(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _GET = web.input()
        return _response(
            lambda: memrise.level_thing_get(
                thing_id,
                referer=_GET.referer,
            )
        )
"""


class level_addrow:
    def POST(self, level_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input()
        return _response(
            lambda: memrise.level_thing_add(
                level_id,
                _POST.data,
                referer=_POST.referer,
            )
        )


class level_editcell:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input()
        return _response(
            lambda: memrise.level_thing_edit(
                thing_id,
                _POST.cell_id,
                _POST.cell_value,
                referer=_POST.referer,
            )
        )


class level_uploadfile:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input(file={})
        return _response(
            lambda: memrise.level_thing_upload(
                thing_id,
                _POST.cell_id,
                _POST.file,
                referer=_POST.referer,
            )
        )


class level_uploadfile_compat:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input(f={})
        return _response(
            lambda: memrise.level_thing_upload(
                _POST.thing_id,
                _POST.cell_id,
                _POST.f,
                referer=_POST.referer,
                csrftoken=_POST.csrfmiddlewaretoken,
            )
        )

class level_removefile:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input(file={})
        return _response(
            lambda: memrise.level_thing_upload_remove(
                thing_id,
                _POST.cell_id,
                _POST.file_id,
                referer=_POST.referer,
            )
        )


class level_alt:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input()
        return _response(
            lambda: memrise.level_thing_get(
                thing_id,
                referer=_POST.referer,
            )
        )


class level_editalt:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input()
        return _response(
            lambda: memrise.level_thing_alt_edit(
                thing_id,
                _POST.alts,
                _POST.cell_id,
                referer=_POST.referer,
            )
        )


class level_editmultimedia:
    def POST(self, level_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input(course_id="", level_index="", txt="")
        return _response(
            lambda: memrise.level_multimedia_edit(
                level_id,
                _POST.txt,
                referer=_POST.referer,
                course_id=_POST.course_id,
                level_index=_POST.level_index,
            )
        )


class level_removerow:
    def POST(self, level_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _POST = web.input()
        return _response(
            lambda: memrise.level_thing_remove(
                level_id,
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

        lastpage = int(ceil(data["nb_courses"] / NBPERPAGE)) or 1
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


class learning_session_register_progress:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        data = web.jsoninput()
        progress = memrise.learning_session_register_progress(data)
        return _response(lambda: progress)


class learning_session_register_end:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        data = web.jsoninput()
        progress = memrise.learning_session_register_end(data)
        return _response(lambda: progress)


class reset_progress_level:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        data = web.jsoninput()
        response = memrise.reset_progress_level(data)
        return _response(lambda: response)


app = web.application(urls, locals(), autoreload=False)
