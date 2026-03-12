from .testcases import SimpleTestCase


# https://github.com/webpy/webpy/tree/master/tests
class ApplicationHomeTest(SimpleTestCase):
    """
    Checking that the API can be requested
    and returns the right status code (200, 404)
    """

    def test_homepage(self):
        response = self.client.request("/")
        self.assertEqual(response.status_code, 200)

    def test_nop(self):
        response = self.client.request("/nop")
        self.assertEqual(response.status_code, 404)
