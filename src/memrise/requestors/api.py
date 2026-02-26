import requests
import time
import logging
import settings
from exceptions import SessionExpired


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


class ApiRequestor:
    """
    Performs requests to Memrise
    The result might still need to be scraped to conform to our Memrise interface
    """

    def raise_for_status(self, response):
        if response.status_code == 302:
            if response.headers["Location"].startswith("/signin"):
                raise SessionExpired()

        if response.status_code >= 300 and settings.DEBUG:
            filesuffix = get_time() + ".log"
            filename = "response." + filesuffix

            with open(filename, "w+") as f:
                f.write(response.text)

                logger.warn(f"Response with status {response.status_code} written to {filename}")

            filename = "request." + filesuffix
            with open(filename, "w+") as f:
                f.write(str(vars(response.request)))

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
            "username": username.strip(),
            "password": password.strip(),
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

    # +-----------------------------------------------------
    # | LEARNING SESSION
    # +-----------------------------------------------------
    def learning_session_register_end(self, data, sessionid=None, csrftoken=None, referer=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        logger.debug(f"Requestor:Learning session register end ({log_session})")

        url = f"{HOST}/{API_VERSION}/learning_sessions/end/"
        response = requests.post(
            url,
            json=data,
            cookies=self.buildCookies(sessionid, csrftoken),
            headers={
                "Origin": HOST,
                "Referer": referer or HOST,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "Content-Type": "application/json",
            },
        )
        self.raise_for_status(response)
        return response.json()

    def learning_session_register_progress(self, data, sessionid=None, csrftoken=None, referer=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        logger.debug(f"Requestor:Learning session register progress ({log_session})")

        data["events"] = data.get("events", [])
        data["sync_token"] = 0
        data["limit"] = 0

        # referer = "https://community-courses.memrise.com/aprender/review?course_id=6698294"
        url = f"{HOST}/{API_VERSION}/progress/register/"
        response = requests.post(
            url,
            json=data,
            cookies=self.buildCookies(sessionid, csrftoken),
            headers={
                "Origin": HOST,
                "Referer": referer or HOST,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "Content-Type": "application/json",
            },
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

    def level(self, idCourse, lvl, session_type="preview", sessionid=None, csrftoken=None):
        log_session = self.buildCookiesLog(sessionid, csrftoken)
        logger.debug(f"Requestor:Level [id_course={idCourse},level={lvl}] ({log_session})")

        url = f"{HOST}/{API_VERSION}/learning_sessions/{session_type}/"

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

    def level_multimedia(self, idCourse, slugCourse, lvl, sessionid=None):
        log_session = self.buildCookiesLog(sessionid)
        log_params = f"id_course={idCourse},slug={slugCourse},level={lvl}"
        logger.debug(f"Requestor:Level multimedia [{log_params}] ({log_session})")

        # https://community-courses.memrise.com/community/course/1892646/grammaire-le-groupe-nominal/3/
        url = f"{HOST}/community/course/{idCourse}/{slugCourse}/{lvl}/"

        response = requests.get(url, cookies=self.buildCookies(sessionid), allow_redirects=False)
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

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

    def user_courses(self, tab, username, sessionid=None):
        log_session = self.buildCookiesLog(sessionid)
        logger.debug(f"Requestor:User courses [username={username},tab={tab}] ({log_session})")

        url = f"{HOST}/user/{username}/courses/{tab}/"

        response = requests.get(url, cookies=self.buildCookies(sessionid), allow_redirects=False)
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    # +-----------------------------------------------------
    # | COURSE EDIT
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
