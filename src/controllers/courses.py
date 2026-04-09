import web
import variables
import settings
from utils import validator
from lang import get_localized_languages
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
                "q": validator.field(
                    validator.schema.str_schema(),
                    default="",
                    on_error="default",
                ),
            },
            data=web.input(),
        )
        _GET = web.storage(input_data)

        # ex https://community-courses.memrise.com/de/community/courses/arabic/swedish/
        # [path: arabic/swedish] = swedish courses for users that speak arabic
        parts = path.strip("/").split("/")
        lang_slug = parts[0]
        cat_slug = ""
        cat_id = ""

        # Filter courses in a given language
        # "I speak..." (french,german,arabic,etc)
        if lang_slug == "":
            lang_slug = web.ctx.session.get("lang_slug", settings.DEFAULT_LANG_SLUG)

        # Filter courses in a given category
        if len(parts) > 1 and parts[1] in variables.categories_slug:
            cat_slug = parts[1]
            cat_id = variables.categories_slug[cat_slug]["id"]

        # Retrieve list of categories that have a course
        categories_to_display = memrise.categories_to_display(lang_slug)
        return web.config.template.render.courses(
            {
                "lang": lang_slug,
                "cat": cat_slug,
                "catId": cat_id,
                "q": _GET.q,
            },
            get_localized_languages(),
            variables.categories_tree,
            categories_to_display,
        )


app = web.application(urls, locals(), autoreload=False)
