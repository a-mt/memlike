import requests, re, sys
import time
import json
import settings
import web

from cache import mc
from bs4 import BeautifulSoup, Tag
from variables import categories_code, levels


class Memrise:

    #+-----------------------------------------------------
    #| AUTH
    #+-----------------------------------------------------
    def login(self, username, password):
        """
            Authenticate with the given username and password

            @param string username
            @param string password
            @return dict - {username, sessionid, csrftoken}
        """
        raise NotImplementedError("subclasses of Memrise must provide a login() method")

    def whoami(self, sessionid):
        """
            Retrieve the username and photo of current user

            Testset: settings.html
            @param string sessionid
            @return dict - {sessionid, username, photo}
        """
        raise NotImplementedError("subclasses of Memrise must provide a whoami() method")

    def whatistudy(self, sessionid):
        """
            Retrieve the list of courses of current user

            Testset: dashboard_courses.json
            @param string sessionid
            @return list of pages > courses - [[{id, name, slug, is_official,photo_url, next_session, goal, progress}]]
        """
        raise NotImplementedError("subclasses of Memrise must provide a whatistudy() method")

    def my_leaderboard(self, sessionid, period):
        """
            Retrieve the learderboard of the current user (50 first)

            Testset: profile_leaderboard.html
            @param string sessionid
            @param string period - month, week, alltime
            @return dict - {rows: [{position, points, username, uid, photo, is_premium, following}]}
        """
        raise NotImplementedError("subclasses of Memrise must provide a my_leaderboard() method")

    def track_progress(self, path, data, sessionid, csrftoken, referer):
        """
            Post play progress

            Testset: progress_register_{request,response}.json
            @param string path - register | session_end
            @param dict data
            @param string sessionid
            @param string csrftoken
            @param string referer
            @return dict
        """
        raise NotImplementedError("subclasses of Memrise must provide a track_progress() method")

    #+-----------------------------------------------------
    #| COURSES
    #+-----------------------------------------------------
    def courses(self, lang, page=1, cat="", query=""):
        """
            Retrieve the list of courses for the given language, category, query string and page

            Testset: browse_cat-languages_scat-french_page-2.json
            @param string lang
            @param integer[optional] page - [1]
            @param string[optional] cat   - [""]
            @param string[optional] query - [""]
            @return dict - {page, content, has_next}
        """
        raise NotImplementedError("subclasses of Memrise must provide a courses() method")

    #+-----------------------------------------------------
    #| CATEGORIES
    #+-----------------------------------------------------
    def categories(self, lang):
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

    #+-----------------------------------------------------
    #| COURSE
    #+-----------------------------------------------------
    def course(self, id, sessionid=False, csrftoken=None):
        """
            Retrieve the info about a course

            Testset: course-6698294.html
            @param integer id
            @return dict - {id, title, url, author, description, photo, levels, breadcrumb}
        """
        raise NotImplementedError("subclasses of Memrise must provide a course() method")

    #+-----------------------------------------------------
    #| COURSE > LEVEL
    #+-----------------------------------------------------
    def level(self, idCourse, slugCourse, lvl, slug="preview", sessionid=False, csrftoken=None, retry=True):
        """
            Retrieve the list of items of a level (wont work for multimedia)

            @param integer idCourse
            @param integer|string lvl - index | "all"
            @param string slug
            @param string session
            @return dict - {learnables, progress, session_source_info, settings}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level() method")

    def level_multimedia(self, urlCourse, lvl):
        """
            Retrieve the content of a multimedia level

            Testset: level_multimedia.html
            @param string urlCourse - ex "/course/43238/durham-university-medicine-year-one/"
            @param integer lvl
            @return string
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_multimedia() method")

    #+-----------------------------------------------------
    #| COURSE > LEADERBOARD
    #+-----------------------------------------------------
    def course_leaderboard(self, idCourse, period):
        """
            Retrieve the learderboard of a course (50 first)

            Testset: course_leaderboard.json
            @param integer idCourse
            @param string period - month, week, alltime
            @return dict - {rows: [{position, points, uid, photo, username, is_premium}]}
        """
        raise NotImplementedError("subclasses of Memrise must provide a course_leaderboard() method")

     #+-----------------------------------------------------
    #| USER
    #+-----------------------------------------------------
    def user(self, username, force=False):
        """
            Retrieve the info about a user

            Testset: user_courses.html
            @param string username
            @param boolean[optional] force - [false] Get data from Memrise even if already cached
            @return dict - {username, photo, rank, stats}
        """
        raise NotImplementedError("subclasses of Memrise must provide a user() method")

    def user_followers(self, username, page=1):
        """
            Retrieve the list of followers of a user

            Testset: user_mempals_followers.html
            @param string mempals - followers  following
            @param string username
            @param integer page - [1]
            @return dict - {page, lastpage, has_next, users}
        """
        raise NotImplementedError("subclasses of Memrise must provide a user_followers() method")

    def user_following(self, username, page=1):
        """
            Retrieve the list of followers of followed users

            Testset: user_mempals_following.html
            @param string mempals - followers  following
            @param string username
            @param integer page - [1]
            @return dict - {page, lastpage, has_next, users}
        """
        raise NotImplementedError("subclasses of Memrise must provide a user_following() method")

    #+-----------------------------------------------------
    #| USER's COURSES
    #+-----------------------------------------------------
    def user_teaching(self, username):
        return self.user_courses("teaching", username)

    def user_learning(self, username):
        return self.user_courses("learning", username)

    def user_courses(self, tab, username):
        """
            Retrieve the courses of an user

            @param string tab - teaching | learning
            @param string username
            @return dict - {content, nbCourse}
        """
        raise NotImplementedError("subclasses of Memrise must provide a user_courses() method")

    #+-----------------------------------------------------
    #| EDIT
    #+-----------------------------------------------------
    def level_edit_get(self, sessionid, idLevel):
        """
            Retrieve the content of a level for the edit page
            May be multimedia or list of things

            @param string sessionid
            @param string idLevel
            @return dict - {success, rendered}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_edit_get() method")

    def level_thing_add(self, sessionid, csrftoken, referer, idLevel, data):
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

    def level_thing_edit(self, sessionid, csrftoken, referer, idThing, cellId, cellValue):
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

    def level_thing_upload(self, sessionid, csrftoken, referer, idThing, cellId, file):
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

    def level_thing_upload_remove(self, sessionid, csrftoken, referer, idThing, cellId, fileId):
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

    def level_thing_remove(self, sessionid, csrftoken, referer, idLevel, idThing):
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

    def level_thing_get(self, sessionid, csrftoken, referer, idThing):
        """
            Retrieves the data of the given thing

            @param string sessionid
            @param string csrftoken
            @param string referer
            @param string idThing - "477757811"
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_thing_get() method")

    def level_thing_alt_edit(self, sessionid, csrftoken, referer, idThing, alts, column_key):
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

    def level_multimedia_edit(self, sessionid, csrftoken, referer, idLevel, txt):
        """
            Edit the content of the given multimedia level

            @param string sessionid
            @param string csrftoken
            @param string referer
            @param string idLevel - "7030263"
            @param string txt - "img:http://cdni.wired.co.uk/620x413..."
            àreturn dict - {success, multimedia}
        """
        raise NotImplementedError("subclasses of Memrise must provide a level_multimedia_edit() method")

    def course_edit_get(self, sessionid, idCourse, slugCourse):
        """
            Retrieve the content of a course for the edit page

            @param string sessionid
            @param string idCourse - "1892646"
            @param string slugCourse - "grammaire-le-groupe-nominal"
        """
        raise NotImplementedError("subclasses of Memrise must provide a course_edit_get() method")
