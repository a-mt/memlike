import logging
import json
import web


logger = logging.getLogger(__name__)


# Helper for controllers: read JSON body
def jsoninput():
    if web.ctx.env.get("CONTENT_TYPE", "").lower() != "application/json":
        return

    text = web.data()
    return json.loads(text)
