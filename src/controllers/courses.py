import web
import variables
import settings
from utils import validator
from memrise import memrise

# fmt: off
urls = (
    r"", "courses",
    r"/(.*)", "courses",
)
# fmt: on


class courses:
    def GET(self, path=""):
        input_data = validator.validate(
            fields={
                'q': validator.field(
                    validator.schema.str_schema(),
                    default='',
                    on_error='default',
                ),
            },
            data=web.input(),
        )
        _GET = web.storage(input_data)

        # ex https://community-courses.memrise.com/de/community/courses/arabic/swedish/
        # [path: arabic/swedish] = swedish courses for users that speak arabic
        parts = path.strip("/").split("/")
        lang_slug = parts[0]
        cat = ""
        catId = ""

        # Filter courses in a given language
        # "I speak..." (french,german,arabic,etc)
        if lang_slug == "":
            lang_slug = web.ctx.session.get("lang_slug", settings.DEFAULT_LANG_SLUG)

        # Filter courses in a given category
        if len(parts) > 1 and parts[1] in variables.categories_code:
            cat = parts[1]
            catId = variables.categories_code[cat]

        # Retrieve list of categories that have a course
        has_courses = memrise.categories(lang_slug)
        return web.config.template.render.courses(
            {
                "lang": lang_slug,
                "cat": cat,
                "catId": catId,
                "q": _GET.q,
            },
            variables.languages,
            variables.categories,
            has_courses,
        )


app = web.application(urls, locals(), autoreload=False)
