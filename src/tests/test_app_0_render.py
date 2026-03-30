from app import app  # noqa F401
from .testcases import SimpleTestCase

from memrise import load_memrise
import settings
import variables
import web


COURSE_ID = "6717861"
COURSE_SLUG = "german"

LEVEL_ID = "16266974"
LEVEL_MULTIMEDIA_ID = "16266978"


class ApplicationRenderTest(SimpleTestCase):
    """
    Check that all templates can be rendered
    """

    auth = False
    memrise = load_memrise("memrise.backends.DummyMemrise")

    def setUp(self):
        if self.auth:
            return

        self.auth = self.get_auth_cookies()

    def test_about(self):
        html = web.config.template.render.about()
        self.assertIsNotNone(html)

    def test_course_get_editpage(self):
        course = self.memrise.course_get_editpage(COURSE_ID, course_slug=COURSE_SLUG)
        html = web.config.template.render.course_edit(course, {}, {})
        self.assertIsNotNone(html)

    def test_course_leaderboard(self):
        period = "alltime"
        course = self.memrise.course(COURSE_ID, course_slug=COURSE_SLUG)
        leaderboard = self.memrise.course_leaderboard(COURSE_ID, period)
        html = web.config.template.render.course_leaderboard(course, period, leaderboard)
        self.assertIsNotNone(html)

    def test_course_summary(self):
        course = self.memrise.course(COURSE_ID, COURSE_SLUG)
        html = web.config.template.render.course_summary(course)
        self.assertIsNotNone(html)

    def test_course_level_from_course(self):
        course = self.memrise.course(settings.DUMMY_SINGLE_LEVEL, COURSE_SLUG)
        items = self.memrise.level(settings.DUMMY_SINGLE_LEVEL, COURSE_SLUG, "1", "preview")
        html = web.config.template.render.course_level(
            course,
            {
                "name": False,
                "type": 1,
                "index": 1,
            },
            items,
        )
        self.assertIsNotNone(html)

    def test_course_level_kind_things(self):
        level_index = "2"

        course = self.memrise.course(COURSE_ID, COURSE_SLUG)
        level = course["levels"][level_index]
        items = self.memrise.level(COURSE_ID, COURSE_SLUG, level_index, "preview")

        html = web.config.template.render.course_level(
            course,
            {
                "name": level["name"],
                "type": level["type"],
                "index": level_index,
            },
            items,
        )
        self.assertIsNotNone(html)

    def test_course_level_kind_multimedia(self):
        level_index = "1"

        course = self.memrise.course(COURSE_ID, COURSE_SLUG)
        level = course["levels"][level_index]
        items = self.memrise.level_multimedia(COURSE_ID, COURSE_SLUG, level_index)

        html = web.config.template.render.course_level(
            course,
            {
                "name": level["name"],
                "type": level["type"],
                "index": level_index,
            },
            items,
        )
        self.assertIsNotNone(html)

    def test_courses(self):
        lang_slug = "french"

        # Retrieve list of categories that have a course
        has_courses = self.memrise.categories(lang_slug)
        html = web.config.template.render.courses(
            {
                "lang": lang_slug,
                "cat": "",
                "catId": "",
                "q": "",
            },
            variables.languages,
            variables.categories,
            has_courses,
        )
        self.assertIsNotNone(html)

    def test_index(self):
        html = web.config.template.render.index()
        self.assertIsNotNone(html)

    def test_design_system(self):
        html = web.config.template.render.design_system()
        self.assertIsNotNone(html)

    def test_dashboard_courses(self):
        html = web.config.template.render.dashboard("courses", False, False)
        self.assertIsNotNone(html)

    def test_dashboard_leaderboard(self):
        period = "alltime"
        leaderboard = self.memrise.my_leaderboard(period)
        html = web.config.template.render.dashboard("leaderboard", period, leaderboard)
        self.assertIsNotNone(html)

    def test_login(self):
        html = web.config.template.render.login("", {}, {})
        self.assertIsNotNone(html)

    def test_user(self):
        user = self.memrise.user("Decks")

        tabs = [
            "teaching",
            "learning",
            "followers",
            "following",
        ]
        for tab in tabs:
            html = web.config.template.render.user(user, tab, variables.USER_RANKS)

            self.assertIsNotNone(html, tab + " could not be rendered")

    def test_learn(self):
        course = self.memrise.course(COURSE_ID, COURSE_SLUG)
        html = web.config.template.render.learn(course, "preview", "1", False, 1, 1)

        self.assertIsNotNone(html)
