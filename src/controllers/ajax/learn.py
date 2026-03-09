import json
import settings
import web
from math import ceil
from memrise import memrise
from requests.exceptions import HTTPError
from utils.ajax import proxied_response


class learning_session_register_progress:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = web.jsoninput()
        progress = memrise.learning_session_register_progress(data)
        return proxied_response(lambda: progress)


class learning_session_register_end:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = web.jsoninput()
        progress = memrise.learning_session_register_end(data)
        return proxied_response(lambda: progress)


class reset_progress_level:
    def POST(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        data = web.jsoninput()
        response = memrise.reset_progress_level(data)
        return proxied_response(lambda: response)

