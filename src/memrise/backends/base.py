import settings
import web


class Memrise:
    def login_as_anonymous(self, **kwargs):
        """
        Retrieve sessionid to retrieve content (using our own account)

        @return string - sessionid
        """
        session = self.login(settings.MEMRISE_ANON_USERNAME, settings.MEMRISE_ANON_PASSWORD)
        session["is_anon"] = True
        return session

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
    def login(self, username, password):
        """
        Authenticate with the given username and password

        @param string username
        @param string password
        @return dict - {username, sessionid, csrftoken}
        """
        raise NotImplementedError("subclasses of Memrise must provide a login() method")

    # +-----------------------------------------------------
    # | CURRENT USER
    # +-----------------------------------------------------
    def whoami(self, **kwargs):
        """
        Retrieve the username and photo of current user

        Testset: profile_settings.html
        @param string sessionid
        @return dict - {sessionid, username, photo}
        """
        raise NotImplementedError("subclasses of Memrise must provide a whoami() method")

    def whatistudy(self, offset=0, **kwargs):
        """
        Retrieve the list of courses of current user

        Testset: dashboard_courses.json
        @param string sessionid
        @return list of pages - [{
                offset,
                has_more_pages,
                courses: [{
                    id,
                    name,
                    slug,
                    is_official,
                    photo_url,
                    next_session,
                    goal,
                    progress,
                }]
            }]
        """
        raise NotImplementedError("subclasses of Memrise must provide a whatistudy() method")

    def my_leaderboard(self, period, **kwargs):
        """
        Retrieve the learderboard of the current user (50 first)

        Testset: profile_leaderboard.json
        @param string sessionid
        @param string period - month, week, alltime
        @return dict - {
            rows: [{
                position,
                points,
                username,
                uid,
                photo,
                is_premium,
                following,
            }]}
        """
        raise NotImplementedError("subclasses of Memrise must provide a my_leaderboard() method")

    def my_progress_summary(self, sync_token=0, **kwargs):
        """
        Count progress thingusers by month/day
        @param int sync_token - 0 or timestamp
        @return dict - ie {{'2025-09': {'12': 222, '20': 157, '23': 19, '24': 37}}
        """
        raise NotImplementedError("subclasses of Memrise must provide a my_progress_summary() method")

    def my_progress(self, sync_token=0, **kwargs):
        """
        Testset: progress1.json
        @param int sync_token - 0 or timestamp
        @return dict - {thingusers: [], sync_token}
        """
        raise NotImplementedError("subclasses of Memrise must provide a my_progress() method")

    # +-----------------------------------------------------
    # | LEARNING SESSION
    # +-----------------------------------------------------

    def learning_session_register_progress(self, data, referer=None, **kwargs):
        """
        Register progress

        Testset: course-6698294_garden_learn_registerprogress_{request,response}.json
        @param dict data - {events: [{learnable_id, box_template...}]}
        @param string sessionid
        @param string csrftoken
        @param string referer
        @return dict - Retrieved JSON
        """
        raise NotImplementedError("subclasses of Memrise must provide a learning_session_register_progress() method")

    def learning_session_register_end(self, data, referer=None, **kwargs):
        """
        Register end

        Testset: course-6698294_garden_learn_sessionend_{request,response}.json
        @param dict data - {session_points,session_type...}
        @param string sessionid
        @param string csrftoken
        @param string referer
        @return dict - Retrieved JSON
        """
        raise NotImplementedError("subclasses of Memrise must provide a learning_session_register_end() method")

    def reset_progress_level(self, data, **kwargs):
        """
        Reset progress

        @param dict data - {level_id: 1}
        @param string sessionid
        @param string csrftoken
        """
        raise NotImplementedError("subclasses of Memrise must provide a reset_progress_level() method")

    # +-----------------------------------------------------
    # | COURSES
    # +-----------------------------------------------------
    def courses(self, lang_slug, page=1, cat="", query="", **kwargs):
        """
        Retrieve the list of courses for the given language, category, query string and page

        Testset: browse_cat-languages_scat-french_page-1.json
        @param string lang_slug - english
        @param integer[optional] page - [1]
        @param string[optional] cat   - [""]
        @param string[optional] query - [""]
        @return dict - {page, content, has_next}
        """
        raise NotImplementedError("subclasses of Memrise must provide a courses() method")

    def categories_to_display(self, lang_slug, **kwargs):
        """
        Retrieve the list of categories that have courses for the given language
        That is: for users that speak [LANG],
        list of categories that do have associated courses (catId: true)
        (starting from the root)

        Testset: courses.html
        @param string lang_slug - english
        @return dict - {ID_COURSE: True}
        """
        raise NotImplementedError("subclasses of Memrise must provide a categories() method")

    # +-----------------------------------------------------
    # | COURSE
    # +-----------------------------------------------------
    def course(self, course_id, course_slug="", **kwargs):
        """
        Retrieve the info about a course

        Testset: course-1892646.html
        @param integer course_id
        @return dict - {id, title, url, author, description, photo, levels, breadcrumb}
        """
        raise NotImplementedError("subclasses of Memrise must provide a course() method")

    def level(self, course_id, course_slug, level_index, session_type="preview", **kwargs):
        """
        Retrieve the list of items of a level (wont work for multimedia)

        Testset: learning_session_learn.json
        @param integer course_id
        @param integer|string level_index - index | "all"
        @param string session_type - preview|learn|classic_review|speed_review
        @param string session
        @return dict - {learnables, progress, session_source_info, settings}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level() method")

    def level_multimedia(self, course_id, course_slug, level_index, **kwargs):
        """
        Retrieve the content of a multimedia level

        Testset: course-1892646_level-1_multimedia.html
        @param string course_id - "43238"
        @param string course_slug - "durham-university-medicine-year-one"
        @param integer level_index
        @return string
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_multimedia() method")

    def course_leaderboard(self, course_id, period, **kwargs):
        """
        Retrieve the learderboard of a course (50 first)

        Testset: course_leaderboard.json
        @param integer course_id
        @param string period - month, week, alltime
        @return dict - {rows: [{position, points, uid, photo, username, is_premium}]}
        """
        raise NotImplementedError("subclasses of Memrise must provide a course_leaderboard() method")

    # +-----------------------------------------------------
    # | USER
    # +-----------------------------------------------------
    def user(self, username, **kwargs):
        """
        Retrieve the info about a user

        Testset: user_courses.html
        @param string username
        @param boolean[optional] force - [false] Get data from Memrise even if already cached
        @return dict - {username, photo, rank, stats}
        """
        raise NotImplementedError("subclasses of Memrise must provide a user() method")

    def user_followers(self, username, page=1, **kwargs):
        """
        Retrieve the list of followers of a user

        Testset: user_mempals_followers.html
        @param string username
        @param integer page - [1]
        @return dict - {page, lastpage, has_next, users}
        """
        return self.user_mempals("followers", username, page, **kwargs)

    def user_following(self, username, page=1, **kwargs):
        """
        Retrieve the list of followed users

        Testset: user_mempals_following.html
        @param string username
        @param integer page - [1]
        @return dict - {page, lastpage, has_next, users}
        """
        return self.user_mempals("following", username, page, **kwargs)

    def user_mempals(self, tab, username, page=1, **kwargs):
        """
        Retrieve the users associated to an user (follower or following)

        @param string mempals - followers | following
        @param string username
        @param integer page - [1]
        @return dict - {page, lastpage, has_next, users}
        """
        raise NotImplementedError("subclasses of Memrise must provide a user_mempals() method")

    def user_teaching(self, username, **kwargs):
        return self.user_courses("teaching", username, **kwargs)

    def user_learning(self, username, **kwargs):
        return self.user_courses("learning", username, **kwargs)

    def user_courses(self, tab, username, **kwargs):
        """
        Retrieve the courses of an user

        Testset: user_courses_teaching.html
        @param string tab - teaching | learning
        @param string username
        @return dict - {content, nb_courses}
        """
        raise NotImplementedError("subclasses of Memrise must provide a user_courses() method")

    # +-----------------------------------------------------
    # | EDIT COURSE
    # +-----------------------------------------------------
    def level_add(self, course_id, pool_id=None, *args, **kwargs):
        """
        Add a new level in the given course
        Either for a list of things (pool_id!=None) or multimedial level

        @param string course_id
        @param string pool_id
        @return dict - {success, redirect_url}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_add() method")

    def level_delete(self, level_id, *args, **kwargs):
        """
        Delete the given level

        @param string level_id
        @return dict - {success}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_delete() method")

    def level_title_edit(self, level_id, title, **kwargs):
        """
        Delete the given level

        @param string level_id
        @param string title
        @return dict - {success}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_title_edit() method")

    def pool_column_edit(self, pool_id, column_key, label, show_after_tests=False):
        """
        Rename a column

        @param string pool_id
        @param string column_key
        @param string label
        @param boolean show_at_tests
        @return dict - {saved}
        """
        raise NotImplementedError("subclasses of Memrise must provide a pool_column_edit() method")

    def pool_attribute_edit(self, pool_id, column_key, label, show_at_tests=False):
        """
        Rename an attribute

        @param string pool_id
        @param string column_key
        @param string label
        @param boolean show_at_tests
        @return dict - {saved}
        """
        raise NotImplementedError("subclasses of Memrise must provide a pool_attribute_edit() method")

    def level_direction_edit(self, level_id, column_a, column_b):
        """
        Set which columns are acting as question and answer

        @param string level_id
        @param string column_a - 1 Which column is the learning_element
        @param string column_b - 2 Which column is the definition_element
        @return dict - {success}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_direction_edit() method")

    def level_get_editpage(self, level_id, **kwargs):
        """
        Retrieve the content of a level for the edit page
        May be multimedia or list of things

        @param string sessionid
        @param string level_id
        @return dict - {success, rendered}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_get_editpage() method")

    def level_thing_add(self, level_id, data, **kwargs):
        """
        Add a thing is the given level

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string level_id
        @param dict data - {columns: {"1":"a","2":"b","4":"plural"}, level_id: "16258912"}
        @return dict - {success, thing: {id, pool_id, columns, attributes}, rendered_thing}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_add() method")

    def level_thing_update(self, thing_id, cell_id, cell_value, **kwargs):
        """
        Edit the value of a thing

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string thing_id - "477757811"
        @param string cell_id - "2"
        @param string cell_value - "b2"
        @return dict - {success}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_update() method")

    def level_thing_file_upload(self, thing_id, cell_id, file, **kwargs):
        """
        Upload a file in the given thing

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string thing_id - "477757811"
        @param string cell_id - "3"
        @param file file - <filename value>
        @return dict - {success, rendered}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_file_upload() method")

    def level_thing_file_delete(self, thing_id, cell_id, file_id, **kwargs):
        """
        Removes an uploaded file from the given thing

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string referer
        @param string thing_id - "477757811"
        @param string cell_id - "3"
        @param string file_id - "1"
        @return dict - {success, rendered}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_file_delete() method")

    def level_thing_delete(self, level_id, thing_id, **kwargs):
        """
        Removes the given thing

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string level_id - "16258912"
        @param string thing_id - "477757811"
        @return dict - {success}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_delete() method")

    def level_thing_get(self, thing_id, **kwargs):
        """
        Retrieves the data of the given thing

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string thing_id - "477757811"
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_get() method")

    def level_thing_alt_update(self, thing_id, alts, column_key, **kwargs):
        """
        Edit the alternative answers of the given column for the given thing

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string thing_id - "477757876"
        @param string alts - '["a2","a3"]'
        @param string column_key - "2"
        @return dict - {success}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_alt_update() method")

    def level_multimedia_update(self, level_id, txt, **kwargs):
        """
        Edit the content of the given multimedia level

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string level_id - "7030263"
        @param string txt - "img:http://cdni.wired.co.uk/620x413..."
        @return dict - {success, multimedia}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_multimedia_update() method")

    def course_get_editpage(self, course_id, course_slug, **kwargs):
        """
        Retrieve the content of a course for the edit page

        Testset: course_get_edit.html
        @param string sessionid
        @param string course_id - "1892646"
        @param string course_slug - "grammaire-le-groupe-nominal"
        """
        raise NotImplementedError("subclasses of Memrise must provide a course_get_editpage() method")

    def course_delete(self, course_id, **kwargs):
        """
        Delete a course

        @param string course_id
        """
        raise NotImplementedError("subclasses of Memrise must provide a course_delete() method")

    def course_add(self, data, **kwargs):
        """
        Add a course

        @param dict data - {name, tags, description, short_description, csrfmiddlewaretoken, category, language}
        """
        raise NotImplementedError("subclasses of Memrise must provide a course_add() method")
