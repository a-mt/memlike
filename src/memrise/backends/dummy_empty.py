from .dummy import DummyMemrise


class DummyEmptyMemrise(DummyMemrise):
    def whatistudy(self, offset=0, **kwargs):
        return [
            {
                "courses": [],
                "offset": 0,
                "has_more_pages": False,
            }
        ]

    def my_leaderboard(self, period, **kwargs):
        return {
            "rows": [],
        }

    def my_progress_summary(self, **kwargs):
        return {}

    def my_progress(self, **kwargs):
        return {
            "sync_token": 0,
            "thingusers": [],
        }

    def courses(self, lang_slug, page=1, cat="", query="", **kwargs):
        return {
            "page": page,
            "content": "",
            "has_next": False,
        }

    def categories(self, lang_slug, **kwargs):
        return {}

    def course(self, course_id, course_slug="course", **kwargs):
        return {
            "id": course_id,
            "title": "Course",
            "url": f"/community/course/{course_id}/{course_slug}/",
            "author": "",
            "description": "",
            "photo": "",
            "levels": {},
            "breadcrumb": [],
        }

    def level(self, course_id, course_slug, level_index, session_type="preview", **kwargs):
        return {
            "learnables": [],
            "progress": [],
            "session_source_info": {
                "source_id": course_id,
                "source_type": "course_id_and_level_index",
                "name": "Course",
                "translated_name": "Course",
                "learnable_ids_to_course_ids": {},
                "nb_due_for_review": 0,
                "level_id": None,
                "level_name": "New level",
                "source_sub_index": level_index,
                "template_id": None,
                "parent_source_id": None,
                "parent_template_id": None,
            },
            "settings": {
                "disable_multimedia": False,
                "disable_tapping": False,
                "prioritize_typing": False,
                "disable_typing": False,
            },
        }

    def level_multimedia(self, course_id, course_slug, level_index, **kwargs):
        return ""

    def course_leaderboard(self, course_id, period, **kwargs):
        return {"rows": []}

    def user(self, username, **kwargs):
        return {
            "username": username,
            "photo": "",
            "points": 0,
            "rank": 0,
            "stats": {
                "following": 0,
                "followers": 0,
                "words": 0,
                "points": 0,
                "learning": 0,
                "teaching": 0,
            },
        }

    def user_mempals(self, tab, username, page=1, **kwargs):
        return {
            "page": 1,
            "lastpage": 1,
            "has_next": False,
            "users": [],
        }

    def user_courses(self, tab, username, **kwargs):
        return {
            "nb_courses": 0,
            "content": [],
        }

    def level_get_editpage(self, level_id, **kwargs):
        return {
            "success": True,
            "rendered": "",
        }

    def level_thing_add(self, level_id, data, **kwargs):
        return {
            "success": True,
            "thing": {"id": 477757811, "pool_id": 7758772, "columns": {}, "attributes": {}},
            "rendered_thing": "",
        }

    def level_thing_update(self, thing_id, cell_id, cell_value, **kwargs):
        return {
            "success": None,
        }

    def level_thing_file_upload(self, thing_id, cell_id, file, **kwargs):
        return {
            "success": True,
            "rendered": "",
        }

    def level_thing_file_delete(self, thing_id, cell_id, file_id, **kwargs):
        return {
            "success": True,
            "rendered": "",
        }

    def level_thing_delete(self, level_id, thing_id, **kwargs):
        return {
            "success": True,
        }

    def level_thing_get(self, thing_id, **kwargs):
        return {
            "thing": {
                "id": thing_id,
                "pool_id": 7758772,
                "columns": {},
                "attributes": {},
            }
        }

    def level_thing_alt_update(self, thing_id, alts, column_key, **kwargs):
        return {
            "success": None,
        }

    def level_multimedia_update(self, level_id, txt, **kwargs):
        return {
            "success": True,
            "multimedia": "",
        }

    def course_get_editpage(self, course_id, course_slug, **kwargs):
        return {
            "id": course_id,
            "csrftoken": "",
            "referer": "",
            "url": f"/community/course/{course_id}/{course_slug}/",
            "title": "Example",
            "levels": [],
            "last_pool_id": None,
        }
