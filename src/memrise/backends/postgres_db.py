import requests
import itertools
import logging
import settings
import variables
import web

from memrise.scrapers import Scraper
from memrise.requestors import ApiRequestor, DummyApiRequestor
from pydantic_core import ValidationError
from utils.crypto import gen_csrftoken
from .dummy import DummyLoginMixin, DummyEditMixin
from .base import Memrise


logger = logging.getLogger(__name__)


class PostgresDB(Memrise):

    # +-----------------------------------------------------
    # | AUTH
    # +-----------------------------------------------------
    def login(self, username, password):
        """
        Authenticate with the given username and password

        @param string username
        @param string password
        @return dict - {username, sessionid, csrftoken}
        """

        # Check if the user exists
        store = web.database()

        # with x as (select username, salt, password from users where username = 'bob') select username from x where crypt('pass', salt) = password;
        qout = web.db.SQLQuery([
            "WITH x AS (SELECT id, username, salt, password FROM users WHERE username = ", web.db.SQLParam(username), ")",
            "SELECT id, username FROM x WHERE crypt(", web.db.SQLParam(password), ", salt) = password"
        ])

        res  = store.query(qout, processed=True).first()
        if res is None:
            return None

        # Create a new CSRF token
        csrftoken = gen_csrftoken(web.ctx.get("ip", "0.0.0.0"), web.config.session_parameters.secret_key)
        res["csrftoken"] = csrftoken
        res["sessionid"] = res["id"]

        return dict(res)

    # +-----------------------------------------------------
    # | CURRENT USER
    # +-----------------------------------------------------
    def whoami(self, **kwargs):
        self.set_default_kwargs(kwargs)

        store = web.database()
        res = store.select(what="id AS sessionid, username, photo", tables="users", where={
            "id": kwargs["sessionid"],
        }).first()

        if not res.get("photo", ""):
            res["photo"] = "/static/img/empty-avatar-1.png"

        return dict(res) if res else None

    def whatistudy(self, offset=0, **kwargs):
        self.set_default_kwargs(kwargs)
        nbperpage = 12

        store = web.database()
        cursor = store.select(
            what="id, title AS name, slug, photo_url",
            tables="courses",
            limit=nbperpage+1,
            offset=offset,
        )
        res = []

        for item in cursor:
            if cursor._index >= nbperpage:
                has_more_pages = True
                break

            item["is_official"] = 0
            item["next_session"] = {
                "single_continue": {
                    "session_type": "learn",
                    "is_pro_mode": False,
                    "url": "/aprender/learn?course_id=6698294?recommendation_id=c8252e77-3fdf-4718-b8de-17581adc1b93",
                    "unlocked_state": "always_unlocked",
                    "badge_count": None
                },
                "mode_selector": {
                    "learn": {
                        "is_pro_mode": False,
                        "url": "/aprender/learn?course_id=6698294?recommendation_id=c8252e77-3fdf-4718-b8de-17581adc1b93",
                        "badge_count": 0,
                        "is_enabled": True,
                        "unlocked_state": "always_unlocked"
                    },
                    "classic_review": {
                        "is_pro_mode": False,
                        "url": "/aprender/review?course_id=6698294?recommendation_id=c8252e77-3fdf-4718-b8de-17581adc1b93",
                        "badge_count": 0,
                        "is_enabled": True,
                        "unlocked_state": "always_unlocked"
                    },
                    "speed_review": {
                        "is_pro_mode": False,
                        "url": "/aprender/speed?course_id=6698294?recommendation_id=c8252e77-3fdf-4718-b8de-17581adc1b93",
                        "badge_count": 0,
                        "is_enabled": True,
                        "unlocked_state": "always_unlocked"
                    },
                    "difficult_words": {
                        "is_pro_mode": True,
                        "url": "/aprender/difficult?course_id=6698294?recommendation_id=c8252e77-3fdf-4718-b8de-17581adc1b93",
                        "badge_count": 4,
                        "is_enabled": True,
                        "unlocked_state": "locked"
                    },
                    "listening_skills": {
                        "is_pro_mode": True,
                        "url": None,
                        "badge_count": 0,
                        "is_enabled": False,
                        "unlocked_state": "locked"
                    },
                    "video": {
                        "is_pro_mode": True,
                        "url": None,
                        "badge_count": 0,
                        "is_enabled": False,
                        "unlocked_state": "locked"
                    }
                }
            }
            item["goal"] = None
            item["progress"] = {
                "id": 6698294,
                "name": "German vocab",
                "size": 274,
                "due_review": 0,
                "learned": 50,
                "ignored": 0,
                "difficult": 4,
                "completed_this_session": False,
                "percent_complete": 18
            }

            if not item["photo_url"]:
                item["photo_url"] = "https://static.memrise.com/garden/img/placeholders/course-4.png"

            res.append(item)

        # Check if there are still items
        has_more_pages = False
        offset += nbperpage

        yield {
            "courses": res,
            "has_more_pages": has_more_pages,
            "next_offset": offset if has_more_pages else None,
        }

    # +-----------------------------------------------------
    # | COURSES
    # +-----------------------------------------------------
    def courses(self, lang_slug, page=1, cat="", query="", **kwargs):
        """
        Retrieve the list of courses for the given language, category, query string and page

        Testset: browse_cat-languages_scat-french_page-1.json
        @param string lang_slug - english
        @param integer[optional] page - [1]
        @param string[optional] cat   - [""] category slug
        @param string[optional] query - [""]
        @return dict - {page, content, has_next}
        """
        nbperpage = 12
        offset = (page-1)*nbperpage
        where = []

        # english -> 6
        source = variables.categories_slug.get(lang_slug, {}).get("id", 6)
        where.append(
            "source = " + web.db.sqlquote(source)
        )

        # german-2 -> LIKE 569.578.879.4% / german -> LIKE 569.578.879%
        if cat:
            condition = self._get_where_breadcrumb_like(cat)
            if condition is not None:
                where.append(condition)
            else:
                where = ["1 = 0"]

        store = web.database()
        query = store.select(
            what="id, title AS name, slug, target AS category, photo_url",
            where=web.db.SQLQuery.join(where, " AND "),
            tables="courses",
            limit=nbperpage+1,
            offset=offset
        )

        has_next = False
        res = []

        for item in query:
            if query._index >= nbperpage:
                has_next = True
                break

            cat_id = item["category"]
            target = variables.categories_id.get(cat_id, None)

            if target is not None:
                item["target"] = {
                    "id": cat_id,
                    "slug": target["slug"],
                    "photo_url": target.get("photo_url", ""),
                }

            item["is_official"] = 0
            item["progress"] = {
                "id": 6698294,
                "name": "German vocab",
                "size": 274,
                "due_review": 0,
                "learned": 50,
                "ignored": 0,
                "difficult": 4,
                "completed_this_session": False,
                "percent_complete": 18
            }
            res.append(item)

        content = web.config.template.prender.ajax_dashboard(res, offset)["__body__"]

        return {
            "page": page,
            "content": content.strip(),
            "has_next": has_next,
        }

    def _get_breadcrumb(self, cat_id):
        """
        :param int cat_id
        :return list(id)
        """
        parents = variables.categories_id.get(cat_id, {}).get("parents", [])

        # Filter on target or any child (starts with the same breadcrumb)
        return [*parents, cat_id]

    def _get_where_breadcrumb_like(self, category_slug):
        """
        Build the where condition to filter on a category, or any child category
        ie
            german-2 -> LIKE 569.578.879.4%
            german -> LIKE 569.578.879%

        :param string category_slug
        :return string|None condition
        """

        # Filter on target or any child (starts with the same breadcrumb)
        category = variables.categories_slug.get(category_slug, None)
        if category is not None:
            ids = self._get_breadcrumb(category["id"])

            return "target_breadcrumb LIKE '" + ".".join(ids) + "%'"

    def categories_to_display(self, lang_slug, **kwargs):
        where = []
        condition = self._get_where_breadcrumb_like(lang_slug)
        if condition is not None:
            where = [condition]

        store = web.database()
        query = store.select(
            what="DISTINCT target, target_breadcrumb",
            where=web.db.SQLQuery.join(where, " AND "),
            tables="courses",
        )

        categories = {}
        for item in query:
            if item["target"] in categories:
                continue

            for cat_id in item["target_breadcrumb"].split("."):
                categories[cat_id] = True

        return categories

    # +-----------------------------------------------------
    # | COURSE
    # +-----------------------------------------------------
    def course(self, course_id, course_slug="", **kwargs):
        store = web.database()
        res = store.select(
            what="id, title, slug, user_username, description, photo_url, source, target",
            where={
                "id": course_id,
            },
            tables="courses",
        ).first()

        if res is None:
            return

        course = {
            "id": course_id,
            "title": res["title"],
            "url": f"/community/course/{res['id']}/{res['slug']}/",
            "author": res["user_username"],
            "description": res["description"],
            "photo": res["photo_url"] or "https://static.memrise.com/garden/img/placeholders/course-4.png",
            "levels": {},
            "nb_things": 0,
            "breadcrumb": [],
            "source": None,
            "target": None,
        }

        # Adding source, target
        def add_language(course, cat_id, to_key="source"):
            """
            Add source / target language to course if the given cat_id is a language
            ie
                "source": {
                    "slug": "afrikaans",
                    "photo_url": "/static/img/language_photos/Afrikaans.png",
                    "id": "62",
                    "language_code": None
                },
            """
            category = variables.categories_id.get(cat_id, {})
            category_slug = category.get("slug", None)

            lang = variables.categories_slug.get(category_slug, None)
            if lang is not None:
                course[to_key] = {
                    "id": cat_id,
                    "slug": category_slug,
                    "photo_url": lang.get("photo_url", None),
                    "language_code": lang.get("language_code", None),
                }

        add_language(course, res["source"], to_key="source")
        add_language(course, res["target"], to_key="target")

        # Adding breadcrumb
        for cat_id in itertools.chain(
            [res["source"]],
            self._get_breadcrumb(res["target"]),
        ):
            course["breadcrumb"].append({
                "id": cat_id,
                "slug": variables.categories_id.get(cat_id, {}).get("slug", ""),
            })

        # Adding levels
        query = store.select(
            what="id, idx, title AS name, pool_id, type, nb_things",
            where={
                "course_id": course_id,
            },
            tables="course_levels",
        )
        for item in query:
            item.status = "TODO"  #  Bereit zum lernen / Bereit zum Wiederholen 

            course["levels"][str(item["idx"])] = dict(item)
            course["nb_things"] += item["nb_things"]

        # Adding stats
        is_logged_in = kwargs["sessionid"] and not kwargs.get("is_anon", False)
        if is_logged_in:
            course["stats"] = {
                "nb_things": 4,
                "learned": 3,
                "review": 2,
                "ignored": 1,
                "percent_complete": 99,
            }

        return course
