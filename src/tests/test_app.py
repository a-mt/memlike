from .testcases import SimpleTestCase


# https://github.com/webpy/webpy/tree/master/tests
class ApplicationTest(SimpleTestCase):

    def test_homepage(self):
        response = self.client.request('/')
        self.assertEqual(response.status_code, 200)

    def test_nop(self):
        response = self.client.request('/nop')
        self.assertEqual(response.status_code, 404)

    def test_session(self):
        response = self.client.request('/ajax/session')
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get('session_id', None))
        self.assertIsNotNone(payload.get('lang', None))
        self.assertFalse(payload.get('loggedin', False))
        self.assertEqual(payload.get('learning', None), {})
