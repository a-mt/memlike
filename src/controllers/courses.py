import web
import variables
from memrise import memrise

# fmt: off
urls = (
    r"", "courses",
    r"/(.*)", "courses",
)
# fmt: on

class courses:
    def GET(self, path=""):
        _GET = web.input(q="")

        # ex https://community-courses.memrise.com/de/community/courses/arabic/swedish/
        # [path: arabic/swedish] = swedish courses for users that speak arabic
        parts = path.strip('/').split('/')
        lang  = parts[0]
        cat   = ""
        catId = ""

        # Filter courses in a given language
        # "I speak..." (french,german,arabic,etc)
        if lang == "":
            lang = web.ctx.session['lang']

        # Filter courses in a given category
        if len(parts) > 1 and parts[1] in variables.categories_code:
            cat   = parts[1]
            catId = variables.categories_code[cat]

        # Retrieve list of categories that have a course
        catHaveCourse = memrise.categories(lang)
        return web.config.template.render.courses({
            "lang"  : lang,
            "cat"   : cat,
            "catId" : catId,
            "q"     : _GET.q,
        }, variables.languages, variables.categories, catHaveCourse)

app = web.application(urls, locals(), autoreload=False)
