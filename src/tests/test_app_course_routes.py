from .testcases import SimpleTestCase


class ApplicationCourseRoutesTest(SimpleTestCase):
    """
    Check that the routes can be called and validate the input data
    """

    def test_courses(self):
        response = self.client.request("/community/courses?q=yoga")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

    def test_course(self):
        response = self.client.request("/course/1/my-course")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

    def test_course_editpage(self):
        response = self.client.request("/course/1/my-course/edit")
        self.assertEqual(response.status_code, 401)

        # Authenticated request = can access dashboard
        cookies = self.get_auth_cookies()
        response = self.client.request("/course/1/my-course/edit", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

    def test_leaderboard(self):
        # Unset period: use the default value
        response = self.client.request("/course/1/my-course/leaderbord")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

        # Wrong period: use the default value
        response = self.client.request("/course/1/my-course/leaderbord?period=nop")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

        # Valid period: use period
        response = self.client.request("/course/1/my-course/leaderbord?period=week")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

    def test_level(self):
        response = self.client.request("/course/1/my-course/1")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

        response = self.client.request("/course/1/my-course/1/my-level")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

    def test_thing(self):
        response = self.client.request("/course/1/my-course/1/28918327345410")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

    def test_learn_course(self):
        # Learning using the direct URL
        response = self.client.request("/course/1/my-course/1/garden/preview")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

    def test_learn_course_fromform(self):
        # Learn after choosing settings via the course form
        response = self.client.request("/course/1/my-course/1/garden?session_type=learn&save_progress=1")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

    def test_learn_level_fromform(self):
        # Learn after choosing settings via the level form
        response = self.client.request("/course/1/my-course/1/garden?session_type=learn&save_progress=1")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

        # Wrong session type: use default value (preview)
        response = self.client.request("/course/1/my-course/1/garden?session_type=whatever&save_progress=1")
        self.assertEqual(response.status_code, 200)

    def test_reset_level(self):
        response = self.client.request("/course/1/my-course/1/reset")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/course/1/my-course/1/reset", headers={"Cookie": cookies.simple_output()})
        self.assertLess(response.status_code, 400)

        html = response.data
        self.assertIsNotNone(html)

    def test_learn_course_v2(self):
        response = self.client.request("/aprender/review?course_id=1")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)
