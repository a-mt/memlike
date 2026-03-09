import web
from memrise import memrise
from utils.ajax import proxied_response


class course_edit:
    def GET(self, course_id, course_slug):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        return proxied_response(lambda: memrise.course_edit_get(course_id, course_slug))


class level_add:
    def POST(self, *args, **kwargs):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = web.input()
        return proxied_response(
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
            raise web.Unauthorized()

        data = web.input()
        return proxied_response(
            lambda: memrise.level_delete(
                level_id=data["level_id"],
                csrftoken=web.ctx.env.get("HTTP_X_CSRFTOKEN", None),
                referer=web.ctx.env.get("HTTP_X_REFERER", None),
            )
        )


class level_edit:
    def GET(self, level_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        return proxied_response(lambda: memrise.level_edit_get(level_id))


"""
class level_getcell:
    def GET(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        _GET = web.input()
        return proxied_response(
            lambda: memrise.level_thing_get(
                thing_id,
                referer=_GET.referer,
            )
        )
"""


class level_addrow:
    def POST(self, level_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        _POST = web.input()
        return proxied_response(
            lambda: memrise.level_thing_add(
                level_id,
                _POST.data,
                referer=_POST.referer,
            )
        )


class level_editcell:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        _POST = web.input()
        return proxied_response(
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
            raise web.Unauthorized()

        _POST = web.input(file={})
        return proxied_response(
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
            raise web.Unauthorized()

        _POST = web.input(f={})
        return proxied_response(
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
            raise web.Unauthorized()

        _POST = web.input(file={})
        return proxied_response(
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
            raise web.Unauthorized()

        _POST = web.input()
        return proxied_response(
            lambda: memrise.level_thing_get(
                thing_id,
                referer=_POST.referer,
            )
        )


class level_editalt:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        _POST = web.input()
        return proxied_response(
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
            raise web.Unauthorized()

        _POST = web.input(course_id="", level_index="", txt="")
        return proxied_response(
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
            raise web.Unauthorized()

        _POST = web.input()
        return proxied_response(
            lambda: memrise.level_thing_remove(
                level_id,
                _POST.id_thing,
                referer=_POST.referer,
            )
        )
