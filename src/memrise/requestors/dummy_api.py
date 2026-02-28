import json
import settings


class DummyApiRequestor:
    def get_testset_text(self, filename):
        with open(settings.ROOTDIR + "/tests/testset/" + filename) as f:
            return f.read().encode("utf-8").strip()

    def get_testset_json(self, filename):
        with open(settings.ROOTDIR + "/tests/testset/" + filename) as f:
            return json.loads(f.read())

    # +-----------------------------------------------------
    # | CURRENT USER
    # +-----------------------------------------------------
    def whoami(self, **kwargs):
        return self.get_testset_text("profile_settings.html")

    def whatistudy(self, offset, nbperpage, **kwargs):
        data = self.get_testset_json("dashboard_courses.json")
        data["has_more_pages"] = offset == 0
        return data

    def my_leaderboard(self, period, **kwargs):
        return self.get_testset_json("profile_leaderboard.json")

    # +-----------------------------------------------------
    # | LEARNING SESSION
    # +-----------------------------------------------------
    def learning_session_register_end(self, data, sessionid=None, csrftoken=None, referer=None):
        return self.get_testset_json("course-6698294_garden_learn1_sessionend_response.json")

    def reset_progress_level(self, data, sessionid=None, csrftoken=None, referer=None):
        return None

    def learning_session_register_progress(self, data, sessionid=None, csrftoken=None, referer=None):
        return self.get_testset_json("course-6698294_garden_review_registerprogress_response.json")

    # +-----------------------------------------------------
    # | COURSES
    # +-----------------------------------------------------
    def courses(self, lang, page, cat, query, **kwargs):
        data = self.get_testset_json("browse_cat-languages_scat-french_page-1.json")
        data["has_next"] = False
        data["page"] = page
        return data

    def categories(self, lang, **kwargs):
        return self.get_testset_text("courses.html")

    # +-----------------------------------------------------
    # | COURSE
    # +-----------------------------------------------------
    def course(self, idCourse, slugCourse="", **kwargs):
        if idCourse == settings.DUMMY_SINGLE_LEVEL:
            return self.get_testset_text("course-6618687.html")

        return self.get_testset_text("course-1892646.html")
        return self.get_testset_text("course-6660056.html")

    def level(self, idCourse, lvl, **kwargs):
        if idCourse == settings.DUMMY_SINGLE_LEVEL:
            return self.get_testset_json("course-6618687_level-1_learning_session_preview.json")

        return self.get_testset_json("course-1892646_level-2_learning_session_preview.json")  # attributes
        return self.get_testset_json("course-399843_level-1_learning_session_preview.json")  # image
        return self.get_testset_json("course-365747_level-3_learning_session_preview.json")  # audio
        return self.get_testset_json("course-57289_level-1_learning_session_preview.json")  # hidden_info

    def level_multimedia(self, idCourse, slugCourse, lvl, **kwargs):
        return self.get_testset_text("course-1892646_level-1_multimedia.html")

    def course_leaderboard(self, idCourse, period, **kwargs):
        return self.get_testset_json("course_leaderboard.json")

    # +-----------------------------------------------------
    # | USER
    # +-----------------------------------------------------
    def user(self, username, **kwargs):
        return self.get_testset_text("user_courses_en.html")

    def user_mempals(self, tab, username, page, **kwargs):
        return self.get_testset_text("user_mempals_following.html")

    def user_courses(self, tab, username, **kwargs):
        return self.get_testset_text("user_courses_teaching.html")

    # +-----------------------------------------------------
    # | EDIT COURSE
    # +-----------------------------------------------------
    def course_edit_get(self, idCourse, slugCourse, **kwargs):
        html = self.get_testset_text("course_get_edit.html")
        return {
            "csrftoken": "",
            "referer": "",
            "html": html,
        }
