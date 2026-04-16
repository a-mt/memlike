import itertools
import logging
import variables
import web

from utils.crypto import gen_csrftoken
from utils.string import slugify
from .base import Memrise


logger = logging.getLogger(__name__)


class PostgresDB(Memrise):
    def reset_db(self):
        store = web.database()
        dbname = store.keywords.get("database", "postgres")

        assert dbname.endswith("_test"), 'Reset can only be executed on the test database (got "%s")' % dbname

        q = web.db.SQLQuery("CALL init_testset()")
        store.query(q, processed=True)

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
        qout = web.db.SQLQuery(
            [
                "WITH x AS (SELECT id, username, salt, password FROM users WHERE username = ",
                web.db.SQLParam(username),
                ")",
                "SELECT id, username FROM x WHERE crypt(",
                web.db.SQLParam(password),
                ", salt) = password",
            ]
        )

        res = store.query(qout, processed=True).first()
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
        res = store.select(
            what="id AS sessionid, username, photo",
            tables="users",
            where={
                "id": kwargs["sessionid"],
            },
        ).first()

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
            limit=nbperpage + 1,
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
                    "badge_count": None,
                },
                "mode_selector": {
                    "learn": {
                        "is_pro_mode": False,
                        "url": "/aprender/learn?course_id=6698294?recommendation_id=c8252e77-3fdf-4718-b8de-17581adc1b93",
                        "badge_count": 0,
                        "is_enabled": True,
                        "unlocked_state": "always_unlocked",
                    },
                    "classic_review": {
                        "is_pro_mode": False,
                        "url": "/aprender/review?course_id=6698294?recommendation_id=c8252e77-3fdf-4718-b8de-17581adc1b93",
                        "badge_count": 0,
                        "is_enabled": True,
                        "unlocked_state": "always_unlocked",
                    },
                    "speed_review": {
                        "is_pro_mode": False,
                        "url": "/aprender/speed?course_id=6698294?recommendation_id=c8252e77-3fdf-4718-b8de-17581adc1b93",
                        "badge_count": 0,
                        "is_enabled": True,
                        "unlocked_state": "always_unlocked",
                    },
                    "difficult_words": {
                        "is_pro_mode": True,
                        "url": "/aprender/difficult?course_id=6698294?recommendation_id=c8252e77-3fdf-4718-b8de-17581adc1b93",
                        "badge_count": 4,
                        "is_enabled": True,
                        "unlocked_state": "locked",
                    },
                    "listening_skills": {
                        "is_pro_mode": True,
                        "url": None,
                        "badge_count": 0,
                        "is_enabled": False,
                        "unlocked_state": "locked",
                    },
                    "video": {
                        "is_pro_mode": True,
                        "url": None,
                        "badge_count": 0,
                        "is_enabled": False,
                        "unlocked_state": "locked",
                    },
                },
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
                "percent_complete": 18,
            }

            if not item["photo_url"]:
                item["photo_url"] = "/static/img/course-4.png"

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
        offset = (page - 1) * nbperpage
        where = []

        # english -> 6
        source = variables.categories_slug.get(lang_slug, {}).get("id", 6)
        where.append("source = " + web.db.sqlquote(source))

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
            limit=nbperpage + 1,
            offset=offset,
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
                "percent_complete": 18,
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
    def _get_course_url(self, course_id, course_slug):
        return f"/community/course/{course_id}/{course_slug}/"

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
            "url": self._get_course_url(res["id"], res["slug"]),
            "author": res["user_username"],
            "description": res["description"],
            "photo": res["photo_url"] or "/static/img/course-4.png",
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
            course["breadcrumb"].append(
                {
                    "id": cat_id,
                    "slug": variables.categories_id.get(cat_id, {}).get("slug", ""),
                }
            )

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

    # +-----------------------------------------------------
    # | EDIT COURSE
    # +-----------------------------------------------------
    def course_add(self, data, referer=None, **kwargs):
        self.set_default_kwargs(kwargs)

        title = data.get("name", "")
        slug = slugify(title)

        source = data.get("language", "")
        target = data.get("category", "")
        target_breadcrumb = ".".join(self._get_breadcrumb(target))

        store = web.database()
        course_id = store.insert(
            tablename="courses",
            title=title,
            slug=slug,
            user_id=kwargs["sessionid"],
            target=target,
            target_breadcrumb=target_breadcrumb,
            source=source,
            description=data.get("description", ""),
            short_description=data.get("short_description", ""),
            tags=data.get("tags", ""),
        )
        # TODO handle errors?

        return {
            "success": True,
            "url": self._get_course_url(course_id, slug),
        }

    def course_delete(self, course_id, **kwargs):
        store = web.database()
        rowcount = store.delete(
            table="courses",
            where={
                "id": course_id,
                "user_id": kwargs["sessionid"],
            },
        )

        # TODO rowcount != 1?

    """
    def my_leaderboard(self, period, **kwargs):
    def my_progress_summary(self, sync_token=0, **kwargs):
    def my_progress(self, sync_token=0, **kwargs):
    def learning_session_register_progress(self, data, referer=None, **kwargs):
    def learning_session_register_end(self, data, referer=None, **kwargs):
    def reset_progress_level(self, data, **kwargs):
    def level(self, course_id, course_slug, level_index, session_type="preview", **kwargs):
    def level_multimedia(self, course_id, course_slug, level_index, **kwargs):
    def course_leaderboard(self, course_id, period, **kwargs):
    def user(self, username, **kwargs):
    def user_followers(self, username, page=1, **kwargs):
    def user_following(self, username, page=1, **kwargs):
    def user_mempals(self, tab, username, page=1, **kwargs):
    def user_teaching(self, username, **kwargs):
    def user_learning(self, username, **kwargs):
    def user_courses(self, tab, username, **kwargs):
    def level_add(self, course_id, pool_id=None, *args, **kwargs):
    def level_delete(self, level_id, *args, **kwargs):
    def level_title_edit(self, level_id, title, **kwargs):
    def level_column_edit(self, pool_id, column_key, label, show_after_tests=False):
    def level_attribute_edit(self, pool_id, column_key, label, show_at_tests=False):
    def level_columns_direction_edit(self, level_id, column_a, column_b):
    def level_get_editpage(self, level_id, **kwargs):
    def level_thing_add(self, level_id, data, **kwargs):
    def level_thing_update(self, thing_id, cell_id, cell_value, **kwargs):
    def level_thing_file_upload(self, thing_id, cell_id, file, **kwargs):
    def level_thing_file_delete(self, thing_id, cell_id, file_id, **kwargs):
    def level_thing_delete(self, level_id, thing_id, **kwargs):
    def level_thing_get(self, thing_id, **kwargs):
    def level_thing_alt_update(self, thing_id, alts, column_key, **kwargs):
    def level_multimedia_update(self, level_id, txt, **kwargs):
    def course_get_editpage(self, course_id, course_slug, **kwargs):
    """
