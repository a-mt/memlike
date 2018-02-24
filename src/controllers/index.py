import web
from _globals import GLOBALS

urls = (
  "", "index"
)

class index:
    def GET(self):
        return GLOBALS['render'].index()

app = web.application(urls, locals())