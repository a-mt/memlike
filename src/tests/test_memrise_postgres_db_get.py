from memrise import load_memrise
from inspect import isgenerator
from .testcases import SimpleTestCase
import settings


COURSE_ID = "1892646"
COURSE_SLUG = "grammaire-le-groupe-nominal"


class MemrisePostgresDBGetTest(SimpleTestCase):
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
