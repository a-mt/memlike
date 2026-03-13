from requests.exceptions import HTTPError
import json
import logging
import web


logger = logging.getLogger(__name__)


def jsoninput():
    """
    Helper to read the JSON body of the current request
    """
    if web.ctx.env.get("CONTENT_TYPE", "").lower() != "application/json":
        return

    text = web.data()
    return json.loads(text)


def error_response(e):
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
        return error_response(e)

    return json_response(data)


def json_response(data):
    web.header("Content-Type", "application/json")
    if isinstance(data, str):
        return data
    else:
        return json.dumps(data)
