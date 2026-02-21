# ruff: noqa
from memrise.requestors import DummyApiRequestor
import logging
from cache import load_memcache_client
from .api import ApiMemrise
from .dummy import DummyLoginMixin, DummyEditMixin


logger = logging.getLogger(__name__)

memcache_client = load_memcache_client()


class CachedData(object):
    def __init__(self, cache_key, cache_timeout=60 * 60 * 24, read_cache=True):
        self.cache_key = cache_key
        self.cache_timeout = cache_timeout
        self.read_cache = read_cache

        self.data = None
        self.need_save = False

    def __enter__(self):
        value = self
        cache_key = self.cache_key

        # If reset is set to true, always consider that the value isn't set
        if not self.read_cache:
            self.need_save = True
        else:
            logger.debug(f"Get {cache_key}")
            self.need_save = False
            self.data = memcache_client.get(cache_key)

            # Gain the lock
            if self.data is None:
                with memcache_client.lock(cache_key) as retries:
                    # We didn't have the lock on the first try:
                    # ensure that the process previously having the lock didn't already set a value
                    if retries:
                        data = memcache_client.get(cache_key)
                        if data:
                            self.data = data
                            return value

                    # Couldn't get the data in our cache
                    logger.info(f"Miss {cache_key}")

        return value

    def update(self, data, need_save=True):
        self.data = data
        self.need_save = need_save

        return data

    def __exit__(self, ctx_type, ctx_value, ctx_traceback):
        if ctx_type is not None:
            logger.error(f"Could not retrieve {self.cache_key}", exc_info=ctx_value)

        elif self.need_save:
            memcache_client.set(self.cache_key, self.data, time=self.cache_timeout)

            logger.debug(f"Save {self.cache_key}")


class CachedApiMemrise(ApiMemrise):
    def login_as_anonymous(self, **kwargs):
        """
        Retrieve sessionid to retrieve content (using our own account)
        Is cached via memcached for 1day

        @param boolean reset - [False] Force cache refresh
        @return string       - sessionid
        """
        kwargs.setdefault("reset", False)

        with CachedData(cache_key="login_anon", read_cache=not kwargs["reset"]) as helper:
            session = helper.data or helper.update(data=super().login_as_anonymous())

            return session

    def courses(self, lang, page=1, cat="", query="", **kwargs):
        """
        Retrieve courses
        Is cached via memcached for 1day unless we're using a query
        """
        if not isinstance(page, int) and not page.isdigit():
            page = 1

        cache_key = f"{lang}_courses_{page}_{cat}"
        use_cache = query == ""

        with CachedData(cache_key=cache_key, read_cache=use_cache) as helper:
            courses = helper.data

            if courses is None:
                courses = helper.update(
                    data=super().courses(
                        lang=lang,
                        page=page,
                        cat=cat,
                        query=query,
                        **kwargs,
                    ),
                    need_save=use_cache,
                )

            return courses

    def categories(self, lang, **kwargs):
        """
        Retrieve categories
        Is cached via memcached for 1day
        """
        with CachedData(cache_key=f"{lang}_categories") as helper:
            categories = helper.data

            if categories is None:
                categories = helper.update(
                    data=super().categories(lang, **kwargs),
                )

            return categories

    def course(self, idCourse, slugCourse="", **kwargs):
        """
        Retrieve the course data
        Is cached via memcached for 1day unless we're logged in to (retrieve the progress / reviews)
        """
        self.set_default_kwargs(kwargs)

        if kwargs["sessionid"] and not kwargs.get("is_anon", False):
            return super().course(idCourse, slugCourse, **kwargs)

        with CachedData(cache_key=f"course_{idCourse}") as helper:
            course = helper.data

            if course is None:
                course = super().course(idCourse, slugCourse, **kwargs)
                helper.update(course)

            return course

    def level(self, idCourse, slugCourse, lvl, slug="preview", **kwargs):
        """
        Retrieve the level things
        Is cached via memcached for 1day unless we're logged in (retrieve the progress / reviews)
        """
        self.set_default_kwargs(kwargs)
        is_anonymous_session = not kwargs["sessionid"] or kwargs.get("is_anon", False)

        if is_anonymous_session:
            slug = "preview"
        elif slug == "speed_review":
            slug = "classic_review"

        cache_key = f"course_{idCourse}_{lvl}_{slug}"
        use_cache = is_anonymous_session

        with CachedData(cache_key=cache_key, read_cache=use_cache) as helper:
            level = helper.data

            if level is None:
                level = helper.update(
                    data=super().level(idCourse, slugCourse, lvl, slug, **kwargs),
                    need_save=use_cache,
                )

            return level

    def level_multimedia(self, idCourse, slugCourse, lvl, **kwargs):
        """
        Retrieve the level multimedia content
        Is cached via memcached for 1day
        """
        cache_key = f"course_{idCourse}_{lvl}_multimedia"

        with CachedData(cache_key=cache_key) as helper:
            data = helper.data

            if data is None:
                data = helper.update(
                    data=super().level_multimedia(idCourse, slugCourse, lvl, **kwargs),
                )

            return data

    def course_leaderboard(self, idCourse, period, **kwargs):
        """
        Retrieve the course leaderboard
        Is cached via memcached for 1day
        """
        cache_key = f"course_{idCourse}_learderboard_{period}"

        with CachedData(cache_key=cache_key) as helper:
            ldboard = helper.data

            if ldboard is None:
                ldboard = helper.update(
                    data=super().course_leaderboard(idCourse, period, **kwargs),
                )

            return ldboard

    def user(self, username, **kwargs):
        """
        Retrieve the user infos
        Is cached via memcached for 1hour
        """
        kwargs.setdefault("reset", False)

        cache_key = f"user_{username}"

        with CachedData(cache_key=cache_key, read_cache=not kwargs["reset"], cache_timeout=60 * 60) as helper:
            user = helper.data or helper.update(data=super().user(username, **kwargs))

            return user

    def user_mempals(self, tab, username, page=1, **kwargs):
        """
        Retrieve the users associated to an user (follower or following)
        Is cached via memcached for 1hour
        """
        if not isinstance(page, int):
            if page.isdigit():
                page = int(page)
            else:
                page = 1

        need_cache_page_max = True
        cache_key = f"user_{username}_{tab}"

        with CachedData(cache_key=cache_key, cache_timeout=60 * 60) as helper_page_max:
            max_page = helper_page_max.data

            # Check if the requested page is within the range
            if max_page is not None:
                need_cache_page_max = False
                if page > max_page:
                    page = max_page

            # Get the users for the given page
            cache_key_page = f"{cache_key}_{page}"
            with CachedData(cache_key=cache_key_page, cache_timeout=60 * 60) as helper:
                data = helper.data

                if data is None:
                    data = helper.update(
                        data=super().user_mempals(tab, username, page, **kwargs),
                    )

            # Save the max page
            if need_cache_page_max and data:
                max_page = data.get("lastpage", 1)

                helper_page_max.update(max_page)

            return data

    def user_courses(self, tab, username, **kwargs):
        """
        Retrieve the courses of an user (learning or teaching)
        Is cached via memcached for 1hour
        """
        cache_key = f"user_{username}_{tab}"

        with CachedData(cache_key=cache_key, cache_timeout=60 * 60) as helper:
            courses = helper.data

            if courses is None:
                courses = helper.update(
                    data=super().user_courses(tab, username, **kwargs),
                )

            return courses


class DummyCachedApiMemrise(DummyLoginMixin, DummyEditMixin, CachedApiMemrise):
    def create_requestor(self):
        return DummyApiRequestor()
