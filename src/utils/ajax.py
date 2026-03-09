import json
import web
from requests.exceptions import HTTPError


def _error(e):
    # https://github.com/webpy/webpy/blob/master/web/webapi.py#L15
    if e.response.status_code == 403:
        return web.Unauthorized()
    elif e.response.status_code == 404:
        return web.NotFound()
    else:
        print(e)
        # traceback.print_exc()
        return web.NotFound()


def proxied_response(call):
    try:
        data = call()
    except HTTPError as e:
        return _error(e)

    return json_response(data)


def json_response(data):
    web.header("Content-Type", "application/json")
    if isinstance(data, str):
        return data
    else:
        return json.dumps(data)
