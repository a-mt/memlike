from .testcases import SimpleTestCase


class ApplicatioDashboardTest(SimpleTestCase):

    def test_dashboard_anonymous(self):
        response = self.client.request('/ajax/dashboard')
        self.assertEqual(response.status_code, 403)

        cookies = self.get_auth_cookies()
        response = self.client.request('/ajax/dashboard', headers={'Cookie': cookies.simple_output()})
        self.assertEqual(response.status_code, 200)
