import web
import settings
import variables
from lang import get_localized_languages
from utils.webapi import add_flash_message
from utils import validator
from memrise import memrise
from requests.exceptions import HTTPError
from pydantic_core import PydanticCustomError, ValidationError


# fmt: off
urls = (
    # Learn
    # /6687517/german-vocab/1/garden
    # /6618687/tables-de-multiplication/0/28918327345410
    r"/(\d+)/(.*)/(\d+)/garden", "learn_fromform",
    r"/(\d+)/(.*)/(\d+)/reset", "reset_progress_level",
    r"/(\d+)/(.*)/(\d+)/(\d+)", "thing",
    r"/(\d+)/(.*)/(\d+)/(.*)", "level",
    r"/(\d+)/(.*)/(\d+)", "level",

    # View course
    r"/(\d+)/(.*)/garden", "learn_fromform",
    r"/(\d+)/(.*)/garden/(preview|learn|review|classic_review|speed_review)", "learn",
    r"/(\d+)/(.*)/leaderboard", "leaderboard",
    r"/(\d+)/(.*)/spreadsheet", "spreadsheet",
    r"/(\d+)/([^/]*)/edit", "course_get_editpage",
    r"/(\d+)/(.*)", "course",
    r"/add", "course_add",
    #r"/(\d+)", "course",
)
# fmt: on


class learn_fromform:
    def GET(self, course_id, path, level_index=False):
        course_slug = path.split("/", 2)[0]

        input_data = validator.validate(
            fields={
                "session_type": validator.field(
                    validator.str_choices_schema(["preview", "learn", "review", "classic_review", "speed_review"]),
                    default="preview",
                    on_error="default",
                ),
                "save_progress": validator.field(
                    validator.schema.bool_schema(),
                    default=False,
                    on_error="default",
                ),
                "reverse_prompt_and_answer": validator.field(
                    validator.schema.bool_schema(),
                    default=False,
                    on_error="default",
                ),
                "build_strategy": validator.field(
                    validator.str_choices_schema(["", "0", "1"]),
                    default="",
                    on_error="default",
                ),
            },
            data=web.input(),
        )

        _GET = web.storage(input_data)
        if not _GET.session_type:
            raise web.seeother(f"/community/course/{course_id}/{course_slug}/", absolute=True)

        course = memrise.course(course_id, course_slug=course_slug)

        return web.config.template.render.learn(
            course,
            _GET.session_type,
            level_index,
            False,
            _GET.save_progress,
            _GET.reverse_prompt_and_answer,
            _GET.build_strategy,
        )


class learn:
    def GET(self, course_id, path, level_index, session_type=False):
        course_slug = path.split("/", 2)[0]

        if not session_type:
            session_type = level_index
            level_index = False

        course = memrise.course(course_id, course_slug=course_slug)

        return web.config.template.render.learn(course, session_type, level_index, False, 1, 0, 1)


class thing:
    def GET(self, course_id, path, level_index, thing_id):
        course_slug = path.split("/", 2)[0]
        course = memrise.course(course_id, course_slug=course_slug)

        return web.config.template.render.learn(course, "preview", level_index, thing_id, 0, 0, 1)


class level:
    def gotoCourse(self, course_id, course_slug, level_index):
        course_slug = course_slug.split("/", 2)[0]

        add_flash_message(
            f"Could not retrieve the requested level ({level_index})",
            level=web.config.FLASH_MESSAGES_TAGS.ERROR,
        )
        raise web.seeother(f"/community/course/{course_id}/{course_slug}/", absolute=True)

    def GET(self, course_id, course_slug, level_index, path=""):
        course_slug = course_slug.split("/", 2)[0]
        try:
            course = memrise.course(course_id, course_slug)
            index = int(level_index)

            # Check that the giving level index is known
            if index <= 1 and not len(course["levels"]):
                index = 1
                level = {
                    "name": "",
                    "type": 1,
                }
            else:
                if level_index not in course["levels"]:
                    return self.gotoCourse(course_id, course_slug, level_index)

                level = course["levels"][level_index]

            # Request the content of that level
            if level["type"] == 1:
                # A list of things
                try:
                    items = memrise.level(course_id, course_slug, index, "preview")
                except HTTPError:
                    items = {"learnables": [], "progress": []}
            else:
                # A multimedia
                try:
                    items = memrise.level_multimedia(course_id, course_slug, index)
                except HTTPError:
                    items = ""

        except HTTPError as e:
            if e.response.status_code == 403:
                return web.config.template.prender._403()
            else:
                # The level doesn't exist: go to the course's page
                if course:
                    return self.gotoCourse(course_id, course_slug, level_index)

                return web.config.template.prender._404()

        # Render the level content
        return web.config.template.render.course_level(
            course,
            {
                "name": level["name"],
                "type": level["type"],
                "index": index,
            },
            items,
        )


class course:
    def GET(self, course_id, course_slug=""):
        course_slug = course_slug.split("/", 2)[0]
        course = memrise.course(course_id, course_slug)

        items = False
        try:
            # Course without any level ?
            if len(course["levels"]) == 0:
                items = memrise.level(course_id, course_slug, "1", "preview")

        except HTTPError as e:
            print(e)

        if items:
            return web.config.template.render.course_level(
                course,
                {
                    "name": False,
                    "type": 1,
                    "index": 1,
                },
                items,
            )

        return web.config.template.render.course_summary(course)


class spreadsheet:
    def GET(self, course_id, course_slug=""):
        course_slug = course_slug.split("/", 2)[0]
        course = memrise.course(course_id, course_slug)

        selectboxes = {"0": "", "1": ""}

        for rank, level in course.get("levels", []).items():
            k = "1" if level["type"] == 2 else "0"

            selectboxes[k] += f"<option value='{rank}' selected>{rank}. {level['name']}</option>"

        return web.config.template.render.course_spreadsheet(course, selectboxes)


class leaderboard:
    def GET(self, course_id, path=""):
        course_slug = path.split("/", 2)[0]

        input_data = validator.validate(
            fields={
                "period": validator.field(
                    validator.str_choices_schema(["month", "week", "alltime"]),
                    default="week",
                    on_error="default",
                ),
            },
            data=web.input(),
        )

        _GET = web.storage(input_data)

        course = memrise.course(course_id, course_slug=course_slug)
        leaderboard = memrise.course_leaderboard(course_id, _GET.period)

        return web.config.template.render.course_leaderboard(course, _GET.period, leaderboard)


class course_get_editpage:
    def GET(self, course_id, path):
        course_slug = path.split("/", 2)[0]

        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        course = memrise.course_get_editpage(course_id, course_slug=course_slug)

        return web.config.template.render.course_edit(course, variables.categories_tree, get_localized_languages())


class reset_progress_level:
    def GET(self, course_id, path, level_index):
        # Note that the URL parameters are use to redirec to the course
        # Wgile the GET parameters are used to reset the progress
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        input_data = validator.validate(
            fields={
                "level_id": validator.field(
                    validator.schema.int_schema(),
                    default="",
                    on_error="default",
                ),
            },
            data=web.input(),
        )

        _GET = web.storage(input_data)
        if _GET.level_id:
            try:
                memrise.reset_progress_level({"level_id": _GET.level_id})
            except HTTPError as e:
                print(e)

        raise web.seeother(f"/community/course/{course_id}/{path}/{level_index}", absolute=True)


class course_add:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = web.ctx.flash.get("data", {})

        if "language" not in data and web.ctx.get("session", {}):
            data["language"] = web.ctx.session.get("lang_slug", settings.DEFAULT_LANG_SLUG)

        return web.config.template.render.course_add(variables.categories_tree, get_localized_languages(), data=data)

    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        def check_lang_category_id(value):
            if value not in variables.source_languages or value not in variables.categories_slug:
                raise PydanticCustomError(
                    "invalid",
                    "Expected a valid language, got '{wrong_value}'",
                    {"wrong_value": value},
                )
            return variables.categories_slug[value]["id"]

        try:
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
                        validator=check_lang_category_id,
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
            data = memrise.course_add(input_data)

            # f"/community/course/{course_id}/{course_slug}/"
            raise web.seeother(data["url"], absolute=True)

        except ValidationError as e:
            web.ctx.session.flash = {"err": {".".join(x["loc"]): x for x in e.errors()}, "data": data}

            web.ctx.status = "400 Bad Request"

            return course_add().GET()

        raise web.seeother("add", absolute=False)


app = web.application(urls, locals(), autoreload=False)
