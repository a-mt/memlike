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
    def GET(self, idCourse, path, lvl=False):
        slugCourse = path.split("/", 2)[0]

        _GET = web.input(session="", sendresults=0)
        if not _GET.session:
            raise web.seeother(f"/course/{idCourse}/{slugCourse}/", absolute=True)

        try:
            course = memrise.course(idCourse, slugCourse=slugCourse)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.learn(course, _GET.session, lvl, False, _GET.sendresults)


class learn:
    def GET(self, idCourse, path, lvl, kind=False):
        slugCourse = path.split("/", 2)[0]

        if not kind:
            kind = lvl
            lvl = False
        try:
            course = memrise.course(idCourse, slugCourse=slugCourse)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.learn(course, kind, lvl, False, 1)


class view:
    def GET(self, idCourse, path, lvl, thing):
        slugCourse = path.split("/", 2)[0]

        try:
            course = memrise.course(idCourse, slugCourse=slugCourse)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.learn(course, "preview", lvl, thing, 0)


class level:
    def gotoCourse(self, idCourse, slugCourse, lvl):
        web.add_flash_message(
            f"Could not retrieve the requested level ({lvl})",
            level=web.config.FLASH_MESSAGES_TAGS.ERROR,
        )
        raise web.seeother(f"/course/{idCourse}/{slugCourse}/", absolute=True)

    def GET(self, idCourse, slugCourse, lvl, path2=""):
        try:
            course = memrise.course(idCourse, slugCourse)
            index = int(lvl)

            # Check that the giving level index is known
            if index <= 1 and not len(course["levels"]):
                index = 1
                level = {
                    "name": "",
                    "type": 1,
                }
            else:
                if lvl not in course["levels"]:
                    return self.gotoCourse(idCourse, slugCourse, lvl)

                level = course["levels"][lvl]

            # Request the content of that level
            try:
                if level["type"] == 1:
                    # A list of things
                    items = memrise.level(idCourse, slugCourse, index, "preview")
                else:
                    # A multimedia
                    items = memrise.level_multimedia(idCourse, slugCourse, index)

            except HTTPError:
                items = {"learnables": [], "progress": []}

        except HTTPError as e:
            if e.response.status_code == 403:
                return web.config.template.prender._403()
            else:
                # The level doesn't exist: go to the course's page
                if course:
                    return self.gotoCourse(idCourse, slugCourse, lvl)

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
    def GET(self, idCourse, slugCourse=""):
        items = False
        try:
            course = memrise.course(idCourse, slugCourse)

            # Course without any level ?
            if len(course["levels"]) == 0:
                items = memrise.level(idCourse, slugCourse, "1", "preview")

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
    def GET(self, idCourse, path=""):
        slugCourse = path.split("/", 2)[0]

        _GET = web.input(period="week")
        try:
            course = memrise.course(idCourse, slugCourse=slugCourse)
            leaderboard = memrise.course_leaderboard(idCourse, _GET.period)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.course_leaderboard(course, _GET.period, leaderboard)


class edit:
    def GET(self, idCourse, path):
        slugCourse = path.split("/", 2)[0]

        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        try:
            course = memrise.course_edit_get(idCourse, slugCourse=slugCourse)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.course_edit(course)


class reset_progress_level:
    def GET(self, idCourse, path, lvl):
        if not web.ctx.session.get("loggedin", False):
            raise web.Forbidden()

        _GET = web.input(level_id="")
        if _GET.level_id:
            try:
                memrise.reset_progress_level({"level_id": _GET.level_id})
            except HTTPError as e:
                print(e)

        raise web.seeother(f"/course/{idCourse}/{path}/{lvl}", absolute=True)


app = web.application(urls, locals(), autoreload=False)
