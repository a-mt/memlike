import settings
import web
from os import getenv
from memrise import memrise
from requests.exceptions import HTTPError

urls = (
  # Learn
  r"/(\d+)/(.*)/(\d+)/garden", "learn_fromform",
  r"/(\d+)/(.*)/(\d+)/(\d+)", "view",
  r"/(\d+)/(.*)/(\d+)/(.*)", "level",
  r"/(\d+)/(.*)/(\d+)", "level",

  # View course
  r"/(\d+)/(.*)/garden", "learn_fromform",
  r"/(\d+)/(.*)/garden/(preview|learn|classic_review|speed_review)", "learn",
  r"/(\d+)/(.*)/leaderboard", "leaderboard",
  r"/(\d+)/([^/]*)/edit", "edit",
  r"/(\d+)/(.*)", "course",
  r"/(\d+)", "course"
)

class learn_fromform:
    def GET(self, idCourse, path, lvl=False):
        _GET = web.input(session="", sendresults=0)

        try:
            course = memrise.course(idCourse)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.learn(course, _GET.session, lvl, False, _GET.sendresults)

class learn:
    def GET(self, idCourse, path, lvl, kind=False):
        if not kind:
            kind = lvl
            lvl  = False
        try:
            course = memrise.course(idCourse)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.learn(course, kind, lvl, False, 1)

class view:
    def GET(self, idCourse, path, lvl, thing):
        try:
            course = memrise.course(idCourse)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.learn(course, "preview", lvl, thing, 0)

class level:
    def GET(self, idCourse, slugCourse, lvl, path2=""):
        try:
            course = memrise.course(idCourse)
            if lvl not in course['levels']:
                return web.config.template.prender._404()

            try:
                if course['levels'][lvl]['type'] == 1:
                    sessionid = False
                    csrftoken = None

                    if web.ctx.session.get('loggedin', False):
                        sessionid = web.ctx.session['loggedin']['sessionid']
                        csrftoken = web.ctx.session['loggedin']['csrftoken']

                    items = memrise.level(idCourse, slugCourse, lvl, "preview", sessionid, csrftoken)
                else:
                    # Type multimedia
                    items = memrise.level_multimedia(course['url'], lvl)
            except HTTPError as e:
                items = {"learnables":[], "progress":[]}

        except HTTPError as e:
            if e.response.status_code == 403:
                return web.config.template.prender._403()
            else:
                return web.config.template.prender._404()

        return web.config.template.render.course_level(course, {
            "name": course['levels'][lvl]['name'],
            "type": course['levels'][lvl]['type'],
            "index": int(lvl)
        }, items)

class course:
    def GET(self, idCourse, slugCourse=""):
        learning = False
        items    = False
        try:
            sessionid = False
            csrftoken = None

            if web.ctx.session.get('loggedin', False):
                sessionid = web.ctx.session['loggedin']['sessionid']
                csrftoken = web.ctx.session['loggedin']['csrftoken']

            course = memrise.course(idCourse, sessionid, csrftoken)

            # Course without any level ?
            if len(course["levels"]) == 0:
                items = memrise.level(idCourse, slugCourse, "1", "preview", sessionid, csrftoken)

        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        if items:
            return web.config.template.render.course_level(course, {
                "name": False,
                "type": 1,
                "index": -1
            }, items)

        return web.config.template.render.course_summary(course)

class leaderboard:
    def GET(self, idCourse, path=""):
        _GET = web.input(period="week")
        try:
            course      = memrise.course(idCourse)
            leaderboard = memrise.leaderboard(idCourse, _GET.period)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.course_leaderboard(course, _GET.period, leaderboard)

class edit:
    def GET(self, idCourse, path):
        if not web.ctx.session.get('loggedin', False):
            raise web.Forbidden()

        sessionid = web.ctx.session['loggedin']['sessionid']
        try:
            course = memrise.course_edit(sessionid, idCourse, path)
        except HTTPError as e:
            print(e)
            return web.config.template.prender._404()

        return web.config.template.render.course_edit(course)

app = web.application(urls, locals(), autoreload=False)
