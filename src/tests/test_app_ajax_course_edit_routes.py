from .testcases import SimpleTestCase


class ApplicationAjaxCourseEditRoutesTest(SimpleTestCase):
    """
    Check that the routes can be called and validate the input data
    """

    def test_course(self):
        response = self.client.request("/ajax/course/1/my-course/edit")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/course/1/my-course/edit", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsNotNone(payload.get("title", None))

    def test_level_add(self):
        response = self.client.request("/ajax/level/add", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/level/add", method="POST", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/level/add",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "course_id": 1,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_level_edit_title(self):
        response = self.client.request("/ajax/level/title_edit", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/level/title_edit", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/level/title_edit",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "level_id": 1,
                "title": "example",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_level_edit_columns(self):
        response = self.client.request("/ajax/level/columns_edit", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/level/columns_edit", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/level/columns_edit",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "level_id": 1,
                "column_a": "1",
                "column_b": "2",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_level_attribute_edit(self):
        response = self.client.request("/ajax/level/column_edit", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/level/column_edit", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/level/column_edit",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "pool_id": 1,
                "column_key": "1",
                "label": "Part of Speach",
                "column_structure": "attribute",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_level_column_remove(self):
        response = self.client.request("/ajax/level/column_remove", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/level/column_remove", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/level/column_remove",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "pool_id": 1,
                "column_key": "1",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_level_delete(self):
        response = self.client.request("/ajax/level/delete", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/level/delete", method="POST", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/level/delete",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "level_id": 1,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_level(self):
        response = self.client.request("/ajax/level/1")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/level/1", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

    def test_level_thing_alt(self):
        response = self.client.request("/ajax/level/1/alt", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/level/1/alt", method="POST", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 200)

    def test_level_thing_alt_update(self):
        response = self.client.request("/ajax/level/1/alt_edit", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/level/1/alt_edit", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/level/1/alt_edit",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "cell_id": 1,
                "alts": r"{}",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_level_thing_add(self):
        response = self.client.request("/ajax/level/1/add", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/level/1/add", method="POST", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/level/1/add",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "data": r"{}",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_level_thing_update(self):
        response = self.client.request("/ajax/level/1/edit", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/level/1/edit", method="POST", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/level/1/edit",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "cell_id": 1,
                "cell_value": r"{}",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_level_thing_delete(self):
        response = self.client.request("/ajax/level/1/remove", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/level/1/remove", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/level/1/remove",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "thing_id": 1,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_level_multimedia_update(self):
        response = self.client.request("/ajax/level/1/edit_multimedia", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/level/1/edit_multimedia", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/level/1/edit_multimedia",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "course_id": 1,
                "level_index": 1,
                "txt": "",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_level_thing_file_upload(self):
        response = self.client.request("/ajax/level/1/upload", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/level/1/upload", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 400)

        data = '--boundary\r\nContent-Disposition: form-data; name="cell_id"\r\n\r\n3\r\n--boundary\r\nContent-Disposition: form-data; name="file"; filename="a.txt"\r\nContent-Type: text/plain\r\n\r\na\r\n--boundary--\r\n'  # noqa: E501

        response = self.client.request(
            "/ajax/level/1/upload",
            method="POST",
            headers={
                "Cookie": cookies.simple_output(),
                "Content-Type": "multipart/form-data; boundary=boundary",
            },
            data=data,
        )
        self.assertEqual(response.status_code, 200)

    def test_level_thing_file_upload_v2(self):
        response = self.client.request("/ajax/thing/cell/upload_file", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/thing/cell/upload_file", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 400)

        data = '--boundary\r\nContent-Disposition: form-data; name="thing_id"\r\n\r\n1\r\n--boundary\r\nContent-Disposition: form-data; name="cell_id"\r\n\r\n3\r\n--boundary\r\nContent-Disposition: form-data; name="f"; filename="a.txt"\r\nContent-Type: text/plain\r\n\r\na\r\n--boundary--\r\n'  # noqa: E501

        response = self.client.request(
            "/ajax/thing/cell/upload_file",
            method="POST",
            headers={
                "Cookie": cookies.simple_output(),
                "Content-Type": "multipart/form-data; boundary=boundary",
            },
            data=data,
        )
        self.assertEqual(response.status_code, 200)

    def test_level_thing_file_delete(self):
        response = self.client.request("/ajax/level/1/upload_remove", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/level/1/upload_remove", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/level/1/upload_remove",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "cell_id": 1,
                "file_id": 1,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_course_delete(self):
        response = self.client.request("/ajax/course/1/example/remove", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request(
            "/ajax/course/1/example/remove", method="POST", headers={"Cookie": cookies.simple_output()}
        )
        self.assertEqual(response.status_code, 200)

    def test_course_add(self):
        response = self.client.request("/ajax/course/add", method="POST")
        self.assertEqual(response.status_code, 401)

        cookies = self.get_auth_cookies()
        response = self.client.request("/ajax/course/add", method="POST", headers={"Cookie": cookies.simple_output()})
        self.assertEqual(response.status_code, 400)

        response = self.client.request(
            "/ajax/course/add",
            method="POST",
            headers={"Cookie": cookies.simple_output()},
            data={
                "name": "Example",
                "category": "2",
                "language": "english",
            },
        )
        print(response.data)
        self.assertEqual(response.status_code, 200)
