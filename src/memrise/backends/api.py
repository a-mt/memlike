import requests
import logging
import settings
import web

from memrise.scrapers import Scraper
from memrise.requestors import ApiRequestor, DummyApiRequestor
from .dummy import DummyLoginMixin, DummyEditMixin
from .base import Memrise


logger = logging.getLogger(__name__)


class ApiMemrise(Memrise):
    def __init__(self):
        self.requestor = self.create_requestor()
        self.scraper = self.create_scraper()

    def create_requestor(self):
        return ApiRequestor()

    def create_scraper(self):
        return Scraper()

    def get_saved_login(self):
        return web.ctx.get("session", {}).get("loggedin", None)

        # csrftoken=web.ctx.env.get("HTTP_X_CSRFTOKEN"),
        # referer=web.ctx.env.get("HTTP_X_REFERER"),

    def set_default_kwargs(self, kwargs):
        session = self.get_saved_login() or {}
        kwargs.setdefault("sessionid", session.get("sessionid", None))
        kwargs.setdefault("csrftoken", session.get("csrftoken", None))
        kwargs.setdefault("is_anon", session.get("is_anon", None))

    def set_kwargs_session(self, kwargs, session):
        kwargs["sessionid"] = session["sessionid"]
        kwargs["csrftoken"] = session["csrftoken"]
        kwargs["is_anon"] = session.get("is_anon", False)

    # +-----------------------------------------------------
    # | AUTH
    # +-----------------------------------------------------
    def login_as_anonymous(self, **kwargs):
        """
        Retrieve sessionid to retrieve content (using our own account)

        @return string - sessionid
        """
        session = self.login(settings.MEMRISE_ANON_USERNAME, settings.MEMRISE_ANON_PASSWORD)
        session["is_anon"] = True
        return session

    def login(self, username, password):
        return self.requestor.login(username, password)

    # +-----------------------------------------------------
    # | CURRENT USER
    # +-----------------------------------------------------
    def whoami(self, **kwargs):
        self.set_default_kwargs(kwargs)

        html = self.requestor.whoami(sessionid=kwargs["sessionid"])

        return self.scraper.whoami(kwargs["sessionid"], html)

    def whatistudy(self, offset=0, **kwargs):
        self.set_default_kwargs(kwargs)
        nbperpage = 4
        load_n_pages = 4

        c = 0
        while c < load_n_pages:
            c += 1

            data = self.requestor.whatistudy(
                offset,
                nbperpage,
                sessionid=kwargs["sessionid"],
            )
            offset += nbperpage
            has_more_pages = "has_more_pages" in data and data["has_more_pages"]

            yield {
                "courses": data["courses"],
                "has_more_pages": has_more_pages,
                "next_offset": offset if has_more_pages else None,
            }
            if not has_more_pages:
                break

    def my_leaderboard(self, period, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.my_leaderboard(
            period,
            sessionid=kwargs["sessionid"],
        )

    def track_progress(self, path, data, referer=None, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.track_progress(
            path,
            data,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
            referer=referer,
        )

    # +-----------------------------------------------------
    # | COURSES
    # +-----------------------------------------------------
    def courses(self, lang, page=1, cat="", query="", **kwargs):
        self.set_default_kwargs(kwargs)

        if not isinstance(page, int) and not page.isdigit():
            page = 1

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        return self.requestor.courses(lang=lang, page=page, cat=cat, query=query)

    def categories(self, lang, **kwargs):
        self.set_default_kwargs(kwargs)
        self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        html = self.requestor.categories(
            lang,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
        )
        return self.scraper.categories(html)

    # +-----------------------------------------------------
    # | COURSE
    # +-----------------------------------------------------
    def course(self, idCourse, slugCourse="", **kwargs):
        self.set_default_kwargs(kwargs)

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        html = self.requestor.course(
            idCourse,
            slugCourse,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
        )
        return self.scraper.course(idCourse, html, isLoggedIn=kwargs["sessionid"])

    def level(self, idCourse, slugCourse, lvl, slug="preview", **kwargs):
        self.set_default_kwargs(kwargs)

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        if slug == "speed_review":
            slug = "classic_review"

        # Retrieve level info
        retry_login = True
        level = {}

        while retry_login:
            is_anonymous_session = kwargs.get("is_anon", False)
            try:
                level = self.requestor.level(
                    idCourse,
                    lvl,
                    sessionid=kwargs["sessionid"],
                    csrftoken=kwargs["csrftoken"],
                )
            except requests.exceptions.HTTPError as e:
                # Try reauthenticate
                if e.response.status_code == 403 and is_anonymous_session and retry_login:
                    self.set_kwargs_session(kwargs, session=self.login_as_anonymous(reset=True))
                else:
                    raise e
            finally:
                retry_login = False

        # Start learning session (to be able to send results to memrise)
        if not is_anonymous_session and slug != "preview":
            csrftoken = self.requestor.level_learning_session(
                idCourse,
                slugCourse,
                sessionType=slug,
                sessionid=kwargs["sessionid"],
            )
            level.update(csrftoken)

        return level

    def level_multimedia(self, idCourse, slugCourse, lvl, **kwargs):
        self.set_default_kwargs(kwargs)

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        html = self.requestor.level_multimedia(
            idCourse,
            slugCourse,
            lvl,
            sessionid=kwargs["sessionid"],
        )
        return self.scraper.level_multimedia(html)

    def course_leaderboard(self, idCourse, period, **kwargs):
        self.set_default_kwargs(kwargs)

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        retry_login = True
        ldboard = {}
        while retry_login:
            try:
                ldboard = self.requestor.course_leaderboard(
                    idCourse,
                    period,
                    sessionid=kwargs["sessionid"],
                )
            except requests.exceptions.HTTPError as e:
                # Try reauthenticate
                if e.response.status_code == 403 and retry_login:
                    session = self.login_as_anonymous(reset=True)

                    self.set_kwargs_session(kwargs, session=session)
                else:
                    raise e
            finally:
                retry_login = False

        if "users" in ldboard:
            return {
                "rows": ldboard.get("users", []),
            }
        return ldboard

    # +-----------------------------------------------------
    # | USER
    # +-----------------------------------------------------
    def user(self, username, **kwargs):
        self.set_default_kwargs(kwargs)

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        html = self.requestor.user(username, sessionid=kwargs["sessionid"])

        return self.scraper.user(username, html)

    def user_mempals(self, tab, username, page=1, **kwargs):
        self.set_default_kwargs(kwargs)

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        html = self.requestor.user_mempals(tab, username, page, sessionid=kwargs["sessionid"])

        return self.scraper.user_mempals(username, page, html)

    def user_courses(self, tab, username, **kwargs):
        self.set_default_kwargs(kwargs)

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        html = self.requestor.user_courses(tab, username, sessionid=kwargs["sessionid"])

        return self.scraper.user_courses(html)

    # +-----------------------------------------------------
    # | EDIT COURSE
    # +-----------------------------------------------------
    def level_edit_get(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_edit_get(*args, **kwargs)

    def level_thing_add(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_add(*args, **kwargs)

    def level_thing_edit(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_edit(*args, **kwargs)

    def level_thing_upload(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_upload(*args, **kwargs)

    def level_thing_upload_remove(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_upload_remove(*args, **kwargs)

    def level_thing_remove(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_remove(*args, **kwargs)

    def level_thing_get(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_get(*args, **kwargs)

    def level_thing_alt_edit(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_alt_edit(*args, **kwargs)

    def level_multimedia_edit(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_multimedia_edit(*args, **kwargs)

    def course_edit_get(self, idCourse, slugCourse, **kwargs):
        self.set_default_kwargs(kwargs)

        data = self.requestor.course_edit_get(idCourse, slugCourse, sessionid=kwargs["sessionid"])
        html = data.pop("html")
        self.scraper.course_edit_get(data, html)

        return data


class DummyApiMemrise(DummyLoginMixin, DummyEditMixin, ApiMemrise):
    def create_requestor(self):
        return DummyApiRequestor()
