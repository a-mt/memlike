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

    def courses(self, lang_slug, page=1, cat="", query="", **kwargs):
        """
        Retrieve courses
        Is cached via memcached for 1day unless we're using a query
        """
        cache_key = f"{lang_slug}_courses_{page}_{cat}"
        use_cache = query == ""

        with CachedData(cache_key=cache_key, read_cache=use_cache) as helper:
            courses = helper.data

            if courses is None:
                courses = helper.update(
                    data=super().courses(
                        lang_slug=lang_slug,
                        page=page,
                        cat=cat,
                        query=query,
                        **kwargs,
                    ),
                    need_save=use_cache,
                )

            return courses

    def categories(self, lang_slug, **kwargs):
        """
        Retrieve categories
        Is cached via memcached for 1day
        """
        with CachedData(cache_key=f"{lang_slug}_categories") as helper:
            categories = helper.data

            if categories is None:
                categories = helper.update(
                    data=super().categories(lang_slug, **kwargs),
                )

            return categories

    def course(self, course_id, course_slug="", **kwargs):
        """
        Retrieve the course data
        Is cached via memcached for 1day unless we're logged in to (retrieve the progress / reviews)
        """
        self.set_default_kwargs(kwargs)

        if kwargs["sessionid"] and not kwargs.get("is_anon", False):
            return super().course(course_id, course_slug, **kwargs)

        with CachedData(cache_key=f"course_{course_id}") as helper:
            course = helper.data

            if course is None:
                course = super().course(course_id, course_slug, **kwargs)
                helper.update(course)

            return course

    def level(self, course_id, course_slug, level_index, session_type="preview", **kwargs):
        """
        Retrieve the level things
        Is cached via memcached for 1day unless we're logged in (retrieve the progress / reviews)
        """
        self.set_default_kwargs(kwargs)
        is_anonymous_session = not kwargs["sessionid"] or kwargs.get("is_anon", False)

        if is_anonymous_session:
            session_type = "preview"
        elif session_type == "speed_review":
            session_type = "classic_review"

        cache_key = f"course_{course_id}_{level_index}_{session_type}"
        use_cache = is_anonymous_session

        with CachedData(cache_key=cache_key, read_cache=use_cache) as helper:
            level = helper.data

            if level is None:
                level = helper.update(
                    data=super().level(course_id, course_slug, level_index, session_type, **kwargs),
                    need_save=use_cache,
                )

            return level

    def level_multimedia(self, course_id, course_slug, level_index, **kwargs):
        """
        Retrieve the level multimedia content
        Is cached via memcached for 1day
        """
        cache_key = f"course_{course_id}_{level_index}_multimedia"

        with CachedData(cache_key=cache_key) as helper:
            data = helper.data

            if data is None:
                data = helper.update(
                    data=super().level_multimedia(course_id, course_slug, level_index, **kwargs),
                )

            return data

    def level_multimedia_edit(self, level_id, txt, **kwargs):
        result = super().level_multimedia_edit(level_id, txt, **kwargs)

        if kwargs.get("course_id", None) and kwargs.get("level_index", None):
            cache_key = "course_{course_id:s}_{level_index:s}_multimedia".format(
                course_id=kwargs["course_id"],
                level_index=kwargs["level_index"],
            )
            memcache_client.delete(cache_key)

        return result

    def course_leaderboard(self, course_id, period, **kwargs):
        """
        Retrieve the course leaderboard
        Is cached via memcached for 1day
        """
        cache_key = f"course_{course_id}_learderboard_{period}"

        with CachedData(cache_key=cache_key) as helper:
            ldboard = helper.data

            if ldboard is None:
                ldboard = helper.update(
                    data=super().course_leaderboard(course_id, period, **kwargs),
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
                if max_page < 1:
                    max_page = 1

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

    def my_progress_summary(self, sync_token=0, **kwargs):
        """
        Retrieve the progress of an user
        Is cached via memcached for 15 mmin
        """
        self.set_default_kwargs(kwargs)

        cache_key = f"progress_{kwargs['sessionid']}"

        with CachedData(cache_key=cache_key, cache_timeout=60 * 15) as helper:
            summary = helper.data

            if summary is None:
                summary = helper.update(
                    data=super().my_progress_summary(sync_token, **kwargs),
                )

            return summary


class DummyCachedApiMemrise(DummyLoginMixin, DummyEditMixin, CachedApiMemrise):
    def create_requestor(self):
        return DummyApiRequestor()
