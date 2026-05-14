import datetime
import decimal
import json
import uuid
import logging
import web
from pydantic_core import ValidationError
from requests.exceptions import HTTPError


logger = logging.getLogger(__name__)


def jsoninput():
    """
    Helper to read the JSON body of the current request
    """
    if web.ctx.env.get("CONTENT_TYPE", "").lower() != "application/json":
        return

    try:
        text = web.data()
        return json.loads(text)

    except json.decoder.JSONDecodeError as e:
        raise ValidationError.from_exception_data(
            "invalid",
            [
                {
                    "msg": "Input data could not be decoded",
                    "type": "json_invalid",
                    # "loc": [],
                    # "input": None,
                    "ctx": {"error": str(e)},
                }
            ],
        )


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
        return json.dumps(data, cls=DjangoJSONEncoder)


def add_flash_message(message, level=web.config.FLASH_MESSAGES_TAGS.INFO):
    web.ctx.session = web.ctx.get("session", None) or web.storage({})

    web.ctx.session.flash = web.ctx.session.get("flash", None) or web.storage({})

    web.ctx.session.flash.messages = web.ctx.session.flash.get("messages", None) or []

    web.ctx.session.flash.messages.append(
        {
            "message": message,
            "level": level,
        }
    )



class DjangoJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types, and
    UUIDs.
    """

    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith("+00:00"):
                r = r.removesuffix("+00:00") + "Z"
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            if is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, datetime.timedelta):
            return str(o)
        elif isinstance(o, (decimal.Decimal, uuid.UUID)):
            return str(o)
        elif type(o).__module__:
            return str(type(o))
        else:
            return super().default(o)
