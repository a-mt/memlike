import json
import web
from math import ceil
from memrise import memrise
from requests.exceptions import HTTPError
from utils.ajax import proxied_response, error_response
from utils import validator


NBPERPAGE = 15


class user:
    def GET(self, username):
        return proxied_response(lambda: memrise.user(username))


class user_mempals:
    def GET(self, username, tab):
        input_data = validator.validate(
            fields={
                "page": validator.field(
                    validator.schema.int_schema(gt=0),
                    default=1,
                ),
            },
            data=web.input(),
        )

        _GET = web.storage(input_data)
        page = _GET.page

        return proxied_response(lambda: getattr(memrise, "user_" + tab)(username, page))


class user_courses:
    def GET(self, username, tab):
        try:
            data = memrise.user_courses(tab, username)
        except HTTPError as e:
            return error_response(e)

        web.header("Content-Type", "application/json")

        # Pagination
        input_data = validator.validate(
            fields={
                "page": validator.field(
                    validator.schema.int_schema(gt=0),
                    default=1,
                ),
            },
            data=web.input(),
        )
        _GET = web.storage(input_data)

        page = _GET.page
        lastpage = int(ceil(data["nb_courses"] / NBPERPAGE)) or 1
        if page > lastpage:
            page = lastpage
        offset = (page - 1) * NBPERPAGE

        data["lastpage"] = lastpage
        data["page"] = page
        data["has_next"] = page != lastpage
        data["content"] = data["content"][offset : offset + 1 + NBPERPAGE]

        return json.dumps(data)
