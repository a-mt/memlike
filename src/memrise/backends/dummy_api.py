import json
import settings

from .api import ApiMemrise, Scraper
from .dummy import DummyMemrise


class DummyRequestor:
    def get_testset_text(self, filename):
        with open(settings.ROOTDIR + "/tests/testset/" + filename) as f:
            return f.read().encode('utf-8').strip()

    def get_testset_json(self, filename):
        with open(settings.ROOTDIR + "/tests/testset/" + filename) as f:
            return json.loads(f.read())

    #+-----------------------------------------------------
    #| CURRENT USER
    #+-----------------------------------------------------
    def whoami(self, sessionid):
        return self.get_testset_text("settings.html")

    def whatistudy(self, sessionid, offset, nbperpage):
        data = self.get_testset_json("dashboard_courses.json")
        data["has_more_pages"] = False
        return data

    def my_leaderboard(self, sessionid, period):
        return self.get_testset_json("profile_leaderboard.json")

    def track_progress(self, path, data, sessionid, csrftoken, referer):
        pass

    #+-----------------------------------------------------
    #| COURSES
    #+-----------------------------------------------------
    def courses(self, lang, page, cat, query):
        data = self.get_testset_json("browse_cat-languages_scat-french_page-1.json")
        data["has_next"] = False
        return data

    #+-----------------------------------------------------
    #| CATEGORIES
    #+-----------------------------------------------------
    def categories(self, lang):
        return self.get_testset_text("courses.html")

    #+-----------------------------------------------------
    #| COURSE
    #+-----------------------------------------------------
    def course(self, sessionid, idCourse):
        return self.get_testset_text("course-6698294.html")

    #+-----------------------------------------------------
    #| COURSE > LEVEL
    #+-----------------------------------------------------
    def level(self, sessionid, csrftoken, idCourse, lvl):
        return self.get_testset_json("learning_session_learn.json")

    def level_learning_session(self, sessionid, idCourse, slugCourse, sessionType):
        return {
            "referer": "",
            "csrftoken": "",
        }

    def level_multimedia(self, urlCourse, lvl):
        return self.get_testset_text("level_multimedia.html")

    #+-----------------------------------------------------
    #| COURSE > LEADERBOARD
    #+-----------------------------------------------------
    def course_leaderboard(self, sessionid, idCourse, period):
        return self.get_testset_json("course_leaderboard.json")

    #+-----------------------------------------------------
    #| USER
    #+-----------------------------------------------------
    def user(self, username):
        return self.get_testset_text("user_courses_en.html")

    def user_mempals(self, tab, username, page):
        return self.get_testset_text("user_mempals_following.html")

    #+-----------------------------------------------------
    #| USER's COURSES
    #+-----------------------------------------------------
    def user_courses(self, tab, username):
        return self.get_testset_text("user_courses_teaching.html")

    #+-----------------------------------------------------
    #| EDIT
    #+-----------------------------------------------------
    def course_edit_get(self, sessionid, idCourse, slugCourse):
        html = self.get_testset_text("course_get_edit.html")
        return {
            "csrftoken": "",
            "referer": "",
            "html": html
        }


class DummyApiMemrise(ApiMemrise):
    def __init__(self):
        self.requestor = DummyRequestor()
        self.scraper = Scraper()

    def _login_as_anonymous(self):
        return self.login(None, None)["sessionid"]

    login = DummyMemrise.__dict__["login"]
    level_edit_get = DummyMemrise.__dict__["level_edit_get"]
    level_thing_add = DummyMemrise.__dict__["level_thing_add"]
    level_thing_edit = DummyMemrise.__dict__["level_thing_edit"]
    level_thing_upload = DummyMemrise.__dict__["level_thing_upload"]
    level_thing_upload_remove = DummyMemrise.__dict__["level_thing_upload_remove"]
    level_thing_remove = DummyMemrise.__dict__["level_thing_remove"]
    level_thing_get = DummyMemrise.__dict__["level_thing_get"]
    level_thing_alt_edit = DummyMemrise.__dict__["level_thing_alt_edit"]
    level_multimedia_edit = DummyMemrise.__dict__["level_multimedia_edit"]
