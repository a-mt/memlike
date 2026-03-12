from .testcases import SimpleTestCase


class ApplicationUserRoutesTest(SimpleTestCase):
    """
    Check that the routes can be called and validate the input data
    """
    def test_my_leaderboard(self):
        cookies = self.get_auth_cookies()
        response = self.client.request("/home/leaderboard")
        self.assertEqual(response.status_code, 401)

        # Without period: use default value
        response = self.client.request("/home/leaderboard", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

        # Wrong period: use default value
        response = self.client.request("/home/leaderboard?period=nop", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

        # Valid period: use period
        response = self.client.request("/home/leaderboard?period=month", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

    def test_user_profile(self):
        response = self.client.request("/user/whatever")
        self.assertEqual(response.status_code, 200)

        response = self.client.request("/user/whatever/courses/teaching")
        self.assertEqual(response.status_code, 200)

        response = self.client.request("/user/whatever/courses/learning")
        self.assertEqual(response.status_code, 200)

        response = self.client.request("/user/whatever/mempals/followers")
        self.assertEqual(response.status_code, 200)

        response = self.client.request("/user/whatever/mempals/following")
        self.assertEqual(response.status_code, 200)
