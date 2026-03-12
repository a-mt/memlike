from .testcases import SimpleTestCase


class ApplicationAjaxUserRoutesTest(SimpleTestCase):
    """
    Check that the routes can be called and validate the input data
    """

    def test_leaderboard(self):
        response = self.client.request("/ajax/leaderboard")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/leaderboard", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("rows", None))

    def test_progress(self):
        response = self.client.request("/ajax/progress")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/progress", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

    def test_user(self):
        response = self.client.request("/ajax/user/bob")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("username", None))

    def test_user_followers(self):
        response = self.client.request("/ajax/user/bob/followers")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("users", None))

    def test_user_following(self):
        response = self.client.request("/ajax/user/bob/following")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("users", None))

    def test_user_teaching(self):
        response = self.client.request("/ajax/user/bob/teaching")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("content", None))

    def test_user_learning(self):
        response = self.client.request("/ajax/user/bob/learning")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("content", None))

    def test_user_progress(self):
        response = self.client.request("/ajax/progress")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/progress", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)
