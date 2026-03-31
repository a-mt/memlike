import json
import web

from .courses import (
    courses,
    course,
    course_leaderboard,
    course_level,
    course_level_multimedia,
)
from .user import (
    user,
    user_mempals,
    user_courses,
)
from .profile import (
    user_dashboard,
    user_leaderboard,
    reload_user,
)
from .learn import (
    learning_session_register_progress,
    learning_session_register_end,
    reset_progress_level,
)
from .edit import (
    course_add,
    course_editpage,
    course_editdetails,
    level_add,
    level_delete,
    level_get_editpage,
    level_title_edit,
    level_columns_direction_edit,
    level_column_edit,
    level_column_add,
    level_column_delete,
    level_thing_alt,
    level_thing_alt_update,
    level_thing_add,
    level_thing_update,
    level_thing_delete,
    level_thing_file_upload,
    level_thing_file_upload_compat,
    level_thing_file_delete,
    level_multimedia_update,
    course_delete,
    course_picture_upload,
)
from .progress import my_progress


# fmt: off
# /ajax/level/...
urls_level = (
    r"/add", level_add,
    r"/delete", level_delete,
    r"/title_edit", level_title_edit,
    r"/columns_edit", level_columns_direction_edit,
    r"/column_edit", level_column_edit,
    r"/column_remove", level_column_delete,
    r"/column_add", level_column_add,
    r"/(\d+)", level_get_editpage,
    r"/(\d+)/alt", level_thing_alt,
    r"/(\d+)/alt_edit", level_thing_alt_update,
    r"/(\d+)/add", level_thing_add,
    r"/(\d+)/edit", level_thing_update,
    r"/(\d+)/remove", level_thing_delete,
    r"/(\d+)/upload", level_thing_file_upload,
    r"/(\d+)/upload_remove", level_thing_file_delete,
    r"/(\d+)/edit_multimedia", level_multimedia_update,
)

urls_thing = (
    r"/cell/upload_file", level_thing_file_upload_compat,
)

# /ajax/course/...
urls_course = (
    r"/(\d+)/([^/]+)/picture_upload", course_picture_upload,
    r"/(\d+)/([^/]+)/edit", course_editpage,
    r"/(\d+)/([^/]+)/details_edit", course_editdetails,
    r"/(\d+)/([^/]+)/(\d+)/media", course_level_multimedia,
    r"/(\d+)/([^/]+)/(\d+|all)/(preview|learn|classic_review|speed_review)", course_level,
    r"/(\d+)/([^/]+)/leaderboard", course_leaderboard,
    r"/(\d+)/([^/]+)", course,
    r"/add", course_add,
    r"/remove", course_delete,
)


urls = (
    r"/community/courses", courses,
    r"/community/course", course_app := web.application(urls_course, locals(), autoreload=False),
    r"/courses", courses,
    r"/course", course_app,
    r"/level", web.application(urls_level, locals(), autoreload=False),
    r"/thing", web.application(urls_thing, locals(), autoreload=False),

    r"/user/([^/]+)", user,
    r"/user/([^/]+)/(followers)", user_mempals,
    r"/user/([^/]+)/(following)", user_mempals,
    r"/user/([^/]+)/(teaching)", user_courses,
    r"/user/([^/]+)/(learning)", user_courses,

    # logged-in user only
    r"/dashboard", user_dashboard,
    r"/leaderboard", user_leaderboard,
    r"/progress", my_progress,
    r"/sync", reload_user,

    r"/register_progress", learning_session_register_progress,
    r"/register_end", learning_session_register_end,
    r"/reset_progress_level", reset_progress_level,

    r"/session", "debug_session",
    "", "index",
)
# fmt: on


class index:
    def GET(self):
        web.header("Content-Type", "application/json")

        # fmt: off
        patterns = {
            "courses": r"GET /ajax/courses?{lang, cat, q, page}",
            "course": r"GET /ajax/course/{course_id}/{course_slug}",
            "course_leaderboard": r"GET /ajax/course/{course_id}/{course_slug}/leaderboard?{period}",
            "course_level_preview": r"GET /ajax/course/{course_id}/{course_slug}/{level_index}/preview",
            "course_level_multimedia": r"GET /ajax/course/{course_id}/{course_slug}/{level_index}/media",
            "course_level_learn": r"GET /ajax/course/{course_id}/{course_slug}/{level_index}/learn {cookies.sessionid}",

            "user": r"GET /ajax/user/{username}",
            "user_followers": r"GET /ajax/user/{username}/followers?{page}",
            "user_following": r"GET /ajax/user/{username}/following?{page}",
            "user_teaching": r"GET /ajax/user/{username}/teaching?{page}",
            "user_learning": r"GET /ajax/user/{username}/learning?{page}",

            "user_dashboard": r"GET /ajax/dashboard {cookies.sessionid}",
            "user_leaderboard": r"GET /ajax/leaderboard {cookies.sessionid}",
            "user_sync": r"GET /ajax/sync {cookies.sessionid}",
            "debug_session": r"GET /ajax/session",
        }
        # fmt: on

        # Add URLs we did not bother to add in patterns
        from utils.debug import autodetect_urls

        autodetect_urls(app, prefix="/ajax", res=patterns)

        return json.dumps({k: patterns[k] for k in sorted(patterns.keys())})


class debug_session:
    def GET(self):
        session = dict(web.ctx.session)
        web.header("Content-Type", "application/json")
        return json.dumps(session)


app = web.application(urls, locals(), autoreload=False)


def catch_unauthorized(handler):
    """
    Don't let the main app render a template for web.Unauthorized exceptions
    Just send the status code and message
    """
    try:
        result = handler()
    except web.Unauthorized as e:
        setattr(e, "__next__", True)

        raise e
    return result


app.add_processor(catch_unauthorized)
