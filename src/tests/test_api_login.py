from .testcases import SimpleTestCase

import web


class ApplicationLoginTest(SimpleTestCase):
    def setUp(self):
        session = web.test.session

        self.session_store = session.store
        self.session_parameters = session._config

        # Reset session configs to defaults
        self.session_parameters.update(dict(web.config.session_parameters))

    def test_session_anonymous(self):
        response = self.client.request("/ajax/session")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("session_id", None))
        self.assertIsNotNone(payload.get("lang", None))
        self.assertFalse(payload.get("loggedin", False))
        self.assertEqual(payload.get("learning", None), {})

    def test_login(self):
        # user isn't logged in
        response = self.client.request("/ajax/session")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertFalse(payload.get("loggedin", None))

        # keep the same session throughout
        cookies = response.get_cookies()
        header_cookies = cookies.output(attrs={}, header="")

        # ---
        # display login form
        response = self.client.request("/login", headers={"Cookie": header_cookies})
        self.assertEqual(response.status_code, 200)

        # send form without username and password
        response = self.client.request(
            "/login",
            method="POST",
            data={"redirect": "/success"},
            headers={"Cookie": header_cookies},
            https=True,
            host="myhost",
            env={"SCRIPT_NAME": "/rootpath"},
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.get_headers().get("location", None), "")  # still on the same same page

        # send form
        username = "bob"
        password = "pass"

        response = self.client.request(
            "/login",
            method="POST",
            data={"username": username, "password": password, "redirect": "/success"},
            headers={"Cookie": header_cookies},
            https=True,
            host="myhost",
            env={"SCRIPT_NAME": "/rootpath"},
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.get_headers().get("location", None), "https://myhost/rootpath/success")

        # ---
        # user is logged in
        response = self.client.request("/ajax/session", headers={"Cookie": header_cookies})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertTrue(payload["loggedin"])
        self.assertIs(type(payload["loggedin"]), dict)
        self.assertEqual(payload["loggedin"].get("username", None), username)

    def test_test_login(self):
        response = self.client.request("/login", method="TEST")
        self.assertEqual(response.status_code, 303)

        response = self.client.request("/ajax/session", headers={"Cookie": response.get_cookies().simple_output()})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("session_id", None))  # session_id in database (correspond to cookie value)
        self.assertIsNotNone(payload.get("lang", None))
        self.assertTrue(payload.get("loggedin", False))
        self.assertEqual(payload.get("learning", None), {})

        self.assertIs(type(payload["loggedin"]), dict)
        self.assertIsNotNone(payload["loggedin"].get("sessionid", None))  # sessionid used to proxy to memrise

    def test_test_sugar_login(self):
        cookies = self.get_auth_cookies()

        response = self.client.request("/ajax/session", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("loggedin", False))

    def test_session_deleted(self):
        cookie_name = self.session_parameters["cookie_name"]

        # ---
        # Unauthenticated Request = create new session
        response = self.client.request("/ajax/session")
        self.assertEqual(response.status_code, 200)

        # Get session ID
        cookies = response.get_cookies()
        sessionid = cookies[cookie_name].value

        # The session has been initialized with the default values
        payload = response.json()
        self.assertIsNotNone(payload.get("lang", None))

        # ---
        # Authenticated Request = same session
        response = self.client.request("/ajax/session", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

        # Same session ID
        cookies2 = response.get_cookies()
        sessionid2 = cookies2[cookie_name].value
        self.assertEqual(sessionid, sessionid2)

        # The session still holds the same values
        payload = response.json()
        self.assertIsNotNone(payload.get("lang", None))

        # Clear out the sessions (config.template holds the session from the last request)
        session_store = self.session_store
        self.assertIsNotNone(session_store)
        del session_store[sessionid]

        # ---
        # Authenticated Request with deleted session = new session
        response = self.client.request("/ajax/session", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

        # New session ID
        cookies3 = response.get_cookies()
        sessionid3 = cookies3[cookie_name].value
        self.assertNotEqual(sessionid, sessionid3)

        # The session has been initialized with the default values
        payload = response.json()
        self.assertIsNotNone(payload.get("lang", None))

    def test_session_deleted2(self):
        # Unauthenticated request = cannot access dashboard
        response = self.client.request("/ajax/dashboard")
        self.assertEqual(response.status_code, 403)

        # Authenticated request = can access dashboard
        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/dashboard", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

        # Delete session
        cookie_name = self.session_parameters["cookie_name"]
        session_store = self.session_store
        del session_store[cookies[cookie_name].value]

        # Authenticated request with deleted session = cannot access dashboard
        response = self.client.request("/ajax/dashboard", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 403)

    def test_session_ip_update(self):
        cookie_name = self.session_parameters["cookie_name"]
        cookies = self.get_auth_cookies()
        headers = {"Cookie": cookies.simple_output()}

        # Set settings = ensure session got created with the current IP
        self.session_parameters.ignore_change_ip = False

        # Request with same IP (None) = same session
        response = self.client.request("/ajax/session", headers=headers, env={"REMOTE_ADDR": None})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json().get("ip", "ANY"))
        self.assertEqual(response.get_cookies()[cookie_name].value, cookies[cookie_name].value)

        response = self.client.request("/ajax/dashboard", headers=headers, env={"REMOTE_ADDR": None})
        self.assertEqual(response.status_code, 200)

        # Request with different IP = new session
        response = self.client.request("/ajax/session", headers=headers, env={"REMOTE_ADDR": "0.0.0.1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("ip", "ANY"), "0.0.0.1")
        self.assertNotEqual(response.get_cookies()[cookie_name].value, cookies[cookie_name].value)

        response = self.client.request("/ajax/dashboard", headers=headers, env={"REMOTE_ADDR": "0.0.0.1"})
        self.assertEqual(response.status_code, 403)

        # Request with old IP = session was deleted, gets new session
        response = self.client.request("/ajax/session", headers=headers, env={"REMOTE_ADDR": None})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json().get("ip", "ANY"))
        self.assertNotEqual(response.get_cookies()[cookie_name].value, cookies[cookie_name].value)

    def test_session_ip_update2(self):
        cookie_name = self.session_parameters["cookie_name"]
        cookies = self.get_auth_cookies()
        headers = {"Cookie": cookies.simple_output()}

        # Set settings = can change current IP during session
        self.session_parameters.ignore_change_ip = True

        # Request with same IP (None) = same session
        response = self.client.request("/ajax/session", headers=headers, env={"REMOTE_ADDR": None})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json().get("ip", "ANY"))
        self.assertEqual(response.get_cookies()[cookie_name].value, cookies[cookie_name].value)

        response = self.client.request("/ajax/dashboard", headers=headers, env={"REMOTE_ADDR": None})
        self.assertEqual(response.status_code, 200)

        # Request with different IP = IP is updated
        response = self.client.request("/ajax/session", headers=headers, env={"REMOTE_ADDR": "0.0.0.1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("ip", "ANY"), "0.0.0.1")
        self.assertEqual(response.get_cookies()[cookie_name].value, cookies[cookie_name].value)

        response = self.client.request("/ajax/dashboard", headers=headers, env={"REMOTE_ADDR": "0.0.0.1"})
        self.assertEqual(response.status_code, 200)

    def test_session_ip_expired(self):
        cookie_name = self.session_parameters["cookie_name"]
        cookies = self.get_auth_cookies()
        headers = {"Cookie": cookies.simple_output()}

        # Set settings = ignore timeout
        self.session_parameters.timeout = 0
        self.session_parameters.ignore_expiry = True

        # Request with timed out session = new session
        response = self.client.request("/ajax/session", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.get_cookies()[cookie_name].value, cookies[cookie_name].value)

    def test_session_ip_expired2(self):
        cookies = self.get_auth_cookies()
        headers = {"Cookie": cookies.simple_output()}

        # Set settings = throw exception on timeout
        self.session_parameters.timeout = 0
        self.session_parameters.ignore_expiry = False

        # Request with timed out session = 401
        response = self.client.request("/ajax/session", headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, b"Session expired")
