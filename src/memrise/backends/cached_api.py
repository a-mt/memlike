# ruff: noqa
from cache import mc
from .api import ApiMemrise


class CachedApiMemrise(ApiMemrise):
    def _login_as_anonymous(self, force=False):
        """
        Retrieve sessionid to retrieve content (using our own account)
        Is cached via memcached for 1day

        @param boolean force - [False] Force cache refresh
        @return string       - sessionid
        """
        cache_key = "login"
        session = mc.get(cache_key)
        if force or session is None:
            with mc.lock(cache_key) as retries:
                # Check if we set memcached while we were waiting for the lock
                if retries:
                    session = mc.get(cache_key)
                    if session:
                        return session["sessionid"]

                print("GET " + cache_key)
                session = super()._login_as_anonymous()
                mc.set(cache_key, session, time=60 * 60 * 24)

        return session["sessionid"]

    def courses(self, lang, page=1, cat="", query=""):
        """
        Retrieve courses
        Is cached via memcached for 1day unless we're using a query
        """
        if not isinstance(page, int) and not page.isdigit():
            page = 0

        # Check cache
        if query != "":
            return super().courses(lang=lang, page=page, cat=cat, query=query)

        cache_key = lang + "_courses_" + str(page) + "_" + cat
        courses = mc.get(cache_key)

        # Query memrise
        if courses is None:
            with mc.lock(cache_key) as retries:
                # Check if we set memcached while we were waiting for the lock
                if retries:
                    courses = mc.get(cache_key)
                    if courses:
                        return courses

                print("GET " + cache_key)
                courses = super().courses(lang=lang, page=page, cat=cat, query=query)
                mc.set(cache_key, courses, time=60 * 60 * 24)

        return courses

    def categories(self, lang):
        """
        Retrieve categories
        Is cached via memcached for 1day
        """
        cache_key = lang + "_categories"
        categories = mc.get(cache_key)

        # Query memrise
        if categories is None:
            with mc.lock(cache_key) as retries:
                # Check if we set memcached while we were waiting for the lock
                if retries:
                    categories = mc.get(cache_key)
                    if categories:
                        return categories

                print("GET " + cache_key)
                categories = super().categories(lang)
                mc.set(cache_key, categories, time=60 * 60 * 24)

        return categories

    def course(self, idCourse, slugCourse="", sessionid=False, csrftoken=None):
        """
        Retrieve the course data
        Is cached via memcached for 1day unless we're logged in to (retrieve the progress / reviews)
        """
        if sessionid:
            return super().course(idCourse, sessionid, csrftoken)

        cache_key = "course_" + idCourse
        course = mc.get(cache_key)

        if course is None:
            with mc.lock(cache_key) as retries:
                # Check if we set memcached while we were waiting for the lock
                if retries:
                    course = mc.get(cache_key)
                    if course:
                        return course

                print("GET " + cache_key)
                sessionid = self._login_as_anonymous()
                course = super().course(idCourse, sessionid, csrftoken)
                mc.set(cache_key, course, time=60 * 60 * 24)
        return course

    def level(self, idCourse, slugCourse, lvl, slug="preview", sessionid=False, csrftoken=None):
        """
        Retrieve the level things
        Is cached via memcached for 1day unless we're logged in (retrieve the progress / reviews)
        """
        if slug == "speed_review":
            slug = "classic_review"

        if sessionid:
            print("GET session" + "course_" + idCourse + "_" + lvl + "_" + slug)
            return super().level(idCourse, slugCourse, lvl, slug, sessionid, csrftoken)

        cache_key = "course_" + idCourse + "_" + lvl + "_" + slug
        level = mc.get(cache_key)

        if level is None:
            with mc.lock(cache_key) as retries:
                # Check if we set memcached while we were waiting for the lock
                if retries:
                    level = mc.get(cache_key)
                    if level:
                        return level

                print("GET " + cache_key)
                level = super().level(idCourse, slugCourse, lvl, slug, sessionid, csrftoken)
                mc.set(cache_key, level, time=60 * 60 * 24)
        return level

    def level_multimedia(self, idCourse, slugCourse, lvl):
        """
        Retrieve the level multimedia content
        Is cached via memcached for 1day
        """
        cache_key = "course_" + idCourse + "_" + lvl + "_multimedia"
        data = mc.get(cache_key)

        if data is None:
            with mc.lock(cache_key) as retries:
                # Check if we set memcached while we were waiting for the lock
                if retries:
                    data = mc.get(cache_key)
                    if data:
                        return data

                data = super().level_multimedia(idCourse, slugCourse, lvl)
                mc.set(cache_key, data, time=60 * 60 * 24)
        return data

    def course_leaderboard(self, idCourse, period):
        """
        Retrieve the course leaderboard
        Is cached via memcached for 1day
        """
        cache_key = "course_" + idCourse + "_learderboard_" + period
        ldboard = mc.get(cache_key)

        if ldboard is None:
            with mc.lock(cache_key) as retries:
                # Check if we set memcached while we were waiting for the lock
                if retries:
                    ldboard = mc.get(cache_key)
                    if ldboard:
                        return ldboard

                print("GET " + cache_key)
                ldboard = super().course_leaderboard(idCourse, period)
                mc.set(cache_key, ldboard, time=60 * 60 * 24)
        return ldboard

    def user(self, username, force=False):
        """
        Retrieve the user infos
        Is cached via memcached for 1hour
        """
        cache_key = "user_" + username
        user = None if force else mc.get(cache_key)

        if user is None:
            with mc.lock(cache_key) as retries:
                # Check if we set memcached while we were waiting for the lock
                if retries:
                    user = mc.get(cache_key)
                    if user:
                        return user

                print("GET " + cache_key)
                user = super().user(username, force)
                mc.set(cache_key, user, time=60 * 60)
        return user

    def user_mempals(self, tab, username, page=1):
        """
        Retrieve the users associated to an user (follower or following)
        Is cached via memcached for 1hour
        """
        if not isinstance(page, int):
            if page.isdigit():
                page = int(page)
            else:
                page = 1

        cache_key = "user_" + username + "_" + tab

        # Check if the requested page if no greater than the last page
        cache_last_page_num = True
        last_page_num = mc.get(cache_key)

        if last_page_num is not None:
            cache_last_page_num = False
            if page > last_page_num:
                page = last_page_num

        # Get the given page
        cache_key_page = cache_key + "_" + str(page)
        data = mc.get(cache_key_page)

        if data is None:
            with mc.lock(cache_key_page) as retries:
                # Check if we set memcached while we were waiting for the lock
                if retries:
                    data = mc.get(cache_key_page)
                    if data:
                        return data

                print("GET " + cache_key_page)
                data = super().user_mempals(tab, username, page)

                if cache_last_page_num:
                    mc.set(cache_key, data["lastpage"] if "lastpage" in data else 1, time=60 * 60)

                mc.set(cache_key + "_" + str(currentPage), data, time=60 * 60)

        return data

    def user_courses(self, tab, username):
        """
        Retrieve the courses of an user (learning or teaching)
        Is cached via memcached for 1hour
        """
        cache_key = "user_" + username + "_" + tab
        courses = mc.get(cache_key)

        if courses is None:
            with mc.lock(cache_key) as retries:
                # Check if we set memcached while we were waiting for the lock
                if retries:
                    courses = mc.get(cache_key)
                    if courses:
                        return courses

                print("GET " + cache_key)
                courses = super().user_courses(tab, username)

                mc.set(cache_key, courses, time=60 * 60)
        return courses
