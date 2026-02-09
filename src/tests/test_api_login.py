from .testcases import SimpleTestCase
from _globals import GLOBALS


class ApplicationLoginTest(SimpleTestCase):

    def test_session_anonymous(self):
        response = self.client.request('/ajax/session')
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get('session_id', None))
        self.assertIsNotNone(payload.get('lang', None))
        self.assertFalse(payload.get('loggedin', False))
        self.assertEqual(payload.get('learning', None), {})

    def test_login(self):

        # user isn't logged in
        response = self.client.request('/ajax/session')
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertFalse(payload['loggedin'])

        # keep the same session throughout
        cookies = response.get_cookies()
        header_cookies = cookies.output(attrs={}, header='')

        # ---
        # display login form
        response = self.client.request('/login', headers={'Cookie': header_cookies})
        self.assertEqual(response.status_code, 200)

        # send form without username and password
        response = self.client.request(
            '/login',
            method='POST',
            data={'redirect': '/success'},
            headers={'Cookie': header_cookies},
            https=True,
            host='myhost',
            env={'SCRIPT_NAME': '/rootpath'},
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.get_headers().get('location', None), '')  # still on the same same page

        # send form
        username = 'bob'
        password = 'pass'

        response = self.client.request(
            '/login',
            method='POST',
            data={'username': username, 'password': password, 'redirect': '/success'},
            headers={'Cookie': header_cookies},
            https=True,
            host='myhost',
            env={'SCRIPT_NAME': '/rootpath'},
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.get_headers().get('location', None), 'https://myhost/rootpath/success')

        # ---
        # user is logged in
        response = self.client.request('/ajax/session', headers={'Cookie': header_cookies})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertTrue(payload['loggedin'])
        self.assertTrue(type(payload['loggedin']) is dict)
        self.assertEqual(payload['loggedin'].get('username', None), username)

    def test_test_login(self):
        response = self.client.request('/login', method='TEST')
        self.assertEqual(response.status_code, 303)

        response = self.client.request('/ajax/session', headers={'Cookie': response.get_cookies().simple_output()})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get('session_id', None))  # session_id in database (correspond to cookie value)
        self.assertIsNotNone(payload.get('lang', None))
        self.assertTrue(payload.get('loggedin', False))
        self.assertEqual(payload.get('learning', None), {})

        self.assertTrue(type(payload['loggedin']) is dict)
        self.assertIsNotNone(payload['loggedin'].get('sessionid', None))  # sessionid used to proxy to memrise

    def test_test_sugar_login(self):
        cookies = self.get_auth_cookies()

        response = self.client.request('/ajax/session', headers={'Cookie': cookies.simple_output()})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('loggedin', False))
