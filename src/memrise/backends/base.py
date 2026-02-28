class Memrise:
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
    def courses(self, lang, page=1, cat="", query="", **kwargs):
        """
        Retrieve the list of courses for the given language, category, query string and page

        Testset: browse_cat-languages_scat-french_page-1.json
        @param string lang
        @param integer[optional] page - [1]
        @param string[optional] cat   - [""]
        @param string[optional] query - [""]
        @return dict - {page, content, has_next}
        """
        raise NotImplementedError("subclasses of Memrise must provide a courses() method")

    def categories(self, lang, **kwargs):
        """
        Retrieve the list of categories that have courses for the given language
        That is: for users that speak [LANG],
        list of categories that do have associated courses (catId: true)
        (starting from the root)

        Testset: courses.html
        @param string lang
        @return dict - {ID_COURSE: True}
        """
        raise NotImplementedError("subclasses of Memrise must provide a categories() method")

    # +-----------------------------------------------------
    # | COURSE
    # +-----------------------------------------------------
    def course(self, idCourse, slugCourse="", **kwargs):
        """
        Retrieve the info about a course

        Testset: course-1892646.html
        @param integer idCourse
        @return dict - {id, title, url, author, description, photo, levels, breadcrumb}
        """
        raise NotImplementedError("subclasses of Memrise must provide a course() method")

    def level(self, idCourse, slugCourse, lvl, slug="preview", **kwargs):
        """
        Retrieve the list of items of a level (wont work for multimedia)

        Testset: learning_session_learn.json
        @param integer idCourse
        @param integer|string lvl - index | "all"
        @param string slug
        @param string session
        @return dict - {learnables, progress, session_source_info, settings}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level() method")

    def level_multimedia(self, idCourse, slugCourse, lvl, **kwargs):
        """
        Retrieve the content of a multimedia level

        Testset: course-1892646_level-1_multimedia.html
        @param string idCourse - "43238"
        @param string slugCourse - "durham-university-medicine-year-one"
        @param integer lvl
        @return string
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_multimedia() method")

    def course_leaderboard(self, idCourse, period, **kwargs):
        """
        Retrieve the learderboard of a course (50 first)

        Testset: course_leaderboard.json
        @param integer idCourse
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
        @return dict - {content, nbCourse}
        """
        raise NotImplementedError("subclasses of Memrise must provide a user_courses() method")

    # +-----------------------------------------------------
    # | EDIT COURSE
    # +-----------------------------------------------------
    def level_edit_get(self, idLevel, **kwargs):
        """
        Retrieve the content of a level for the edit page
        May be multimedia or list of things

        @param string sessionid
        @param string idLevel
        @return dict - {success, rendered}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_edit_get() method")

    def level_thing_add(self, idLevel, data, **kwargs):
        """
        Add a thing is the given level

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string idLevel
        @param dict data - {columns: {"1":"a","2":"b","4":"plural"}, level_id: "16258912"}
        @return dict - {success, thing: {id, pool_id, columns, attributes}, rendered_thing}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_add() method")

    def level_thing_edit(self, idThing, cellId, cellValue, **kwargs):
        """
        Edit the value of a thing

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string idThing - "477757811"
        @param string cellId - "2"
        @param string cellValue - "b2"
        @return dict - {success}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_edit() method")

    def level_thing_upload(self, idThing, cellId, file, **kwargs):
        """
        Upload a file in the given thing

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string idThing - "477757811"
        @param string CellId - "3"
        @param file file - <filename value>
        @return dict - {success, rendered}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_upload() method")

    def level_thing_upload_remove(self, idThing, cellId, fileId, **kwargs):
        """
        Removes an uploaded file from the given thing

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string referer
        @param string idThing - "477757811"
        @param string cellId - "3"
        @param string fileId - "1"
        @return dict - {success, rendered}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_upload_remove() method")

    def level_thing_remove(self, idLevel, idThing, **kwargs):
        """
        Removes the given thing

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string idLevel - "16258912"
        @param string idThing - "477757811"
        @return dict - {success}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_remove() method")

    def level_thing_get(self, idThing, **kwargs):
        """
        Retrieves the data of the given thing

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string idThing - "477757811"
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_get() method")

    def level_thing_alt_edit(self, idThing, alts, column_key, **kwargs):
        """
        Edit the alternative answers of the given column for the given thing

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string idThing - "477757876"
        @param string alts - '["a2","a3"]'
        @param string column_key - "2"
        @return dict - {success}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_alt_edit() method")

    def level_multimedia_edit(self, idLevel, txt, **kwargs):
        """
        Edit the content of the given multimedia level

        @param string sessionid
        @param string csrftoken
        @param string referer
        @param string idLevel - "7030263"
        @param string txt - "img:http://cdni.wired.co.uk/620x413..."
        @return dict - {success, multimedia}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_multimedia_edit() method")

    def course_edit_get(self, idCourse, slugCourse, **kwargs):
        """
        Retrieve the content of a course for the edit page

        Testset: course_get_edit.html
        @param string sessionid
        @param string idCourse - "1892646"
        @param string slugCourse - "grammaire-le-groupe-nominal"
        """
        raise NotImplementedError("subclasses of Memrise must provide a course_edit_get() method")
