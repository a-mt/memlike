import web
from memrise import memrise
from utils.webapi import proxied_response
from utils import validator
from variables import categories_code, languages
from pydantic_core import PydanticCustomError


def is_valid_lang(value):
    if value not in languages or value not in categories_code:
        raise PydanticCustomError(
            "invalid",
            "Expected a valid language, got '{wrong_value}'",
            {"wrong_value": value},
        )
    return categories_code[value]


class course_add:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = web.input()
        input_data = validator.validate(
            fields={
                "name": validator.field(
                    validator.schema.str_schema(min_length=1),
                ),
                "category": validator.field(
                    validator.schema.int_schema(),
                ),
                "language": validator.field(
                    validator.schema.str_schema(),
                    validator=is_valid_lang,
                ),
                "tags": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
                "description": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
                "short_description": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=data,
        )
        return proxied_response(lambda: memrise.course_add(input_data))


class course_editpage:
    def GET(self, course_id, course_slug):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        return proxied_response(lambda: memrise.course_get_editpage(course_id, course_slug))


class course_editdetails:
    def GET(self, course_id, course_slug):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        return proxied_response(lambda: memrise.course_get_editdetails(course_id, course_slug))

    def POST(self, course_id, course_slug):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "name": validator.field(
                    validator.schema.str_schema(min_length=1),
                ),
                "course_status": validator.field(
                    validator.schema.int_schema(),
                ),
                "target": validator.field(
                    validator.schema.str_schema(),
                ),
                "source": validator.field(
                    validator.schema.str_schema(),
                ),
                "tags": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
                "description": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
                "short_description": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
                "audio_mode": validator.field(
                    validator.schema.bool_schema(),
                ),
                "csrfmiddlewaretoken": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=web.input(),
        )
        return proxied_response(lambda: memrise.course_editdetails(course_id, course_slug, data))


class level_add:
    def POST(self, *args, **kwargs):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "course_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "pool_id": validator.field(
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
                "level_id": validator.field(
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


class level_get_editpage:
    def GET(self, level_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        return proxied_response(lambda: memrise.level_get_editpage(level_id))


class level_title_edit:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "level_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "title": validator.field(
                    validator.schema.str_schema(),
                ),
            },
            data=web.input(),
        )
        return proxied_response(lambda: memrise.level_title_edit(data["level_id"], data["title"]))


class level_columns_direction_edit:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "level_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "column_a": validator.field(
                    validator.schema.str_schema(),
                ),
                "column_b": validator.field(
                    validator.schema.str_schema(),
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_columns_direction_edit(
                data["level_id"],
                data["column_a"],
                data["column_b"],
            )
        )


class level_column_edit:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "pool_id": validator.field(
                    validator.schema.str_schema(),
                ),
                "column_key": validator.field(
                    validator.schema.str_schema(),
                ),
                "label": validator.field(
                    validator.schema.str_schema(),
                ),
                "show_at_tests": validator.field(
                    validator.schema.bool_schema(),
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_column_edit(
                data["pool_id"],
                data["column_key"],
                data["label"],
                data["show_at_tests"],
            )
        )


class level_column_delete:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "pool_id": validator.field(
                    validator.schema.str_schema(),
                ),
                "column_key": validator.field(
                    validator.schema.str_schema(),
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_column_delete(
                data["pool_id"],
                data["column_key"],
            )
        )


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


class level_thing_add:
    def POST(self, level_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "data": validator.field(
                    validator.schema.str_schema(),
                ),
                "referer": validator.field(
                    validator.schema.str_schema(),
                    default="",
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


class level_thing_update:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "cell_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "cell_value": validator.field(
                    validator.schema.str_schema(),
                ),
                "referer": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_thing_update(
                thing_id,
                data["cell_id"],
                data["cell_value"],
                referer=data["referer"],
            )
        )


class level_thing_file_upload:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        values = web.input(file={})

        data = validator.validate(
            fields={
                "cell_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "file": validator.field(
                    validator.file_schema(),
                ),
                "referer": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=values,
        )
        return proxied_response(
            lambda: memrise.level_thing_file_upload(
                thing_id,
                data["cell_id"],
                data["file"],
                referer=data["referer"],
            )
        )


class level_thing_file_upload_compat:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "thing_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "cell_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "f": validator.field(
                    validator.file_schema(),
                ),
                "referer": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
                "csrfmiddlewaretoken": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=web.input(f={}),
        )

        return proxied_response(
            lambda: memrise.level_thing_file_upload(
                data["thing_id"],
                data["cell_id"],
                data["f"],
                referer=data["referer"],
                csrftoken=data["csrfmiddlewaretoken"],
            )
        )


class level_thing_file_delete:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "cell_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "file_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "referer": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_thing_file_delete(
                thing_id,
                data["cell_id"],
                data["file_id"],
                referer=data["referer"],
            )
        )


class level_thing_alt:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "referer": validator.field(
                    validator.schema.str_schema(),
                    default="",
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


class level_thing_alt_update:
    def POST(self, thing_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "cell_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "alts": validator.field(
                    validator.schema.str_schema(),
                ),
                "referer": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_thing_alt_update(
                thing_id,
                data["alts"],
                data["cell_id"],
                referer=data["referer"],
            )
        )


class level_multimedia_update:
    def POST(self, level_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "course_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "level_index": validator.field(
                    validator.schema.int_schema(),
                ),
                "txt": validator.field(
                    validator.schema.str_schema(),
                ),
                "referer": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_multimedia_update(
                level_id,
                data["txt"],
                referer=data["referer"],
                course_id=data["course_id"],
                level_index=data["level_index"],
            )
        )


class level_thing_delete:
    def POST(self, level_id):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = validator.validate(
            fields={
                "thing_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "referer": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=web.input(),
        )
        return proxied_response(
            lambda: memrise.level_thing_delete(
                level_id,
                data["thing_id"],
                referer=data["referer"],
            )
        )


class course_delete:
    def POST(self, course_id, course_slug, **kwargs):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        return proxied_response(
            lambda: memrise.course_delete(
                course_id=course_id,
                csrftoken=web.ctx.env.get("HTTP_X_CSRFTOKEN", None),
                referer=web.ctx.env.get("HTTP_X_REFERER", None),
            )
        )


class course_picture_upload:
    def POST(self, course_id, course_slug, **kwargs):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        values = web.input(image_file={})

        data = validator.validate(
            fields={
                "image_file": validator.field(
                    validator.file_schema(),
                ),
                "csrfmiddlewaretoken": validator.field(
                    validator.schema.str_schema(),
                    default="",
                ),
            },
            data=values,
        )
        return proxied_response(
            lambda: memrise.course_picture_upload(
                course_id=course_id,
                file=data["image_file"],
                csrftoken=data.get("csrfmiddlewaretoken", ""),
            )
        )
