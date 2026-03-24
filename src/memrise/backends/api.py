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

    def my_progress_summary(self, sync_token=0, **kwargs):
        self.set_default_kwargs(kwargs)

        summary = {}
        prev_sync_token = None

        while sync_token is not None and prev_sync_token != sync_token:
            prev_sync_token = sync_token

            data = self.my_progress(sync_token, **kwargs)

            for thing in data["thingusers"]:
                date, time = thing["last_date"].split("T", 1)
                month, day = date.rsplit("-", 1)

                if month not in summary:
                    summary[month] = {}
                if day not in summary[month]:
                    summary[month][day] = 0

                summary[month][day] += 1

            if len(data["thingusers"]) == 5000:
                sync_token = data.get("sync_token", None)

        return summary

    def my_progress(self, sync_token=0, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.my_progress(sync_token, sessionid=kwargs["sessionid"])

    # +-----------------------------------------------------
    # | LEARNING SESSION
    # +-----------------------------------------------------
    def learning_session_register_progress(self, data, referer=None, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.learning_session_register_progress(
            data,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
            referer=referer,
        )

    def learning_session_register_end(self, data, referer=None, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.learning_session_register_end(
            data,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
            referer=referer,
        )

    def reset_progress_level(self, data, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.reset_progress_level(
            data,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
        )

    # +-----------------------------------------------------
    # | COURSES
    # +-----------------------------------------------------
    def courses(self, lang_slug, page=1, cat="", query="", **kwargs):
        self.set_default_kwargs(kwargs)

        if not isinstance(page, int):
            page = int(page) if page.isdigit() else 1
        if page < 1:
            page = 1

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        return self.requestor.courses(lang_slug=lang_slug, page=page, cat=cat, query=query)

    def categories(self, lang_slug, **kwargs):
        self.set_default_kwargs(kwargs)
        self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        html = self.requestor.categories(
            lang_slug,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
        )
        return self.scraper.categories(html)

    # +-----------------------------------------------------
    # | COURSE
    # +-----------------------------------------------------
    def course(self, course_id, course_slug="", **kwargs):
        self.set_default_kwargs(kwargs)

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        html = self.requestor.course(
            course_id,
            course_slug,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
        )
        return self.scraper.course(course_id, html, is_logged_in=kwargs["sessionid"])

    def level(self, course_id, course_slug, level_index, session_type="preview", **kwargs):
        self.set_default_kwargs(kwargs)

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        if session_type == "speed_review":
            session_type = "review"
        elif session_type == "classic_review":
            session_type = "review"

        # Retrieve level info
        retry_request = True
        level = {}
        should_empty = False

        if session_type not in ("preview", "review", "learn"):
            session_type = "preview"

        while retry_request:
            is_anonymous_session = kwargs.get("is_anon", False)
            try:
                level = self.requestor.level(
                    course_id,
                    level_index,
                    session_type=session_type,
                    sessionid=kwargs["sessionid"],
                    csrftoken=kwargs["csrftoken"],
                )
                retry_request = False

            except requests.exceptions.HTTPError as e:
                # Try reauthenticate
                if e.response.status_code == 403:
                    if is_anonymous_session and retry_request:
                        self.set_kwargs_session(kwargs, session=self.login_as_anonymous(reset=True))
                        continue

                # Trying to learn but there's nothing more to learn:
                # retrieve the "session_source_info" but empty out the list of things to learn
                elif e.response.status_code == 400 and session_type == "learn":
                    session_type = "preview"
                    should_empty = True
                    continue

                raise e

        if should_empty:
            level["learnables"] = []
            level["progress"] = []

        return level

    def level_multimedia(self, course_id, course_slug, level_index, **kwargs):
        self.set_default_kwargs(kwargs)

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        html = self.requestor.level_multimedia(
            course_id,
            course_slug,
            level_index,
            sessionid=kwargs["sessionid"],
        )
        return self.scraper.level_multimedia(html)

    def course_leaderboard(self, course_id, period, **kwargs):
        self.set_default_kwargs(kwargs)

        if not kwargs["sessionid"]:
            self.set_kwargs_session(kwargs, session=self.login_as_anonymous())

        retry_login = True
        ldboard = {}
        while retry_login:
            try:
                ldboard = self.requestor.course_leaderboard(
                    course_id,
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
    def level_add(self, course_id, pool_id=None, **kwargs):
        self.set_default_kwargs(kwargs)

        # Add the level
        result = self.requestor.level_add(
            course_id,
            pool_id,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
        )
        result["id"] = None
        result["pool_id"] = pool_id

        if result["success"]:
            url = result.get("redirect_url", None)
            if url:
                m = url.split("#l_", 2)
                result["id"] = m[1] if len(m) == 2 else None

        return result

    def level_delete(self, level_id, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_delete(
            level_id,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
        )

    def level_title_edit(self, level_id, title, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_title_edit(
            level_id,
            title,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
        )

    def level_columns_edit(self, level_id, column_a, column_b, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_columns_edit(
            level_id,
            column_a,
            column_b,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
        )

    def level_get_editpage(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_get_editpage(*args, **kwargs)

    def level_thing_add(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_add(*args, **kwargs)

    def level_thing_update(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_update(*args, **kwargs)

    def level_thing_file_upload(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_file_upload(*args, **kwargs)

    def level_thing_file_delete(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_file_delete(*args, **kwargs)

    def level_thing_delete(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_delete(*args, **kwargs)

    def level_thing_get(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_get(*args, **kwargs)

    def level_thing_alt_update(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_thing_alt_update(*args, **kwargs)

    def level_multimedia_update(self, *args, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.level_multimedia_update(*args, **kwargs)

    def course_get_editpage(self, course_id, course_slug, **kwargs):
        self.set_default_kwargs(kwargs)

        data = self.requestor.course_get_editpage(course_id, course_slug, sessionid=kwargs["sessionid"])
        html = data.pop("html")
        self.scraper.course_get_editpage(data, html)

        return data

    def course_delete(self, course_id, referer=None, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.course_delete(
            course_id,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
            referer=referer,
        )

    def course_picture_upload(self, course_id, file, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.course_picture_upload(
            course_id,
            file,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
        )

    def course_add(self, data, referer=None, **kwargs):
        self.set_default_kwargs(kwargs)

        success_url, error_page = self.requestor.course_add(
            data={
                "name": data.get("name", ""),
                "tags": data.get("tags", ""),
                "description": data.get("description", ""),
                "short_description": data.get("short_description", ""),
                "csrfmiddlewaretoken": data.get("csrfmiddlewaretoken", ""),
                "target": data.get("category", ""),
                "source": data.get("language", ""),
            },
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
            referer=referer,
        )
        if error_page:
            errors = {}

            id_mapping = {
                "id_name": "name",
                "id_target": "category",
                "id_source": "language",
                "id_tags": "tags",
                "id_description": "description",
                "id_sdescription": "short_description",
            }
            for error in self.scraper.course_add(error_page):
                k = error["id"]
                name = id_mapping.get(k, None)
                if name is None:
                    name = "base." + k

                errors[name] = {
                    "msg": error["message"],
                    "type": "upstream",
                    "loc": (k,),
                }
            return None, errors

        return success_url, None


class DummyApiMemrise(DummyLoginMixin, DummyEditMixin, ApiMemrise):
    def create_requestor(self):
        return DummyApiRequestor()
