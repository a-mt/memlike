from memrise import load_memrise
from inspect import isgenerator
from .testcases import SimpleTestCase
import settings


class MemrisePostgresDBTest(SimpleTestCase):
    session = {}
    memrise = load_memrise("memrise.backends.PostgresDB")

    def setUp(self):
        if "session_id" in self.session:
            return

        self.init_context()
        self.init_memrise_login()

    def init_context(self):
        """
        Ensure web.ctx exists
        """
        response = self.client.request("/")
        self.assertEqual(response.status_code, 200)

        self.memrise.reset_db()

    def init_memrise_login(self):
        username = "bob"
        password = "pass"

        result = self.memrise.login(username, password)

        self.assertIsNotNone(result)
        self.assertIs(type(result), dict)
        self.assertEqual(result.get("username", None), username)
        self.assertIsNotNone(result.get("sessionid", None))
        self.assertIsNotNone(result.get("csrftoken", None))

        self.session["session_id"] = result["sessionid"]
        self.session["csrftoken"] = result["csrftoken"]

    def test_memrise_whoami(self):
        self.assertIsNotNone(self.session["session_id"])

        result = self.memrise.whoami(sessionid=self.session["session_id"])

        self.assertIs(type(result), dict)
        self.assertIsNotNone(result.get("sessionid", None))
        self.assertIsNotNone(result.get("username", None))
        self.assertIsNotNone(result.get("photo", None))
        self.assertEqual(result["sessionid"], self.session["session_id"])

    def test_memrise_whatistudy(self):
        self.assertIsNotNone(self.session["session_id"])

        pages = self.memrise.whatistudy(sessionid=self.session["session_id"])

        # Depending on the backend we might retrieve a generator or a list
        if isgenerator(pages):
            data = next(pages)
        else:
            self.assertIs(type(pages), list)
            self.assertTrue(len(pages) > 0)
            data = pages[0]

        self.assertIs(type(data.get("courses", None)), list)
        self.assertTrue(len(data["courses"]) > 0)

        course = data["courses"][0]
        self.assertIsNotNone(course.get("id", None))
        self.assertIsNotNone(course.get("name", None))
        self.assertIsNotNone(course.get("slug", None))
        self.assertIsNotNone(course.get("is_official", None))
        self.assertIsNotNone(course.get("photo_url", None))
        self.assertIsNotNone(course.get("next_session", None))  # TODO
        self.assertIsNotNone(course.get("progress", None))  # TODO

    def test_memrise_courses(self):
        result = self.memrise.courses(lang_slug="english", page=1)

        self.assertIs(type(result), dict)
        self.assertEqual(result["page"], 1)
        self.assertIsNotNone(result.get("has_next", None))
        self.assertIs(type(result.get("content", None)), str)

        # Filter on category
        result = self.memrise.courses(lang_slug="english", cat="german-2")
        self.assertNotEqual(len(result.get("content", None)), 0)

        # Filter on parent category
        result = self.memrise.courses(lang_slug="english", cat="german")
        self.assertNotEqual(len(result.get("content", None)), 0)

        # Filter on another category
        result = self.memrise.courses(lang_slug="english", cat="bengali")
        self.assertEqual(len(result.get("content", None)), 0)

        # Offset > size
        result = self.memrise.courses(lang_slug="english", page=2)
        self.assertEqual(len(result.get("content", None)), 0)

    def test_memrise_categories(self):
        self.assertIsNotNone(self.session["session_id"])

        lang_slug = "german"
        lang_id = "879"

        result = self.memrise.categories_to_display(lang_slug, sessionid=self.session["session_id"])

        self.assertIs(type(result), dict)
        self.assertTrue(lang_id in result)
        self.assertTrue(result[lang_id])

        # at least the "french" category should have coursess - so {"2": True} is included in result
        self.assertTrue({lang_id: True}.items() <= result.items())

    def test_memrise_course(self):
        self.assertIsNotNone(self.session["session_id"])

        result = self.memrise.course(
            1,
            "example",
            sessionid=self.session["session_id"],
            csrftoken=self.session["csrftoken"],
        )

        self.assertIs(type(result), dict)
        self.assertEqual(result.get("id", None), 1)
        self.assertNotEqual(result.get("title", ""), "")
        self.assertNotEqual(result.get("description", ""), "")
        self.assertNotEqual(result.get("author", ""), "")
        self.assertNotEqual(result.get("photo", ""), "")
        self.assertNotEqual(result.get("url", ""), "")
        self.assertIsNotNone(result.get("levels", None))
        self.assertIsNotNone(result.get("breadcrumb", None))

        self.assertIs(type(result["breadcrumb"]), list)
        self.assertTrue(len(result["breadcrumb"]) > 0)
        self.assertIsNotNone(result["breadcrumb"][0].get("slug", None))

        self.assertIs(type(result["levels"]), dict)
        self.assertTrue(len(result["levels"]) > 0)
        level = result["levels"]["1"]
        self.assertIsNotNone(level.get("name", None))
        self.assertIsNotNone(level.get("type", None))
        self.assertTrue(level.get("type", None) in (1, 2))
        self.assertIsNotNone(level.get("status", None))
        # <span class="ico ico-complete ico-correct ico-m ico-green"></span>

        self.assertIsNotNone(result.get("stats", None))
        self.assertEqual(result["stats"].get("ignored", None), 1)
        self.assertEqual(result["stats"].get("learned", None), 3)
        self.assertEqual(result["stats"].get("review", None), 2)
        self.assertEqual(result["stats"].get("nb_things", None), 4)
        self.assertEqual(result["stats"].get("percent_complete", None), 99)

    def test_memrise_course_single_level(self):
        self.assertIsNotNone(self.session["session_id"])

        result = self.memrise.course(
            2,
            "",
            sessionid=self.session["session_id"],
            csrftoken=self.session["csrftoken"],
        )

        self.assertIs(type(result), dict)
        self.assertIsNotNone(result.get("id", None))
        self.assertIsNotNone(result.get("title", None))
        self.assertIsNotNone(result.get("description", None))
        self.assertIsNotNone(result.get("author", None))
        self.assertIsNotNone(result.get("photo", None))
        self.assertIsNotNone(result.get("url", None))
        self.assertIsNotNone(result.get("levels", None))
        self.assertIsNotNone(result.get("breadcrumb", None))

        self.assertIs(type(result["breadcrumb"]), list)
        self.assertTrue(len(result["breadcrumb"]) > 0)
        self.assertIsNotNone(result["breadcrumb"][0].get("slug", None))

        self.assertIs(type(result["levels"]), dict)
        self.assertEqual(len(result["levels"]), 0)
        self.assertIsNotNone(result.get("nb_things", None))

        self.assertIsNotNone(result.get("stats", None))
        self.assertIsNotNone(result["stats"].get("ignored", None))
        self.assertIsNotNone(result["stats"].get("learned", None))
        self.assertIsNotNone(result["stats"].get("percent_complete", None))
        self.assertIsNotNone(result["stats"].get("review", None))
        self.assertIsNotNone(result["stats"].get("nb_things", None))

    def test_course_add(self):
        self.assertIsNotNone(self.session["session_id"])

        result = self.memrise.course_add(
            data={
                "name": "New",
                "category": "2",
                "language": "6",
            },
            sessionid=self.session["session_id"],
            csrftoken=self.session["csrftoken"],
        )
        self.assertIs(type(result), dict)

    def test_course_delete(self):
        self.assertIsNotNone(self.session["session_id"])

        result = self.memrise.course_delete(
            3,
            sessionid=self.session["session_id"],
            csrftoken=self.session["csrftoken"],
        )
        self.assertIsNone(result)
