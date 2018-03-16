import web, json
from memrise import memrise
from requests.exceptions import HTTPError
from math import ceil
from _globals import GLOBALS

urls = (
  "", "api",

  "/courses", "courses",
  "/course/(\d+)/([^/]+)/(\d+)/media", "course_level_multimedia",
  "/course/(\d+)/([^/]+)/(\d+|all)/(preview|learn|classic_review|speed_review)", "course_level",
  "/course/(\d+)/([^/]+)/leaderboard", "course_leaderboard",
  "/course/(\d+)/([^/]+)", "course",

  "/user/([^/]+)", "user",
  "/user/([^/]+)/(followers)", "user_mempals",
  "/user/([^/]+)/(following)", "user_mempals",
  "/user/([^/]+)/(teaching)", "user_courses",
  "/user/([^/]+)/(learning)", "user_courses",

  # logged-in user only
  "/dashboard", "user_dashboard",
  "/leaderboard", "user_leaderboard",
  "/sync/(\d+)", "user_sync_course",
  "/sync", "user_sync",
  "/session", "debug_session"
)
NBPERPAGE = 15

class api:
    def GET(self):
        web.header('Content-Type', 'application/json')

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
            "user_sync_course": "/ajax/sync/{id} {cookies.sessionid}",
            "user_sync": "/ajax/sync {cookies.sessionid}",
            "debug_session": "/ajax/session"
        })

def _error(e):
    # https://github.com/webpy/webpy/blob/master/web/webapi.py#L15
    print e
    if e.response.status_code == 403:
        return web.Forbidden()
    else:
        return web.NotFound()

def _response(call):
    try:
        data = call()
    except HTTPError as e:
        return _error(e)

    web.header('Content-Type', 'application/json')
    if isinstance(data, basestring):
        return data
    else:
        return json.dumps(data)

def saveSession():
    if not GLOBALS['session'].get('_killed'):
        GLOBALS['session'].store[GLOBALS['session'].session_id] = dict(GLOBALS['session']._data)

class courses:
    def GET(self):
        _GET = web.input(lang=GLOBALS['session'].lang, cat="", q="", page=1)

        return _response(lambda: memrise.courses(_GET.lang, _GET.page, _GET.cat, _GET.q))

class course:
    def GET(self, idCourse, slug):
        return _response(lambda: memrise.course(idCourse))

class course_level:
    def GET(self, idCourse, slug, lvl, kind="preview"):
        _GET = web.input(session=False)

        sessionid = False
        if _GET.session:
            if not GLOBALS['session']['loggedin']:
                return web.Forbidden()
            sessionid = GLOBALS['session']['loggedin']['sessionid']

        return _response(lambda: memrise.level(idCourse, lvl, kind, sessionid))

class course_level_multimedia:
    def GET(self, idCourse, slug, lvl):
        try:
            data = memrise.level_multimedia("/course/" + idCourse + "/" + slug + "/", lvl)
        except HTTPError as e:
            return _error(e)

        web.header('Content-Type', 'text/plain')
        return data

class course_leaderboard:
    def GET(self, idCourse, slug):
        _GET = web.input(period="week")
        return _response(lambda: memrise.leaderboard(idCourse, _GET.period))

class user:
    def GET(self, username):
        return _response(lambda: memrise.user(username))

class user_mempals:
    def GET(self, username, tab):
        _GET = web.input(page=1)

        return _response(lambda: getattr(memrise, 'user_' + tab)(username, _GET.page))

class user_courses:
    def GET(self, username, tab):
        try:
            data = memrise.user_courses(tab, username)
        except HTTPError as e:
            return _error(e)

        web.header('Content-Type', 'application/json')

        # Pagination
        _GET = web.input(page=1)
        page = int(_GET.page)

        if not isinstance(page, int) and not page.isdigit():
            page = 1

        lastpage = int(ceil(data['nbCourse'] / NBPERPAGE) + 1)
        if page > lastpage:
            page = lastpage
        offset = (page-1)*NBPERPAGE

        data['lastpage'] = lastpage
        data['page']     = page
        data['has_next'] = page != lastpage
        data['content']  = data["content"][offset:offset+1+NBPERPAGE]

        return json.dumps(data)

class user_dashboard():
    def GET(self):
        if not GLOBALS['session']['loggedin']:
            raise web.Forbidden()

        web.header('Content-type','text/plain')
        web.header('Transfer-Encoding','chunked')

        sessionid = GLOBALS['session']['loggedin']['sessionid']
        offset    = 0
        c         = 0
        try:
            for courses in memrise.whatistudy(sessionid):
                yield json.dumps({"content": GLOBALS['prender'].ajax_dashboard(courses, offset)['__body__'] })
                offset += len(courses)

                # Take this opportunity to sync courses in session
                for course in courses:
                    data = {}
                    for k in ['num_things', 'learned', 'review', 'ignored', 'percent_complete']:
                        data[k] = course[k]

                    GLOBALS['session']['learning'][course['id']] = data
                    c += 1
                saveSession()

        except HTTPError as e:
            if e.response.status_code == 403:
                raise web.Forbidden()
            else:
                raise web.NotFound()

        except Exception as e:
            print(e)
            raise web.InternalError()

class user_leaderboard():
    def GET(self):
        if not GLOBALS['session']['loggedin']:
            raise web.Forbidden()

        sessionid = GLOBALS['session']['loggedin']['sessionid']
        _GET = web.input(period="week")
        return _response(lambda: memrise.user_leaderboard(sessionid, _GET.period))

class user_sync():
    def GET(self):
        c = 0

        if not GLOBALS['session']['loggedin']:
            raise web.Forbidden()

        sessionid = GLOBALS['session']['loggedin']['sessionid']
        for courses in memrise.whatistudy(sessionid):
            for course in courses:
                data = {}
                for k in ['num_things', 'learned', 'review', 'ignored', 'percent_complete']:
                    data[k] = course[k]

                GLOBALS['session']['learning'][course['id']] = data
                c += 1

        return str(c)

class user_sync_course():
    def GET(self, idCourse):
        if not GLOBALS['session']['loggedin']:
            raise web.Forbidden()

        sessionid = GLOBALS['session']['loggedin']['sessionid']
        data      = memrise.course_progress(idCourse, sessionid)

        GLOBALS['session']['learning'][idCourse] = data

class debug_session():
    def GET(self):
        web.header('Content-Type', 'application/json')
        return json.dumps(GLOBALS['session'].__dict__)

app = web.application(urls, locals())