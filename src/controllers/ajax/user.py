import json
import settings
import web
from math import ceil
from memrise import memrise
from requests.exceptions import HTTPError
from utils.ajax import proxied_response


NBPERPAGE = 15


class user:
    def GET(self, username):
        return proxied_response(lambda: memrise.user(username))


class user_mempals:
    def GET(self, username, tab):
        _GET = web.input(page=1)
        page = int(_GET.page)

        if not isinstance(page, int):
            page = int(page) if page.isdigit() else 1
        if page < 1:
            page = 1

        return proxied_response(lambda: getattr(memrise, "user_" + tab)(username, page))


class user_courses:
    def GET(self, username, tab):
        try:
            data = memrise.user_courses(tab, username)
        except HTTPError as e:
            return _error(e)

        web.header("Content-Type", "application/json")

        # Pagination
        _GET = web.input(page=1)
        page = int(_GET.page)

        if not isinstance(page, int):
            page = int(page) if page.isdigit() else 1
        if page < 1:
            page = 1

        lastpage = int(ceil(data["nb_courses"] / NBPERPAGE)) or 1
        if page > lastpage:
            page = lastpage
        offset = (page - 1) * NBPERPAGE

        data["lastpage"] = lastpage
        data["page"] = page
        data["has_next"] = page != lastpage
        data["content"] = data["content"][offset : offset + 1 + NBPERPAGE]

        return json.dumps(data)
