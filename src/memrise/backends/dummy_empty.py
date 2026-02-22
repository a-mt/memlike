from .dummy import DummyMemrise


class DummyEmptyMemrise(DummyMemrise):
    def whatistudy(self, offset=0, **kwargs):
        return [{
            "courses": [],
            "offset": 0,
            "has_more_pages": False,
        }]

    def my_leaderboard(self, period, **kwargs):
        return {
            "rows": [],
        }

    def courses(self, lang, page=1, cat="", query="", **kwargs):
        return {
            "page": page,
            "content": "",
            "has_next": False
        }

    def categories(self, lang, **kwargs):
        return {}

    def course(self, idCourse, slugCourse="example", **kwargs):
        return {
            "id"         : idCourse,
            "title"      : "Example",
            "url"        : f"/community/course/{idCourse}/{slugCourse}/",
            "author"     : "4v15721",
            "description": "",
            "photo"      : "",
            "levels"     : {},
            "breadcrumb" : [],
        }

    def level(self, idCourse, slugCourse, lvl, slug="preview", **kwargs):
        return {
          "learnables": [],
          "progress": [],
          "session_source_info": {
            "source_id": idCourse,
            "source_type": "course_id_and_level_index",
            "name": "Example",
            "translated_name": "Example",
            "learnable_ids_to_course_ids": {},
            "num_due_for_review": 0,
            "level_id": None,
            "level_name": "New level",
            "source_sub_index": lvl,
            "template_id": None,
            "parent_source_id": None,
            "parent_template_id": None
          },
          "settings": {
            "disable_multimedia": False,
            "disable_tapping": False,
            "prioritize_typing": False,
            "disable_typing": False,
          },
        }

    def level_multimedia(self, idCourse, slugCourse, lvl, **kwargs):
        return ""

    def course_leaderboard(self, idCourse, period, **kwargs):
        return {
            "rows": []
        }

    def user(self, username, **kwargs):
        return {
            "username": username,
            "photo"   : "",
            "points"  : 0,
            "rank"    : 0,
            "stats"   : {
                "following": 0,
                "followers": 0,
                "words": 0,
                "points": 0,
                "learning": 0,
                "teaching": 0,
            }
        }

    def user_mempals(self, tab, username, page=1, **kwargs):
        return {
            "page": 1,
            "lastpage": 1,
            "has_next": False,
            "users": []
        }

    def user_courses(self, tab, username, **kwargs):
        return {
            "nbCourse": 0,
            "content": []
        }

    def level_edit_get(self, idLevel, **kwargs):
        return {
            "success": True,
            "rendered": "",
        }

    def level_thing_add(self, idLevel, data, **kwargs):
        return {
            "success": True,
            "thing": {
                "id": 477757811,
                "pool_id": 7758772,
                "columns": {},
                "attributes": {}
            },
            "rendered_thing": "",
        }

    def level_thing_edit(self, idThing, cellId, cellValue, **kwargs):
        return {
            "success": None,
        }

    def level_thing_upload(self, idThing, cellId, file, **kwargs):
        return {
            "success": True,
            "rendered": "",
        }

    def level_thing_upload_remove(self, idThing, cellId, fileId, **kwargs):
        return {
            "success": True,
            "rendered": "",
        }

    def level_thing_remove(self, idLevel, idThing, **kwargs):
        return {
            "success": True,
        }

    def level_thing_get(self, idThing, **kwargs):
        return {
            "thing": {
                "id": idThing,
                "pool_id": 7758772,
                "columns": {},
                "attributes": {}
            }
        }

    def level_thing_alt_edit(self, idThing, alts, column_key, **kwargs):
        return {
            "success": None,
        }

    def level_multimedia_edit(self, idLevel, txt, **kwargs):
        return {
            "success": True,
            "multimedia": "",
        }

    def course_edit_get(self, idCourse, slugCourse, **kwargs):
        """
        Testset: tests/testset/course_edit.html
        """
        return {
            "csrftoken": "",
            "referer": "",
            "url": f"/community/course/{idCourse}/{slugCourse}/",
            "title": "Example",
            "levels": [],
        }
