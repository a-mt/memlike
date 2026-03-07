import web
from memrise import memrise
from requests.exceptions import HTTPError

# fmt: off
urls = (
    # Learn
    # /6687517/german-vocab/1/garden
    # /6618687/tables-de-multiplication/0/28918327345410
    r"/(\d+)/(.*)/(\d+)/garden", "learn_fromform",
    r"/(\d+)/(.*)/(\d+)/reset", "reset_progress_level",
    r"/(\d+)/(.*)/(\d+)/(\d+)", "view",
    r"/(\d+)/(.*)/(\d+)/(.*)", "level",
    r"/(\d+)/(.*)/(\d+)", "level",

    # View course
    r"/(\d+)/(.*)/garden", "learn_fromform",
    r"/(\d+)/(.*)/garden/(preview|learn|classic_review|speed_review)", "learn",
    r"/(\d+)/(.*)/leaderboard", "leaderboard",
    r"/(\d+)/([^/]*)/edit", "edit",
    r"/(\d+)/(.*)", "course",
    r"/(\d+)", "course",
)
# fmt: on


class learn_fromform:
    def GET(self, course_id, path, level_index=False):
        course_slug = path.split("/", 2)[0]

        _GET = web.input(session="", save_progress=0, reverse_prompt_and_answer=0)
        if not _GET.session:
            raise web.seeother(f"/course/{course_id}/{course_slug}/", absolute=True)

        try:
            course = memrise.course(course_id, course_slug=course_slug)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.learn(
            course,
            _GET.session,
            level_index,
            False,
            _GET.save_progress,
            _GET.reverse_prompt_and_answer,
        )


class learn:
    def GET(self, course_id, path, level_index, session_type=False):
        course_slug = path.split("/", 2)[0]

        if not session_type:
            session_type = level_index
            level_index = False
        try:
            course = memrise.course(course_id, course_slug=course_slug)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.learn(course, session_type, level_index, False, 1)


class view:
    def GET(self, course_id, path, level_index, thing_id):
        course_slug = path.split("/", 2)[0]

        try:
            course = memrise.course(course_id, course_slug=course_slug)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.learn(course, "preview", level_index, thing_id, 0)


class level:
    def gotoCourse(self, course_id, course_slug, level_index):
        web.add_flash_message(
            f"Could not retrieve the requested level ({level_index})",
            level=web.config.FLASH_MESSAGES_TAGS.ERROR,
        )
        raise web.seeother(f"/course/{course_id}/{course_slug}/", absolute=True)

    def GET(self, course_id, course_slug, level_index, path2=""):
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
            try:
                if level["type"] == 1:
                    # A list of things
                    items = memrise.level(course_id, course_slug, index, "preview")
                else:
                    # A multimedia
                    items = memrise.level_multimedia(course_id, course_slug, index)

            except HTTPError:
                items = {"learnables": [], "progress": []}

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
        items = False
        try:
            course = memrise.course(course_id, course_slug)

            # Course without any level ?
            if len(course["levels"]) == 0:
                items = memrise.level(course_id, course_slug, "1", "preview")

        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

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


class leaderboard:
    def GET(self, course_id, path=""):
        course_slug = path.split("/", 2)[0]

        _GET = web.input(period="week")
        try:
            course = memrise.course(course_id, course_slug=course_slug)
            leaderboard = memrise.course_leaderboard(course_id, _GET.period)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.course_leaderboard(course, _GET.period, leaderboard)


class edit:
    def GET(self, course_id, path):
        course_slug = path.split("/", 2)[0]

        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        try:
            course = memrise.course_edit_get(course_id, course_slug=course_slug)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.course_edit(course)


class reset_progress_level:
    def GET(self, course_id, path, level_index):
        # Note that the URL parameters are use to redirec to the course
        # Wgile the GET parameters are used to reset the progress
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _GET = web.input(level_id="")
        if _GET.level_id:
            try:
                memrise.reset_progress_level({"level_id": _GET.level_id})
            except HTTPError as e:
                print(e)

        raise web.seeother(f"/course/{course_id}/{path}/{level_index}", absolute=True)


app = web.application(urls, locals(), autoreload=False)
