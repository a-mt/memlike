import requests
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
        @param string[optional] cat   - [""] category code
        @param string[optional] query - [""]
        @return dict - {page, content, has_next}
        """
        nbperpage = 12
        offset = (page-1)*nbperpage
        where = []

        # english -> 6
        source = variables.categories_code.get(lang_slug, 6)
        where.append(
            "source = " + web.db.sqlquote(source)
        )

        # german-2 -> 569.578.879.4 / german -> 569.578.879
        if cat:
            catID = variables.categories_code.get(cat, None)
            if catID is not None:
                get_parents = lambda x: variables.categories.get(x, {}).get("parents", [])

                # Filter on target or any child (starts with the same breadcrumb)
                target_breadcrumb = ".".join([
                    *get_parents(catID),
                    catID,
                ])
                where.append(
                    "target_breadcrumb LIKE '" + target_breadcrumb + "%'"
                )
            else:
                where = ["1 = 0"]

        store = web.database()
        qout = store.select(
            what="id, title AS name, slug, target AS category, user_username AS author, photo_url",
            where=web.db.SQLQuery.join(where, " AND "),
            tables="courses",
            limit=nbperpage+1,
            offset=offset,
            _test=True,
        )

        has_next = False
        res = []

        cursor = iter(store.query(qout, processed=True))
        for item in cursor:
            if cursor._index >= nbperpage:
                has_next = True
                break

            catID = item["category"]
            target = variables.categories.get(catID, None)

            if target is not None:
                item["target"] = {
                    "id": catID,
                    "slug": target["code"],
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
