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
        username = settings.MEMRISE_ANON_USERNAME or "bob"
        password = settings.MEMRISE_ANON_PASSWORD or "pass"

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
