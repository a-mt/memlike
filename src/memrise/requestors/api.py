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

    def raise_for_status(self, response, raise_for_redirect=True):
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
        if raise_for_redirect and 300 <= response.status_code < 400:
            loc = response.headers.get("Location", "")

            http_error_msg = (
                f"{response.status_code} Redirect Error: {response.reason} for url: {response.url} -> {loc}"
            )
            raise requests.exceptions.HTTPError(http_error_msg, response=response)

        # Raise exception if response status code >= 400
        response.raise_for_status()

    def get_request_kwargs(self, method, about_request_msg, sessionid=None, csrftoken=None, referer=None):
        """
        :param string method - GET | POST
        :param string about_request_msg - What to print in the debug statement
        """
        cookies = {}
        args = []

        if sessionid:
            cookies["sessionid_2"] = sessionid
            args.append("session")

        if csrftoken:
            cookies["csrftoken"] = csrftoken
            args.append("csrftoken")

        about_session_msg = ",".join(args)
        logger.debug(f"{method} {about_request_msg} ({about_session_msg})")

        kwargs = {
            "cookies": cookies,
            "headers": {},
        }
        if method == "POST":
            kwargs["headers"] = {
                "Origin": HOST,
                "Referer": referer or HOST,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            }
        else:
            kwargs["allow_redirects"] = False

        return kwargs

    # +-----------------------------------------------------
    # | AUTH
    # +-----------------------------------------------------
    def login(self, username, password):
        logger.debug(f"Login {username}")

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

        data["sessionid"] = response.cookies["sessionid_2"]
        data["csrftoken"] = response.cookies["csrftoken"]

        return data

    # +-----------------------------------------------------
    # | CURRENT USER
    # +-----------------------------------------------------
    def whoami(self, sessionid=None):
        request_msg = "Who am I"

        url = f"{HOST}/settings/"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    def whatistudy(self, offset, nbperpage, sessionid=None):
        request_msg = f"What I study [offset={offset}]"

        url = f"{HOST}/{API_VERSION}/dashboard/courses/?filter=recent&offset={offset}&limit={nbperpage}"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def my_leaderboard(self, period, sessionid=None):
        request_msg = f"My leaderboard [period={period}]"

        url = f"{HOST}/ajax/leaderboard/mempals/?period={period}&how_many=50"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def my_progress(self, sync_token=0, sessionid=None):
        request_msg = f"My progress [sync_token={sync_token}]"

        url = f"{HOST}/{API_VERSION}/progress/?sync_token={sync_token}"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    # +-----------------------------------------------------
    # | LEARNING SESSION
    # +-----------------------------------------------------
    def learning_session_register_end(self, data, sessionid=None, csrftoken=None, referer=None):
        request_msg = "Learning session register end"

        url = f"{HOST}/{API_VERSION}/learning_sessions/end/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            json=data,
            headers={**request_kwargs.pop("headers", {}), **{"Content-Type": "application/json"}},
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def reset_progress_level(self, data, sessionid=None, csrftoken=None, referer=None):
        request_msg = "Level progress reset"

        url = f"{HOST}/ajax/level/restart/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            json=data,
            headers={**request_kwargs.pop("headers", {}), **{"Content-Type": "application/json"}},
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def learning_session_register_progress(self, data, sessionid=None, csrftoken=None, referer=None):
        request_msg = "Learning session register progress"

        data["events"] = data.get("events", [])
        data["sync_token"] = 0
        data["limit"] = 0

        # referer = "https://community-courses.memrise.com/aprender/review?course_id=6698294"
        url = f"{HOST}/{API_VERSION}/progress/register/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            json=data,
            headers={**request_kwargs.pop("headers", {}), **{"Content-Type": "application/json"}},
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    # +-----------------------------------------------------
    # | COURSES
    # +-----------------------------------------------------
    def courses(self, lang_slug, page, cat, query):
        request_msg = f"Courses [lang_slug={lang_slug},cat={cat},query={query},page={page}]"

        url = f"{HOST}/ajax/browse/?s_cat={lang_slug}"
        if cat != "":
            url += "&cat=" + cat
        if query != "":
            url += "&q=" + query
        url += "&page=" + str(page) + "&_=" + get_time()

        request_kwargs = self.get_request_kwargs("GET", request_msg)
        response = requests.get(
            url,
            headers={**request_kwargs.pop("headers", {}), **{"Accept-Language": ACCEPT_LANGUAGE}},
            **request_kwargs,
        )
        return response.json()

    def categories(self, lang_slug, sessionid=None, csrftoken=None):
        request_msg = f"Categories [lang_slug={lang_slug}]"

        locale = lang_slug[:2]
        if locale not in ("fr", "en"):
            locale = "fr"

        # /de/community/courses/french = "Ich spreche französicsch"
        host = HOST
        if locale != "en":
            host += "/" + locale

        url = f"{host}/community/courses/{lang_slug}/"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid, csrftoken)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    # +-----------------------------------------------------
    # | COURSE
    # +-----------------------------------------------------
    def course(self, course_id, course_slug="", sessionid=None, csrftoken=None):
        request_msg = f"Course [id={course_id},slug={course_slug}]"

        url = url_base = f"{HOST}/community/course/{course_id}/"
        if course_slug:
            url += course_slug + "/"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid, csrftoken)
        response = requests.get(
            url,
            **request_kwargs,
        )

        # Follow redirect to canonical URL
        if response.status_code == 301:
            new_url = response.headers["Location"]

            if new_url[0] == "/":
                new_url = HOST + new_url

            if new_url.startswith(url_base):
                response = requests.get(
                    new_url,
                    **request_kwargs,
                )

        self.raise_for_status(response)

        return response.text.encode("utf-8").strip()

    def level(self, course_id, level_index, session_type="preview", sessionid=None, csrftoken=None):
        request_msg = f"Level [id_course={course_id},level={level_index}]"

        url = f"{HOST}/{API_VERSION}/learning_sessions/{session_type}/"
        referer = f"{HOST}/aprender/preview?course_id=${course_id}"
        data = {
            "session_source_id": course_id,
        }
        if level_index and level_index != "all":
            referer += f"&level_index=${level_index}"
            data["session_source_sub_index"] = level_index
            data["session_source_type"] = "course_id_and_level_index"

        elif session_type == "preview":
            # Can't preview all things...
            referer += "&level_index=1"
            data["session_source_sub_index"] = "1"
            data["session_source_type"] = "course_id_and_level_index"
        else:
            data["session_source_type"] = "course"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            headers={**request_kwargs.pop("headers", {}), **{"Content-Type": "application/json"}},
            json=data,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_multimedia(self, course_id, course_slug, level_index, sessionid=None):
        request_msg = f"Level multimedia [id_course={course_id},slug={course_slug},level={level_index}]"

        # https://community-courses.memrise.com/community/course/1892646/grammaire-le-groupe-nominal/3/
        url = f"{HOST}/community/course/{course_id}/{course_slug}/{level_index}/"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    def course_leaderboard(self, course_id, period, sessionid=None):
        request_msg = f"Course leaderboard [id_course={course_id},period={period}]"

        url = f"{HOST}/ajax/leaderboard/course/{course_id}/?period={period}&how_many=50"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    # +-----------------------------------------------------
    # | USER
    # +-----------------------------------------------------
    def user(self, username, sessionid=None):
        request_msg = f"User profile [username={username}]"

        url = f"{HOST}/user/{username}/courses/teaching/"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    def user_mempals(self, tab, username, page, sessionid=None):
        request_msg = f"User pals [username={username},tab={tab},page={page}]"

        url = f"{HOST}/user/{username}/mempals/{tab}/?page={page}"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    def user_courses(self, tab, username, sessionid=None):
        request_msg = f"User courses [username={username},tab={tab}]"

        url = f"{HOST}/user/{username}/courses/{tab}/"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    # +-----------------------------------------------------
    # | COURSE EDIT
    # +-----------------------------------------------------
    def level_add(self, course_id, pool_id=None, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Level add [level_id={course_id}]"

        url = f"{HOST}/ajax/level/add/"
        if pool_id:
            data = {
                "course_id": course_id,
                "pool_id": pool_id,
                "kind": "things",
            }
        else:
            data = {
                "course_id": course_id,
                "kind": "multimedia",
            }

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data=data,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_delete(self, level_id, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Level delete [level_id={level_id}]"

        url = f"{HOST}/ajax/level/delete/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data={
                "level_id": level_id,
            },
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_title_edit(self, level_id, title, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Level edit title [level_id={level_id}]"

        url = f"{HOST}/ajax/level/set_title/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data={
                "level_id": level_id,
                "new_val": title,
            },
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_columns_edit(self, level_id, column_a, column_b, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Level edit columns [level_id={level_id}]"

        url = f"{HOST}/ajax/level/set_columns/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data={
                "level_id": level_id,
                "column_a": column_a,
                "column_b": column_b,
            },
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_get_editpage(self, level_id, sessionid=None, csrftoken=None, **kwargs):
        request_msg = f"Level edition: get things / multimedia [level_id={level_id}]"

        url = f"{HOST}/ajax/level/editing_html/?level_id={level_id}&_=" + get_time()

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid, csrftoken)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_add(self, level_id, data, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Level edition: add thing [level_id={level_id}]"

        url = f"{HOST}/ajax/level/thing/add/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data={
                "columns": data,
                "level_id": level_id,
            },
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_update(self, thing_id, cell_id, cell_value, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Level edition: edit thing [thing_id={thing_id},cell_id={cell_id}]"

        url = f"{HOST}/ajax/thing/cell/update/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data={
                "cell_id": cell_id,
                "cell_type": "column",
                "new_val": cell_value,
                "thing_id": thing_id,
            },
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_file_upload(self, thing_id, cell_id, file, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Level edition: upload file to thing [thing_id={thing_id},cell_id={cell_id}]"

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
        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data={
                "cell_id": cell_id,
                "cell_type": "column",
                "thing_id": thing_id,
            },
            files={
                "f": (file.filename, file.raw),  # files={FILENAME: file-like-object}
            },
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_file_delete(
        self, thing_id, cell_id, file_id, sessionid=None, csrftoken=None, referer=None, **kwargs
    ):
        request_msg = f"Level edition: delete file from thing [thing_id={thing_id},cell_id={cell_id},file_id={file_id}]"

        url = f"{HOST}/ajax/thing/column/delete_from/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data={
                "column_key": cell_id,
                "cell_type": "column",
                "thing_id": thing_id,
                "file_id": file_id,
            },
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_delete(self, level_id, thing_id, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Level edition: delete thing [level_id={level_id},thing_id={thing_id}]"

        url = f"{HOST}/ajax/level/thing_remove/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data={
                "thing_id": thing_id,
                "level_id": level_id,
            },
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_get(self, thing_id, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Level edition: get thing [thing_id={thing_id}]"

        url = f"{HOST}/ajax/thing/get/?thing_id={thing_id}&_=" + get_time()

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid, csrftoken, referer)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_thing_alt_update(
        self, thing_id, alts, column_key, sessionid=None, csrftoken=None, referer=None, **kwargs
    ):
        request_msg = f"Level edition: edit thing alternative values [thing_id={thing_id},column={column_key}]"

        url = f"{HOST}/ajax/thing/column/update_alts/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data={
                "alts": alts,
                "column_key": column_key,
                "thing_id": thing_id,
            },
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def level_multimedia_update(self, level_id, txt, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Level edition: update multimedia [level_id={level_id}]"

        url = f"{HOST}/ajax/level/set_multimedia/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data={
                "multimedia": txt,
                "level_id": level_id,
            },
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def course_get_editpage(self, course_id, course_slug, sessionid=None, **kwargs):
        request_msg = f"Course edition: get levels [course_id={course_id}]"

        url = f"{HOST}/course/{course_id}/{course_slug}/edit/"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)

        html = response.text.encode("utf-8").strip()
        csrftoken = response.cookies.get("csrftoken")

        return {
            "id": course_id,
            "csrftoken": csrftoken,
            "referer": url,
            "html": html,
        }

    def course_get_editdetails(self, course_id, course_slug, sessionid=None, **kwargs):
        request_msg = f"Course edition: get details [course_id={course_id}]"

        url = f"{HOST}/course/{course_id}/{course_slug}/edit/details/"

        request_kwargs = self.get_request_kwargs("GET", request_msg, sessionid)
        response = requests.get(
            url,
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.text.encode("utf-8").strip()

    def course_delete(self, course_id, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Course delete [course_id={course_id}]"

        url = f"{HOST}/ajax/course/delete/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data={
                "course_id": course_id,
            },
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()

    def course_add(self, data, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Course add [name={data.get('name', '')}]"

        url = f"{HOST}/course/create/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data=data,
            allow_redirects=False,
            **request_kwargs,
        )
        self.raise_for_status(response, raise_for_redirect=False)

        if response.status_code >= 300:
            url = response.headers["Location"]

            # Remove the HOST part
            if url.startswith("http"):
                parts = url[8:].split("/", 1)

                if len(parts) == 2:
                    url = "/" + url[1]

            return url.rstrip("/") + "#i_1", None
        else:
            return None, response.text.encode("utf-8").strip()

    def course_picture_upload(self, course_id, file, sessionid=None, csrftoken=None, referer=None, **kwargs):
        request_msg = f"Course edition: upload picture [course_id={course_id}]"

        url = f"{HOST}/ajax/course/picture/"

        request_kwargs = self.get_request_kwargs("POST", request_msg, sessionid, csrftoken, referer)
        response = requests.post(
            url,
            data={
                "course_id": course_id,
                "csrfmiddlewaretoken": request_kwargs.pop("csrftoken", ""),
            },
            files={
                "image_file": (file.filename, file.raw),
            },
            **request_kwargs,
        )
        self.raise_for_status(response)
        return response.json()
