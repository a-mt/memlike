import web
from memrise import memrise
from utils.ajax import proxied_response
from utils import validator


class course_edit:
    def GET(self, course_id, course_slug):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        return proxied_response(lambda: memrise.course_edit_get(course_id, course_slug))


class level_add:
    def POST(self, *args, **kwargs):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                'course_id': validator.field(
                    validator.schema.int_schema(),
                ),
                'pool_id': validator.field(
                    validator.schema.int_schema(),
                    default=None,
                ),
            },
            data=web.input(),
        )

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

        data = validator.validate(
            fields={
                'level_id': validator.field(
                    validator.schema.int_schema(),
                ),
            },
            data=web.input(),
        )

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

        data = validator.validate(
            fields={
                'data': validator.field(
                    validator.schema.str_schema(),
                ),
                'referer': validator.field(
                    validator.schema.str_schema(),
                    default='',
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_thing_add(
                level_id,
                data["data"],
                referer=data["referer"],
            )
        )


class level_editcell:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                'cell_id': validator.field(
                    validator.schema.int_schema(),
                ),
                'cell_value': validator.field(
                    validator.schema.str_schema(),
                ),
                'referer': validator.field(
                    validator.schema.str_schema(),
                    default='',
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_thing_edit(
                thing_id,
                data["cell_id"],
                data["cell_value"],
                referer=data["referer"],
            )
        )


class level_uploadfile:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        values = web.input(file={})

        data = validator.validate(
            fields={
                'cell_id': validator.field(
                    validator.schema.int_schema(),
                ),
                'file': validator.field(
                    validator.is_file_schema(),
                ),
                'referer': validator.field(
                    validator.schema.str_schema(),
                    default='',
                ),
            },
            data=values,
        )
        return proxied_response(
            lambda: memrise.level_thing_upload(
                thing_id,
                data["cell_id"],
                data["file"],
                referer=data["referer"],
            )
        )


class level_uploadfile_compat:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                'thing_id': validator.field(
                    validator.schema.int_schema(),
                ),
                'cell_id': validator.field(
                    validator.schema.int_schema(),
                ),
                'f': validator.field(
                    validator.is_file_schema(),
                ),
                'referer': validator.field(
                    validator.schema.str_schema(),
                    default='',
                ),
                'csrfmiddlewaretoken': validator.field(
                    validator.schema.str_schema(),
                    default='',
                ),
            },
            data=web.input(f={}),
        )

        return proxied_response(
            lambda: memrise.level_thing_upload(
                data["thing_id"],
                data["cell_id"],
                data["f"],
                referer=data["referer"],
                csrftoken=data["csrfmiddlewaretoken"],
            )
        )


class level_removefile:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                'cell_id': validator.field(
                    validator.schema.int_schema(),
                ),
                'file_id': validator.field(
                    validator.schema.int_schema(),
                ),
                'referer': validator.field(
                    validator.schema.str_schema(),
                    default='',
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_thing_upload_remove(
                thing_id,
                data["cell_id"],
                data["file_id"],
                referer=data["referer"],
            )
        )


class level_alt:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                'referer': validator.field(
                    validator.schema.str_schema(),
                    default='',
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_thing_get(
                thing_id,
                referer=data["referer"],
            )
        )


class level_editalt:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                'cell_id': validator.field(
                    validator.schema.int_schema(),
                ),
                'alts': validator.field(
                    validator.schema.str_schema(),
                ),
                'referer': validator.field(
                    validator.schema.str_schema(),
                    default='',
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_thing_alt_edit(
                thing_id,
                data["alts"],
                data["cell_id"],
                referer=data["referer"],
            )
        )


class level_editmultimedia:
    def POST(self, level_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                'course_id': validator.field(
                    validator.schema.int_schema(),
                ),
                'level_index': validator.field(
                    validator.schema.int_schema(),
                ),
                'txt': validator.field(
                    validator.schema.str_schema(),
                ),
                'referer': validator.field(
                    validator.schema.str_schema(),
                    default='',
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_multimedia_edit(
                level_id,
                data["txt"],
                referer=data["referer"],
                course_id=data["course_id"],
                level_index=data["level_index"],
            )
        )


class level_removerow:
    def POST(self, level_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                'thing_id': validator.field(
                    validator.schema.int_schema(),
                ),
                'referer': validator.field(
                    validator.schema.str_schema(),
                    default='',
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_thing_remove(
                level_id,
                data["thing_id"],
                referer=data["referer"],
            )
        )
