import web
from memrise import memrise
from utils.webapi import proxied_response, jsoninput
from utils import validator


class learning_session_register_progress:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = jsoninput() or web.input()
        validator.validate(
            fields={
                "events": validator.field(
                    validator.schema.list_schema(),
                ),
                "sync_token": validator.field(
                    validator.schema.int_schema(),
                    default=0,
                ),
                "limit": validator.field(
                    validator.schema.int_schema(),
                    default=0,
                ),
            },
            data=data,
        )
        progress = memrise.learning_session_register_progress(data)
        return proxied_response(lambda: progress)


class learning_session_register_end:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = jsoninput() or web.input()
        validator.validate(
            fields={
                "session_points": validator.field(
                    validator.schema.int_schema(),
                    default=0,
                ),
                "session_type": validator.field(
                    validator.str_choices_schema(["preview", "learn", "review", "classic_review", "speed_review"]),
                ),
                "session_source_type": validator.field(
                    validator.str_choices_schema(["course", "course_id_and_level_index"]),
                ),
                "session_source_id": validator.field(
                    validator.schema.int_schema(),
                ),
                "session_source_sub_index": validator.field(
                    validator.schema.int_schema(),
                    required=False,
                ),
            },
            data=data,
        )
        progress = memrise.learning_session_register_end(data)
        return proxied_response(lambda: progress)


class reset_progress_level:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = jsoninput() or web.input()
        validator.validate(
            fields={
                "level_id": validator.field(
                    validator.schema.int_schema(),
                ),
            },
            data=data,
        )
        response = memrise.reset_progress_level(data)
        return proxied_response(lambda: response)
