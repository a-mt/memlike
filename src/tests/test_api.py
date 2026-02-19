from .testcases import SimpleTestCase


# https://github.com/webpy/webpy/tree/master/tests
class ApplicationHomeTest(SimpleTestCase):
    def test_homepage(self):
        response = self.client.request("/")
        self.assertEqual(response.status_code, 200)

    def test_nop(self):
        response = self.client.request("/nop")
        self.assertEqual(response.status_code, 404)
