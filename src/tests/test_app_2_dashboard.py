from .testcases import SimpleTestCase


class ApplicationDashboardTest(SimpleTestCase):
    """
    Check that the user dashboard can only be accessed
    when a valid session_id is present in the cookies
    """
    def test_dashboard_anonymous(self):
        response = self.client.request("/ajax/dashboard")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/dashboard", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)
