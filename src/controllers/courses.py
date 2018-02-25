from variables import *
import web
from memrise import memrise
from _globals import GLOBALS

urls = (
  "", "courses",
  "/(.*)", "courses"
)

class courses:
    def GET(self, path=""):
        _GET = web.input(q="")

        parts = path.strip('/').split('/')
        lang  = parts[0]
        cat   = ""
        catId = ""

        # Filter courses in a given language
        if lang == "":
            lang = GLOBALS['session'].lang

        # Filter courses in a given category
        if len(parts) > 1 and parts[1] in categories_code:
            cat   = parts[1]
            catId = categories_code[cat]

        # Retrieve list of categories that have a course
        catHaveCourse = memrise.categories(lang)

        return GLOBALS['render'].courses({
            "lang"  : lang,
            "cat"   : cat,
            "catId" : catId,
            "q"     : _GET.q
        }, languages, categories, catHaveCourse)

app = web.application(urls, locals())