import requests
import re
import time
import logging
import settings
import web
from exceptions import SessionExpired

from bs4 import BeautifulSoup, Tag
from variables import categories_code, levels, languages
from .base import Memrise


# fmt: off
OAUTH_CLIENT_ID = "1e739f5e77704b57a703"
USER_AGENT      = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0"
HOST            = "https://community-courses.memrise.com"
API_VERSION     = "v1.25"
ACCEPT_LANGUAGE = "fr;q=0.8,en-US;q=0.5,en;q=0.3"
# fmt: on

logger = logging.getLogger(__name__)


def get_time():
    return "%d" % (time.time() * 1000)


class Requestor:
    """
    Performs requests to Memrise
    The result might still need to be scraped to conform to our Memrise interface
    """

    def raise_for_status(self, response):
        if response.status_code == 302:
            if response.headers["Location"].startswith("/signin"):
                raise SessionExpired()

        # might redirect to canonical URL
        # which isn't supposed to happen if we have the correct slug
        if 300 <= response.status_code < 400:
            loc = response.headers.get("Location", "")

            http_error_msg = (
                f"{response.status_code} Redirect Error: {response.reason} for url: {response.url} -> {loc}"
            )
            raise requests.exceptions.HTTPError(http_error_msg, response=response)

        # Raise exception if response status code >= 400
        response.raise_for_status()

    # +-----------------------------------------------------
    # | AUTH
    # +-----------------------------------------------------
    def login(self, username, password):
        logger.debug(f"Requestor:Login {username}")

        data = {}
        cookies = {}

        # -----------------------------------------------------------------------
        # Retrieve CRSF token
        headers = {
            "Referer": f"{HOST}/signin",
            "User-Agent": USER_AGENT,
        }
        url = f"{HOST}/{API_VERSION}/web/ensure_csrf"
        response = requests.get(url)
        response.raise_for_status()

        json = response.json()
        csrftoken = json["csrftoken"]

        # -----------------------------------------------------------------------
        # Retrieve access_token (login)
        headers["Origin"] = HOST
        headers["X-CSRFToken"] = csrftoken

        cookies = {"csrftoken": csrftoken}
        data = {
            "client_id": OAUTH_CLIENT_ID,
            "grant_type": "password",
            "username": username,
            "password": password,
        }
        url = f"{HOST}/{API_VERSION}/auth/access_token/"
        response = requests.post(url, cookies=cookies, headers=headers, data=data)
        response.raise_for_status()

        json = response.json()
        data = json["user"]  # {username, is_new, id}

        # -----------------------------------------------------------------------
        # Retrieve sessionid_2
        del headers["Origin"]
        del headers["X-CSRFToken"]

        token = json["access_token"]["access_token"]
        url = f"{HOST}/{API_VERSION}/auth/web/?invalidate_token_after=true&token={token}"
        response = requests.get(url, cookies=cookies, headers=headers)
        response.raise_for_status()

        data["sessionid"] = response.cookies["sessionid_2"]  # j74y9ut8nwrw4wqomtvqmyt5k9g4gvwng
        data["csrftoken"] = response.cookies["csrftoken"]

        return data

    # +-----------------------------------------------------
    # | CURRENT USER
    # +-----------------------------------------------------
    def buildCookies(self, sessionid=None, csrftoken=None):
        cookies = {}

        if sessionid:
            cookies["sessionid_2"] = sessionid

        if csrftoken:
            cookies["csrftoken"] = csrftoken

        return cookies

    def buildCookiesLog(self, sessionid=None, csrftoken=None):
        args = []

        if sessionid:
            args.append("session")

        if csrftoken:
            args.append("csrftoken")

        return ",".join(args)

    def whoami(self, sessionid=None):
        log_session = self.buildCookiesLog(sessionid)
        logger.debug(f"Requestor:Who am I ({log_session})")

        url = f"{HOST}/settings/"

        response = requests.get(url, cookies=self.buildCookies(sessionid))
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    def whatistudy(self, offset, nbperpage, sessionid=None):
        log_session = self.buildCookiesLog(sessionid)
        logger.debug(f"Requestor:What I study [offset={offset}] ({log_session})")

        # url = f"https://app.memrise.com/ajax/courses/dashboard/?courses_filter=most_recent&offset={offset}&limit={nbperpage-1}&get_review_count=true"
        url = f"{HOST}/{API_VERSION}/dashboard/courses/?filter=recent&offset={offset}&limit={nbperpage}"

        response = requests.get(url, cookies=self.buildCookies(sessionid))
        self.raise_for_status(response)
        return response.json()

    def my_leaderboard(self, period, sessionid=None):
        log_session = self.buildCookiesLog(sessionid)
        logger.debug(f"Requestor:My leaderboard [period={period}] ({log_session})")

        url = f"{HOST}/ajax/leaderboard/mempals/?period={period}&how_many=50"

        response = requests.get(url, cookies=self.buildCookies(sessionid))
        self.raise_for_status(response)
        return response.json()

    def track_progress(self, path, data, sessionid=None, csrftoken=None, referer=None):
        """
        TODO
        Post play progress

        @throws requests.exceptions.HTTPError
        @param string path - register | session_end
        @param dict data
        @param string sessionid
        @param string csrftoken
        @param string referer
        @return dict - Retrieved JSON
        """
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        logger.debug(f"Requestor:Track progress [path={path}] ({log_session})")

        if path == "session_end":
            url = "https://app.memrise.com/ajax/session_end/"
        else:
            url = "https://app.memrise.com/api/garden/register/"

        response = requests.post(
            url,
            data=data,
            cookies=self.buildCookies(sessionid, csrftoken),
            headers={"Origin": HOST, "Referer": referer or HOST, "User-Agent": USER_AGENT, "X-CSRFToken": csrftoken},
        )
        self.raise_for_status(response)
        return response.json()

    # +-----------------------------------------------------
    # | COURSES
    # +-----------------------------------------------------
    def courses(self, lang, page, cat, query):
        logger.debug(f"Requestor:Courses [lang={lang},cat={cat},query={query},page={page}]")

        url = f"{HOST}/ajax/browse/?s_cat={lang}"
        if cat != "":
            url += "&cat=" + cat
        if query != "":
            url += "&q=" + query
        url += "&page=" + str(page) + "&_=" + get_time()

        response = requests.get(url, headers={"Accept-Language": ACCEPT_LANGUAGE})
        return response.json()

    # +-----------------------------------------------------
    # | CATEGORIES
    # +-----------------------------------------------------
    def categories(self, lang, sessionid=None, csrftoken=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        logger.debug(f"Requestor:Categories [lang={lang}] ({log_session})")

        locale = lang[:2]
        if locale not in ("fr", "en"):
            locale = "fr"

        # /de/community/courses/french = "Ich spreche französicsch"
        host = HOST
        if locale != "en":
            host += "/" + locale

        url = f"{host}/community/courses/{lang}/"

        response = requests.get(url, cookies=self.buildCookies(sessionid, csrftoken), allow_redirects=False)
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    # +-----------------------------------------------------
    # | COURSE
    # +-----------------------------------------------------
    def course(self, idCourse, slugCourse="", sessionid=None, csrftoken=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        logger.debug(f"Requestor:Course [id={idCourse},slug={slugCourse}] ({log_session})")

        url = f"{HOST}/community/course/{idCourse}/"
        if slugCourse:
            url += slugCourse + "/"

        response = requests.get(url, cookies=self.buildCookies(sessionid, csrftoken), allow_redirects=False)
        self.raise_for_status(response)

        return response.text.encode("utf-8").strip()

    # +-----------------------------------------------------
    # | COURSE > LEVEL
    # +-----------------------------------------------------
    def level(self, idCourse, lvl, sessionid=None, csrftoken=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        logger.debug(f"Requestor:Level [id_course={idCourse},level={lvl}] ({log_session})")

        url = f"{HOST}/{API_VERSION}/learning_sessions/preview/"

        referer = f"{HOST}/aprender/preview?course_id=${idCourse}&level_index=${lvl}"
        response = requests.post(
            url,
            cookies=self.buildCookies(sessionid, csrftoken),
            headers={
                "Origin": HOST,
                "Referer": referer,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/json",
            },
            json={
                "session_source_id": idCourse,
                "session_source_sub_index": lvl,
                "session_source_type": "course_id_and_level_index",
            },
        )
        self.raise_for_status(response)
        return response.json()

    def level_learning_session(self, idCourse, slugCourse, sessionType, sessionid=None):
        log_session = self.buildCookiesLog(sessionid)
        log_params = f"id_course={idCourse},slug={slugCourse}],session_type={sessionType}"
        logger.debug(f"Requestor:Level learning session [{log_params}] ({log_session})")

        url = f"{HOST}/course/{idCourse}/{slugCourse}/garden/{sessionType}/"

        response = requests.head(url, cookies=self.buildCookies(sessionid))
        self.raise_for_status(response)
        return {
            "referer": url,
            "csrftoken": response.cookies.get("csrftoken"),
        }

    def level_multimedia(self, idCourse, slugCourse, lvl, sessionid=None):
        log_session = self.buildCookiesLog(sessionid)
        log_params = f"id_course={idCourse},slug={slugCourse},level={lvl}"
        logger.debug(f"Requestor:Level multimedia [{log_params}] ({log_session})")

        # https://community-courses.memrise.com/community/course/1892646/grammaire-le-groupe-nominal/3/
        url = f"{HOST}/community/course/{idCourse}/{slugCourse}/{lvl}/"

        response = requests.get(url, cookies=self.buildCookies(sessionid), allow_redirects=False)
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    # +-----------------------------------------------------
    # | COURSE > LEADERBOARD
    # +-----------------------------------------------------
    def course_leaderboard(self, idCourse, period, sessionid=None):
        log_session = self.buildCookiesLog(sessionid)
        logger.debug(f"Requestor:Course leaderboard [id_course={idCourse},period={period}] ({log_session})")

        url = f"{HOST}/ajax/leaderboard/course/{idCourse}/?period={period}&how_many=50"

        response = requests.get(url, cookies=self.buildCookies(sessionid), allow_redirects=False)
        self.raise_for_status(response)
        return response.json()

    # +-----------------------------------------------------
    # | USER
    # +-----------------------------------------------------
    def user(self, username, sessionid=None):
        log_session = self.buildCookiesLog(sessionid)
        logger.debug(f"Requestor:User profile [username={username}] ({log_session})")

        url = f"{HOST}/user/{username}/courses/teaching/"

        response = requests.get(url, cookies=self.buildCookies(sessionid), allow_redirects=False)
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    def user_mempals(self, tab, username, page):
        logger.debug(f"Requestor:User pals [username={username},tab={tab},page={page}]")

        url = f"{HOST}/user/{username}/mempals/{tab}/?page={page}"

        response = requests.get(url)
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    # +-----------------------------------------------------
    # | USER"s COURSES
    # +-----------------------------------------------------
    def user_courses(self, tab, username, sessionid=None):
        log_session = self.buildCookiesLog(sessionid)
        logger.debug(f"Requestor:User courses [username={username},tab={tab}] ({log_session})")

        url = f"{HOST}/user/{username}/courses/{tab}/"

        response = requests.get(url, cookies=self.buildCookies(sessionid), allow_redirects=False)
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    # +-----------------------------------------------------
    # | EDIT
    # +-----------------------------------------------------
    def level_edit_get(self, idLevel, sessionid=None):
        log_session = self.buildCookiesLog(sessionid)
        logger.debug(f"Requestor:Level edition: get things / multimedia [level_id={idLevel}] ({log_session})")

        url = f"{HOST}/ajax/level/editing_html/?level_id={idLevel}&_=" + get_time()

        response = requests.get(url, cookies=self.buildCookies(sessionid), allow_redirects=False)
        self.raise_for_status(response)
        return response.json()

    def level_thing_add(self, idLevel, data, sessionid=None, csrftoken=None, referer=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        logger.debug(f"Requestor:Level edition: add thing [level_id={idLevel}] ({log_session})")

        url = f"{HOST}/ajax/level/thing/add/"

        response = requests.post(
            url,
            data={
                "columns": data,
                "level_id": idLevel,
            },
            cookies=self.buildCookies(sessionid, csrftoken),
            headers={
                "Origin": HOST,
                "Referer": referer,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_edit(self, idThing, cellId, cellValue, sessionid=None, csrftoken=None, referer=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        logger.debug(f"Requestor:Level edition: edit thing [thing_id={idThing},cell_id={cellId}] ({log_session})")

        url = f"{HOST}/ajax/thing/cell/update/"

        response = requests.post(
            url,
            data={
                "cell_id": cellId,
                "cell_type": "column",
                "new_val": cellValue,
                "thing_id": idThing,
            },
            cookies=self.buildCookies(sessionid, csrftoken),
            headers={
                "Origin": HOST,
                "Referer": referer or HOST,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_upload(self, idThing, cellId, file, sessionid=None, csrftoken=None, referer=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        log_params = f"thing_id={idThing},cell_id={cellId}"
        logger.debug(f"Requestor:Level edition: upload file to thing [{log_params}] ({log_session})")

        url = f"{HOST}/ajax/thing/cell/upload_file/"

        """
        Possible File-like-object:
            filepointer <attr name="...">
            (filename, filepointer)
            (filename, filepointer, filecontenttype)
            (filename, filepointer, filecontenttype, fileheaders)

        Possible Filepointer:
            isinstance(fp, (str, bytes, bytearray))
            hasattr(fp, "read")   # _pyio
        """
        response = requests.post(
            url,
            data={
                "cell_id": cellId,
                "cell_type": "column",
                "thing_id": idThing,
            },
            files={
                "f": (file.filename, file.value),  # files={FILENAME: file-like-object}
            },
            cookies=self.buildCookies(sessionid, csrftoken),
            headers={
                "Origin": HOST,
                "Referer": referer or HOST,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_upload_remove(self, idThing, cellId, fileId, sessionid=None, csrftoken=None, referer=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        log_params = f"thing_id={idThing},cell_id={cellId},file_id={fileId}"
        logger.debug(f"Requestor:Level edition: delete file from thing [{log_params}] ({log_session})")

        url = f"{HOST}/ajax/thing/column/delete_from/"

        response = requests.post(
            url,
            data={
                "column_key": cellId,
                "cell_type": "column",
                "thing_id": idThing,
                "file_id": fileId,
            },
            cookies=self.buildCookies(sessionid, csrftoken),
            headers={
                "Origin": HOST,
                "Referer": referer or HOST,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_remove(self, idLevel, idThing, sessionid=None, csrftoken=None, referer=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        logger.debug(f"Requestor:Level edition: delete thing [level_id={idLevel},thing_id={idThing}] ({log_session})")

        url = f"{HOST}/ajax/level/thing_remove/"

        response = requests.post(
            url,
            data={
                "thing_id": idThing,
                "level_id": idLevel,
            },
            cookies=self.buildCookies(sessionid, csrftoken),
            headers={
                "Origin": HOST,
                "Referer": referer or HOST,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_get(self, idThing, sessionid=None, csrftoken=None, referer=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        logger.debug(f"Requestor:Level edition: get thing [thing_id={idThing}] ({log_session})")

        url = f"{HOST}/ajax/thing/get/?thing_id={idThing}&_=" + get_time()

        response = requests.get(
            url,
            cookies=self.buildCookies(sessionid, csrftoken),
            headers={
                "Origin": HOST,
                "Referer": referer or HOST,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_alt_edit(self, idThing, alts, column_key, sessionid=None, csrftoken=None, referer=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        log_params = f"thing_id={idThing},column={column_key}"
        logger.debug(f"Requestor:Level edition: edit thing alternative values [{log_params}] ({log_session})")

        url = f"{HOST}/ajax/thing/column/update_alts/"

        response = requests.post(
            url,
            data={
                "alts": alts,
                "column_key": column_key,
                "thing_id": idThing,
            },
            cookies=self.buildCookies(sessionid, csrftoken),
            headers={
                "Origin": HOST,
                "Referer": referer or HOST,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        self.raise_for_status(response)
        return response.json()

    def level_multimedia_edit(self, idLevel, txt, sessionid=None, csrftoken=None, referer=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        logger.debug(f"Requestor:Level edition: update multimedia [level_id={idLevel}] ({log_session})")

        url = f"{HOST}/ajax/level/set_multimedia/"

        response = requests.post(
            url,
            data={
                "multimedia": txt,
                "level_id": idLevel,
            },
            cookies=self.buildCookies(sessionid, csrftoken),
            headers={
                "Origin": HOST,
                "Referer": referer or HOST,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        self.raise_for_status(response)
        return response.json()

    def course_edit_get(self, idCourse, slugCourse, sessionid=None):
        log_session = self.buildCookiesLog(sessionid)
        logger.debug(f"Requestor:Course edition: get levels [course_id={idCourse}] ({log_session})")

        url = f"{HOST}/course/{idCourse}/{slugCourse}/edit/"

        response = requests.get(url, cookies=self.buildCookies(sessionid))
        self.raise_for_status(response)

        html = response.text.encode("utf-8").strip()
        csrftoken = response.cookies.get("csrftoken")

        return {
            "csrftoken": csrftoken,
            "referer": url,
            "html": html,
        }


class Scraper:
    # +-----------------------------------------------------
    # | CURRENT USER
    # +-----------------------------------------------------
    def whoami(self, sessionid, html):
        assert len(html) > 0

        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")
        data = {"sessionid": sessionid}

        div = DOM.find(id="content")
        if div is not None:
            # Get username
            item = div.find(id="id_username")
            if item is not None:
                data["username"] = item.attrs["value"]

            # Get photo
            item = div.find("div", {"class": "thumbnail"})
            if item is not None:
                data["photo"] = item.img.attrs["src"]

        return data

    # +-----------------------------------------------------
    # | CATEGORIES
    # +-----------------------------------------------------
    def categories(self, html):
        assert len(html) > 0

        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")
        ul_list = DOM.find_all("ul", {"class": "categories-list"})

        def parseCategories(ul):
            for li in ul.find_all(recursive=False):
                if "data-category-id" not in li.attrs:
                    continue

                id = li.attrs["data-category-id"]
                categories[id] = True

                if li.ul:
                    parseCategories(li.ul)

        categories = {}
        if len(ul_list):
            parseCategories(ul_list.pop())

        return categories

    # +-----------------------------------------------------
    # | COURSE
    # +-----------------------------------------------------
    def course(self, idCourse, html, isLoggedIn=False):
        assert len(html) > 0

        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")
        course = {
            "id": idCourse,
            "title": "",
            "url": "",
            "author": "",
            "description": "",
            "photo": "",
            "levels": {},
            "breadcrumb": [],
            "source": None,  # for users that speak (=breadcrumb.0)
            "target": None,  # for users that want to learn (=breadcrumb.last if present in languages)
        }

        div = DOM.find("div", {"class", "course-wrapper"})
        if div is not None:
            # Title
            item = div.find(itemprop="name")
            if item is not None:
                course["title"] = item.text

            # Description
            item = div.find(itemprop="about")
            if item is not None:
                course["description"] = item.text

            # Author (only when logged in :/)
            item = div.find(itemprop="author")
            if item is not None:
                course["author"] = item.find(itemprop="additionalName").text

            # Breadcrumb
            # (Courses / Languages / European / German / German) = Deutsch für Englisch-Sprecher
            # (Kurse / Maths / Science Chemistry) = Chemie for Deutsche-Sprecher
            item = div.find("div", {"class", "course-breadcrumb"})
            if item is not None:
                for child in item.find_all("a"):
                    cat = child.attrs["href"].strip("/").split("/").pop()

                    if cat in categories_code:
                        course["breadcrumb"].append(
                            {
                                "id": categories_code[cat],
                                "name": cat,
                            }
                        )

            # Add source and target languages
            if len(course["breadcrumb"]) >= 3:

                def add_language(course, category, to_key="source"):
                    slug = category["name"]
                    if slug not in languages:
                        return False

                    lang = languages[slug]
                    course[to_key] = {
                        "slug": slug,  # ie portuguese-brazil (lang=pt)
                        "photo_url": lang["url"],
                        "id": category["id"],
                        "language_code": lang.get("code", None),
                    }

                # Add source language
                categories = course["breadcrumb"].copy()

                add_language(course, to_key="source", category=categories.pop(0))

                # Add target language
                if categories[0]["name"] == "languages":
                    categories.pop(0)

                    # Unravel target until we reach a language we known (ie german / german-2)
                    while len(categories):
                        if add_language(course, to_key="target", category=categories.pop(-1)):
                            break

            # Photo + url
            item = div.find("a", {"class", "course-photo"})
            if item is not None:
                course["url"] = item.attrs["href"]
                course["photo"] = item.img.attrs["src"]

        # List of levels
        div = DOM.find("div", {"class": "levels"})
        if div is not None:
            for child in div.children:
                if not isinstance(child, Tag):
                    continue

                name = child.find("div", {"class": "level-title"}).text.strip()
                idx = child.find("div", {"class": "level-index"}).text.strip()
                ico = child.find(attrs={"class": "level-ico"}).attrs["class"].pop()

                course["levels"][idx] = {
                    "name": name,
                    "type": (2 if ico == "level-ico-multimedia-inactive" or ico == "level-ico-multimedia" else 1),
                }
                if isLoggedIn:
                    status = child.find("div", {"class": "level-status"})
                    if status is not None:
                        course["levels"][idx]["status"] = re.sub(r"\s+", " ", str(status))

        # List of things (course without levels)
        div = DOM.find("div", {"class": "things"})
        if div is not None:
            things = 0

            for child in div.find_all("div", {"class": "thing"}, recursive=False):
                things += 1

            course["num_things"] = things

        if isLoggedIn:
            stats = self._course_progress(DOM)
            if stats is not None:
                course["stats"] = stats

        return course

    def _course_progress(self, DOM):
        stats = {
            "ignored": 0,
            "learned": 0,
            "percent_complete": 0,
            "review": 0,
            "num_things": 0,
        }

        div = DOM.find("div", {"class", "progress-box"})
        if div is None:
            return stats

        # Ignored, learned, total
        item = div.find("div", {"class": "progress-box-title"})
        if item is not None:
            text = item.find(string=True, recursive=False)
            if text:
                res = re.search(r"^(\d+) ?/ ?(\d+)", text.strip())
                if res:
                    stats["learned"] = int(res.group(1))
                    stats["num_things"] = int(res.group(2))

            text = item.find(attrs={"class": "pull-right"})
            if text:
                res = re.search(r"^(\d+)", text.text.strip())
                if res:
                    stats["ignored"] = int(res.group(1))
                    stats["num_things"] += int(res.group(1))

            # Percentage complete
            if stats["learned"] > 0:
                if stats["num_things"] == 0:
                    stats["percent_complete"] = 100
                else:
                    percent = float(stats["learned"])
                    percent /= float(stats["num_things"]) - float(stats["ignored"])
                    stats["percent_complete"] = int(percent * 100)

        # Review
        item = div.find("a", {"class": "blue"})
        if item is not None:
            res = re.search(r"\((\d+)\)", item.text)
            if res:
                stats["review"] = int(res.group(1))

        return stats

    # +-----------------------------------------------------
    # | COURSE > LEVEL
    # +-----------------------------------------------------
    def level_multimedia(self, html):
        assert len(html) > 0

        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")
        data = None

        # Look for value of js variable "level_multimedia"
        VAR_MULTIMEDIA = "var level_multimedia = "
        scripts = DOM.html.body.find_all("script", string=True, recursive=False)
        for script in scripts:
            text = script.string.strip()

            if text and text.startswith(VAR_MULTIMEDIA):
                data = text[len(VAR_MULTIMEDIA) :].strip(";")
                break

        return data

    # +-----------------------------------------------------
    # | USER
    # +-----------------------------------------------------
    def user(self, username, html):
        assert len(html) > 0

        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")
        user = {
            "username": username,
            "photo": "",
            "points": 0,
            "rank": 0,
            "stats": {},
        }

        div = DOM.find(id="page-head")
        if div is not None:
            # Get avatar
            item = div.find("img", {"class": "avatar"})
            if item is not None:
                user["photo"] = item.attrs["src"]

            # Get stats (num followers, following, word|words|word|wörter, leaderboard)
            # Note that we"re supposed to request memrise in english
            div = div.find(attrs={"class": "profile-stats"})
            for child in div.children:
                if not isinstance(child, Tag):
                    continue

                text = child.text.strip()
                result = re.search(r"([0-9,]+)([\n\w ]*)", text)
                if result:
                    link = child.find("a")
                    if link:
                        tab = link.attrs["href"].strip("/").split("/")[-1]
                    else:
                        tab = result.group(2).strip().lower()

                    if tab == "leaderboard":
                        tab = "points"
                    elif tab == "word":
                        tab = "words"

                    user["stats"][tab] = result.group(1)

        if "points" in user["stats"]:
            points = int(user["stats"]["points"].replace(",", ""))
            rank = 0

            for i, threshold in enumerate(levels):
                if threshold < points:
                    rank = i
                else:
                    break

            # https://community-courses.memrise.com/community/course/1601869/all-about-ziggy-no-difficult-typing/
            user["rank"] = rank + 1

        div = DOM.find(id="content")
        if div is not None:
            # Get stats
            # {"following": "1", "": "1", "wort": "0", "punkte": "660", "learning": "1", "teaching": "61"}
            item = div.find("div", {"class", "btn-group"})
            if item is not None:
                for child in item.children:
                    if not isinstance(child, Tag):
                        continue

                    result = re.search(r"\(([0-9,]+)\)", child.text)
                    if result:
                        tab = child.attrs["href"].strip("/").split("/")[-1]
                        user["stats"][tab] = result.group(1)
                    else:
                        tab = ""

        return user

    def user_mempals(self, username, page, html):
        assert len(html) > 0

        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")
        data = {
            "page": page,
            "lastpage": 0,
            "users": [],
        }

        # Get list of followers
        div = DOM.find(id="content")
        if div is not None:
            users = div.find_all(attrs={"class": "user-box"})
            for user in users:
                username = user.find(attrs={"class": "username"})
                img = user.find("img")
                if username is None:
                    continue

                item = {
                    "name": username.text.strip(),
                    "photo": img.attrs["src"] if img else "",
                }
                data["users"].append(item)

        # Get current page + max page number
        div = DOM.find("ul", {"class": "pagination"})
        currentPage = page
        lastpage = 0

        if div is not None:
            for child in div.children:
                if not isinstance(child, Tag):
                    continue

                text = child.text.strip()
                if not re.match("[0-9]+", text):
                    continue

                lastpage = int(text)
                if "class" in child.attrs and "active" in child.attrs["class"]:
                    currentPage = lastpage

            data["page"] = currentPage
            data["lastpage"] = lastpage
            data["has_next"] = data["page"] < data["lastpage"]

        return data

    # +-----------------------------------------------------
    # | USER"s COURSES
    # +-----------------------------------------------------
    def user_courses(self, html):
        assert len(html) > 0

        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")
        courses = {
            "nbCourse": 0,
            "content": [],
        }

        # Get list of courses
        div = DOM.find(id="content")
        if div != "None":
            content = div.find_all("div", {"class": "course-box-wrapper"})

            for wrapper in content:
                courses["content"].append(str(wrapper))
                courses["nbCourse"] += 1

        return courses

    # +-----------------------------------------------------
    # | EDIT
    # +-----------------------------------------------------
    def course_edit_get(self, data_pointer, html):
        assert len(html) > 0

        data = data_pointer
        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")

        # Course data
        div = DOM.find(id="page-head")
        if div is not None:
            item = div.find("div", {"class": "course-details"})
            if item is not None:
                data["url"] = item.a.attrs["href"]
                data["title"] = item.text.strip()

        # Levels
        div = DOM.find(id="levels")
        levels = []

        if div is not None:
            for child in div.find_all(attrs={"class": "level"}, recursive=False):
                level = {"id": child.attrs["data-level-id"]}
                header = child.find("div", {"class": "level-header"}, recursive=False)

                if "data-pool-id" in child.attrs:
                    level["pool"] = child.attrs["data-pool-id"]

                if header is not None:
                    level["name"] = header.h3.text.strip()

                levels.append(level)
        data["levels"] = levels

        return data


class ApiMemrise(Memrise):
    def __init__(self):
        self.requestor = Requestor()
        self.scraper = Scraper()

    def get_saved_login(self):
        return web.ctx.get("session", {}).get("loggedin", None)

        # csrftoken=web.ctx.env.get("HTTP_X_CSRFTOKEN"),
        # referer=web.ctx.env.get("HTTP_X_REFERER"),

    def set_default_kwargs(self, kwargs, session=None):
        session = self.get_saved_login() or {}
        kwargs.setdefault("sessionid", session.get("sessionid", None))
        kwargs.setdefault("csrftoken", session.get("csrftoken", None))

    def _login_as_anonymous(self, **kwargs):
        """
        Retrieve sessionid to retrieve content (using our own account)

        @return string - sessionid
        """
        return self.login(settings.MEMRISE_ANON_USERNAME, settings.MEMRISE_ANON_PASSWORD)

    def login(self, username, password):
        return self.requestor.login(username, password)

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

    def track_progress(self, path, data, referer=None, **kwargs):
        self.set_default_kwargs(kwargs)

        return self.requestor.track_progress(
            path,
            data,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
            referer=referer,
        )

    def courses(self, lang, page=1, cat="", query=""):
        if not isinstance(page, int) and not page.isdigit():
            page = 0

        return self.requestor.courses(lang=lang, page=page, cat=cat, query=query)

    def categories(self, lang, **kwargs):
        self.set_default_kwargs(kwargs)

        html = self.requestor.categories(
            lang,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
        )
        return self.scraper.categories(html)

    def course(self, idCourse, slugCourse="", **kwargs):
        self.set_default_kwargs(kwargs)

        html = self.requestor.course(
            idCourse,
            slugCourse,
            sessionid=kwargs["sessionid"],
            csrftoken=kwargs["csrftoken"],
        )
        return self.scraper.course(idCourse, html, isLoggedIn=kwargs["sessionid"])

    def level(self, idCourse, slugCourse, lvl, slug="preview", **kwargs):
        self.set_default_kwargs(kwargs)

        if not kwargs["sessionid"]:
            is_anonymous_session = True
            session = self._login_as_anonymous()

            kwargs["sessionid"] = session["sessionid"]
            kwargs["csrftoken"] = session["csrftoken"]
        else:
            is_anonymous_session = False

        if slug == "speed_review":
            slug = "classic_review"

        # Retrieve level info
        retry_login = True
        level = {}
        while retry_login:
            try:
                level = self.requestor.level(
                    idCourse,
                    lvl,
                    sessionid=kwargs["sessionid"],
                    csrftoken=kwargs["csrftoken"],
                )
            except requests.exceptions.HTTPError as e:
                # Try reauthenticate
                if e.response.status_code == 403 and is_anonymous_session and retry_login:
                    session = self._login_as_anonymous(nocache=True)

                    kwargs["sessionid"] = session["sessionid"]
                    kwargs["csrftoken"] = session["csrftoken"]
                else:
                    raise e
            finally:
                retry_login = False

        # Start learning session (to be able to send results to memrise)
        if not is_anonymous_session and slug != "preview":
            session = self.requestor.level_learning_session(
                idCourse,
                slugCourse,
                sessionType=slug,
                sessionid=kwargs["sessionid"],
            )
            level.update(session)

        return level

    def level_multimedia(self, idCourse, slugCourse, lvl, **kwargs):
        self.set_default_kwargs(kwargs)

        html = self.requestor.level_multimedia(
            idCourse,
            slugCourse,
            lvl,
            sessionid=kwargs["sessionid"],
        )
        return self.scraper.level_multimedia(html)

    def course_leaderboard(self, idCourse, period, **kwargs):
        self.set_default_kwargs(kwargs)

        retry_login = True
        ldboard = {}
        while retry_login:
            try:
                ldboard = self.requestor.course_leaderboard(
                    idCourse,
                    period,
                    sessionid=kwargs["sessionid"],
                )
            except requests.exceptions.HTTPError as e:
                # Try reauthenticate
                if e.response.status_code == 403 and retry_login:
                    session = self._login_as_anonymous(nocache=True)

                    kwargs["sessionid"] = session["sessionid"]
                    kwargs["csrftoken"] = session["csrftoken"]
                else:
                    raise e
            finally:
                retry_login = False

        if "users" in ldboard:
            return {
                "rows": ldboard.get("users", []),
            }
        return ldboard

    def user(self, username, **kwargs):
        self.set_default_kwargs(kwargs)

        html = self.requestor.user(username, sessionid=kwargs["sessionid"])

        return self.scraper.user(username, html)

    def user_mempals(self, tab, username, page=1, **kwargs):
        self.set_default_kwargs(kwargs)

        html = self.requestor.user_mempals(tab, username, page, sessionid=kwargs["sessionid"])

        return self.scraper.user_mempals(username, page, html)

    def user_courses(self, tab, username, **kwargs):
        self.set_default_kwargs(kwargs)

        html = self.requestor.user_courses(tab, username, sessionid=kwargs["sessionid"])

        return self.scraper.user_courses(html)

    def level_edit_get(self, *args, **kwargs):
        return self.requestor.level_edit_get(*args, **kwargs)

    def level_thing_add(self, *args, **kwargs):
        return self.requestor.level_thing_add(*args, **kwargs)

    def level_thing_edit(self, *args, **kwargs):
        return self.requestor.level_thing_edit(*args, **kwargs)

    def level_thing_upload(self, *args, **kwargs):
        return self.requestor.level_thing_upload(*args, **kwargs)

    def level_thing_upload_remove(self, *args, **kwargs):
        return self.requestor.level_thing_upload_remove(*args, **kwargs)

    def level_thing_remove(self, *args, **kwargs):
        return self.requestor.level_thing_remove(*args, **kwargs)

    def level_thing_get(self, *args, **kwargs):
        return self.requestor.level_thing_get(*args, **kwargs)

    def level_thing_alt_edit(self, *args, **kwargs):
        return self.requestor.level_thing_alt_edit(*args, **kwargs)

    def level_multimedia_edit(self, *args, **kwargs):
        return self.requestor.level_multimedia_edit(*args, **kwargs)

    def course_edit_get(self, idCourse, slugCourse, **kwargs):
        self.set_default_kwargs(kwargs)

        data = self.requestor.course_edit_get(idCourse, slugCourse, sessionid=kwargs["sessionid"])
        html = data.pop("html")
        self.scraper.course_edit_get(data, html)

        return data
