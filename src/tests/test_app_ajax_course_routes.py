from .testcases import SimpleTestCase
import json


class ApplicationAjaxCourseRoutesTest(SimpleTestCase):
    """
    Check that the routes can be called and validate the input data
    """

    def test_courses(self):
        response = self.client.request("/ajax/courses")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("content", None))

    def test_course(self):
        response = self.client.request("/ajax/course/1/my-course")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("title", None))

    def test_leaderboard(self):
        response = self.client.request("/ajax/course/1/my-course/leaderboard")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("rows", None))

        response = self.client.request("/ajax/course/1/my-course/leaderboard?period=week")
        self.assertEqual(response.status_code, 200)

        response = self.client.request("/ajax/course/1/my-course/leaderboard?period=nop")
        self.assertEqual(response.status_code, 400)

    def test_level_things(self):
        response = self.client.request("/ajax/course/1/my-course/1/preview")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("learnables", None))

    def test_level_media(self):
        response = self.client.request("/ajax/course/1/my-course/1/media")
        self.assertEqual(response.status_code, 200)

        html = response.data
        self.assertIsNotNone(html)

    def test_level_learn(self):
        response = self.client.request("/ajax/course/1/my-course/1/learn")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("learnables", None))

    def test_level_reset(self):
        response = self.client.request("/ajax/reset_progress_level", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/reset_progress_level", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/reset_progress_level",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "level_id": 1,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_register_progress(self):
        response = self.client.request("/ajax/register_progress", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/register_progress", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/register_progress",
            method="POST",
            headers={
                "Cookie": cookies.simple_output(),
                "Content-type": "application/json",
            },
            data=json.dumps(
                {
                    "events": [],
                }
            ),
        )
        self.assertEqual(response.status_code, 200)

    def test_register_end(self):
        response = self.client.request("/ajax/register_end", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/register_end", method="POST", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/register_end",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "session_points": 0,
                "session_type": "review",
                "session_source_type": "course",
                "session_source_id": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
