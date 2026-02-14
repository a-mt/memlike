import requests, re, sys
import time
import json

from cache import mc
from bs4 import BeautifulSoup, Tag
from variables import categories_code, levels
from .base import Memrise


OAUTH_CLIENT_ID = "1e739f5e77704b57a703"
USER_AGENT      = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.167 Chrome/64.0.3282.167 Safari/537.36"
ORIGIN          = "https://app.memrise.com"


def get_time():
    return '%d' % (time.time() * 1000)


class Requestor:
    """
    Performs requests to Memrise
    The result might still need to be scraped to conform to our Memrise interface
    """

    #+-----------------------------------------------------
    #| AUTH
    #+-----------------------------------------------------
    def login(self, username, password):
        data     = {}
        cookies  = {}

        #-----------------------------------------------------------------------
        # Retrieve CRSF token
        headers = {
            "Referer": "https://app.memrise.com/signin",
            "User-Agent": USER_AGENT,
        }
        response  = requests.get("https://app.memrise.com/v1.17/web/ensure_csrf")
        response.raise_for_status()

        json      = response.json()
        csrftoken = json['csrftoken']

        #-----------------------------------------------------------------------
        # Retrieve access_token (login)
        headers['Origin']      = ORIGIN
        headers['X-CSRFToken'] = csrftoken

        cookies = {
            'csrftoken': csrftoken
        }
        data = {
            'client_id' : OAUTH_CLIENT_ID,
            'grant_type': 'password',
            'username'  : username,
            'password'  : password
        }
        response  = requests.post("https://app.memrise.com/v1.17/auth/access_token/", cookies=cookies, headers=headers, data=data)
        response.raise_for_status()

        json = response.json()
        data = json['user']

        #-----------------------------------------------------------------------
        # Retrieve sessionid_2
        del headers['Origin']
        del headers['X-CSRFToken']

        token     = json['access_token']['access_token']
        response  = requests.get("https://app.memrise.com/v1.17/auth/web/?invalidate_token_after=true&token=" + token, cookies=cookies, headers=headers)
        response.raise_for_status()

        data['sessionid'] = response.cookies["sessionid_2"]
        data['csrftoken'] = response.cookies["csrftoken"]

        return data

    #+-----------------------------------------------------
    #| CURRENT USER
    #+-----------------------------------------------------
    def whoami(self, sessionid):
        url = "https://app.memrise.com/settings/"

        response = requests.get(url, cookies={"sessionid_2": sessionid})
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def whatistudy(self, sessionid, offset, nbperpage):
        #url = f"https://app.memrise.com/ajax/courses/dashboard/?courses_filter=most_recent&offset={offset}&limit={nbperpage-1}&get_review_count=true"
        url = f"https://app.memrise.com/v1.21/dashboard/courses/?filter=recent&offset={offset}&limit={nbperpage-1}"

        response = requests.get(url, cookies={"sessionid_2": sessionid})
        response.raise_for_status()
        return response.json()

    def my_leaderboard(self, sessionid, period):
        url = "https://app.memrise.com/ajax/leaderboard/mempals/?period=" + period + "&how_many=50"

        response = requests.get(url, cookies={"sessionid_2": sessionid})
        response.raise_for_status()
        return response.json()

    def track_progress(self, path, data, sessionid, csrftoken, referer):
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
        if path == "session_end":
            url = "https://app.memrise.com/ajax/session_end/"
        else:
            url = "https://app.memrise.com/api/garden/register/"

        response = requests.post(url, data=data, cookies={"sessionid_2": sessionid, "csrftoken": csrftoken}, headers={
            "Origin": ORIGIN,
            "Referer": referer,
            "User-Agent": USER_AGENT,
            "X-CSRFToken": csrftoken
        })
        response.raise_for_status()
        return response.json()

    #+-----------------------------------------------------
    #| COURSES
    #+-----------------------------------------------------
    def courses(self, lang, page, cat, query):
        url  = 'https://app.memrise.com/ajax/browse/?s_cat=' + lang
        if cat != "":
            url += "&cat=" + cat
        if query != "":
            url += "&q=" + query
        url += '&page=' + str(page) + '&_=' + get_time()

        response = requests.get(url, headers={"Accept-Language": "fr;q=0.8,en-US;q=0.5,en;q=0.3"})
        return response.text.encode('utf-8').strip()

    #+-----------------------------------------------------
    #| CATEGORIES
    #+-----------------------------------------------------
    def categories(self, lang):
        url = "https://app.memrise.com/fr/courses/" + lang + "/"

        response = requests.get(url)
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    #+-----------------------------------------------------
    #| COURSE
    #+-----------------------------------------------------
    def course(self, sessionid, idCourse):
        url = "https://app.memrise.com/course/" + idCourse

        response = requests.get(url, cookies={"sessionid_2": sessionid})
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    #+-----------------------------------------------------
    #| COURSE > LEVEL
    #+-----------------------------------------------------
    def level(self, sessionid, csrftoken, idCourse, lvl):
        url = "https://app.memrise.com/v1.21/learning_sessions/preview/"
        referer = f"https://app.memrise.com/aprender/preview?course_id=${idCourse}&level_index=${lvl}"

        response = requests.post(
            url,
            cookies={
                "sessionid_2": sessionid,
                "csrftoken": csrftoken,
            },
            headers={
                "Origin": ORIGIN,
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
            }
        )
        response.raise_for_status()
        return response.json()

    def level_learning_session(self, sessionid, idCourse, slugCourse, sessionType):
        url = "https://app.memrise.com/course/" + idCourse + "/" + slugCourse + "/garden/" + sessionType + "/"

        response = requests.head(url, cookies={"sessionid_2": sessionid})
        response.raise_for_status()
        return {
            "referer": url,
            "csrftoken": response.cookies.get("csrftoken"),
        }

    def level_multimedia(self, urlCourse, lvl):
        url = "https://app.memrise.com" + urlCourse + lvl + "/"

        response = requests.get(url)
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    #+-----------------------------------------------------
    #| COURSE > LEADERBOARD
    #+-----------------------------------------------------
    def course_leaderboard(self, sessionid, idCourse, period):
        url = "https://app.memrise.com/ajax/leaderboard/course/" + idCourse + "/?period=" + period + "&how_many=50"

        response = requests.get(url, cookies={"sessionid_2": sessionid})
        response.raise_for_status()
        return response.json()

    #+-----------------------------------------------------
    #| USER
    #+-----------------------------------------------------
    def user(self, username):
        url = "https://app.memrise.com/user/" + username + "/courses/teaching/"

        response = requests.get(url)
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def user_mempals(self, tab, username, page):
        url = "https://app.memrise.com/user/" + username + "/mempals/" + tab + "/?page=" + str(page)

        response = requests.get(url)
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    #+-----------------------------------------------------
    #| USER's COURSES
    #+-----------------------------------------------------
    def user_courses(self, tab, username):
        url = "https://app.memrise.com/user/" + username + "/courses/" + tab + "/"

        response = requests.get(url)
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    #+-----------------------------------------------------
    #| EDIT
    #+-----------------------------------------------------
    def level_edit_get(self, sessionid, idLevel):
        url = "https://app.memrise.com/ajax/level/editing_html/?level_id=" + idLevel + "&_=" + get_time()

        response = requests.get(url, cookies={"sessionid_2": sessionid})
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_add(self, sessionid, csrftoken, referer, idLevel, data):
        url = "https://app.memrise.com/ajax/level/thing/add/"

        response = requests.post(
            url,
            data={
                "columns":data,
                "level_id":idLevel,
            },
            cookies={
                "sessionid_2": sessionid,
                "csrftoken": csrftoken,
            },
            headers={
                "Origin": ORIGIN,
                "Referer": referer,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_edit(self, sessionid, csrftoken, referer, idThing, cellId, cellValue):
        url = "https://app.memrise.com/ajax/thing/cell/update/"

        response = requests.post(
            url,
            data={
                "cell_id": cellId,
                "cell_type": "column",
                "new_val": cellValue,
                "thing_id": idThing
            },
            cookies={
                "sessionid_2": sessionid,
                "csrftoken": csrftoken,
            },
            headers={
                "Origin": ORIGIN,
                "Referer": referer,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest"
            })
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_upload(self, sessionid, csrftoken, referer, idThing, cellId, file):
        url = "https://app.memrise.com/ajax/thing/cell/upload_file/"

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
                "thing_id": idThing
            },
            files={
                "f": (file.filename, file.value),  # files={FILENAME: file-like-object}
            },
            cookies={
                "sessionid_2": sessionid,
                "csrftoken": csrftoken,
            },
            headers={
                "Origin": ORIGIN,
                "Referer": referer,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            })
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_upload_remove(self, sessionid, csrftoken, referer, idThing, cellId, fileId):
        url = "https://app.memrise.com/ajax/thing/column/delete_from/"

        response = requests.post(
            url,
            data={
                "column_key": cellId,
                "cell_type": "column",
                "thing_id": idThing,
                "file_id": fileId
            },
            cookies={
                "sessionid_2": sessionid,
                "csrftoken": csrftoken,
            },
            headers={
                "Origin": ORIGIN,
                "Referer": referer,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            })
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_remove(self, sessionid, csrftoken, referer, idLevel, idThing):
        url = "https://www.memrise.com/ajax/level/thing_remove/"

        response = requests.post(
            url,
            data={
                "thing_id":idThing,
                "level_id":idLevel,
            },
            cookies={
                "sessionid_2": sessionid,
                "csrftoken": csrftoken,
            },
            headers={
                "Origin": ORIGIN,
                "Referer": referer,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_get(self, sessionid, csrftoken, referer, idThing):
        url = "https://app.memrise.com/api/thing/get/?thing_id=" + idThing + "&_=" + get_time()

        response = requests.get(
            url,
            cookies={
                "sessionid_2": sessionid,
                "csrftoken": csrftoken,
            },
            headers={
                "Origin": ORIGIN,
                "Referer": referer,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_alt_edit(self, sessionid, csrftoken, referer, idThing, alts, column_key):
        url = "https://app.memrise.com/ajax/thing/column/update_alts/"

        response = requests.post(
            url,
            data={
                "alts": alts,
                "column_key": column_key,
                "thing_id": idThing
            },
            cookies={
                "sessionid_2": sessionid,
                "csrftoken": csrftoken,
            },
            headers={
                "Origin": ORIGIN,
                "Referer": referer,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_multimedia_edit(self, sessionid, csrftoken, referer, idLevel, txt):
        url = "https://app.memrise.com/ajax/level/set_multimedia/"

        response = requests.post(
            url,
            data={
                "multimedia":txt,
                "level_id":idLevel,
            },
            cookies={
                "sessionid_2": sessionid,
                "csrftoken": csrftoken,
            },
            headers={
                "Origin": ORIGIN,
                "Referer": referer,
                "User-Agent": USER_AGENT,
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def course_edit_get(self, sessionid, idCourse, slugCourse):
        url = "https://app.memrise.com/course/" + idCourse + "/" + slugCourse + "/edit/"

        response = requests.get(url, cookies={"sessionid_2": sessionid})
        response.raise_for_status()

        html = response.text.encode('utf-8').strip()
        csrftoken = response.cookies.get('csrftoken')

        return {
            "csrftoken": csrftoken,
            "referer": url,
            "html": html
        }


class Scraper:

    #+-----------------------------------------------------
    #| CURRENT USER
    #+-----------------------------------------------------
    def whoami(self, sessionid, html):
        DOM  = BeautifulSoup(html, "html5lib", from_encoding='utf-8')
        data = {
            "sessionid": sessionid
        }

        div  = DOM.find(id="content")
        if div != None:

            # Get username
            item = div.find(id="id_username")
            if item != None:
                data["username"] = item.attrs["value"]

            # Get photo
            item = div.find('div', {'class':'thumbnail'})
            if item != None:
                data["photo"] = item.img.attrs["src"]

        return data

    #+-----------------------------------------------------
    #| CATEGORIES
    #+-----------------------------------------------------
    def categories(self, html):
        DOM = BeautifulSoup(html, "html5lib", from_encoding='utf-8')
        ul_list = DOM.find_all('ul',{'class':'categories-list'})

        def parseCategories(ul):
            for li in ul.findChildren():
                if not 'data-category-id' in li.attrs:
                    continue

                id = li.attrs['data-category-id']
                categories[id] = True

                if li.ul:
                    parseCategories(li.ul)

        categories = {}
        if len(ul_list):
            parseCategories(ul_list.pop())

        return categories

    #+-----------------------------------------------------
    #| COURSE
    #+-----------------------------------------------------
    def course(self, idCourse, html, isLoggedIn=False):
        DOM    = BeautifulSoup(html, "html5lib", from_encoding='utf-8')
        course = {
            "id"         : idCourse,
            "title"      : "",
            "url"        : "",
            "author"     : "",
            "description": "",
            "photo"      : "",
            "levels"     : {},
            "breadcrumb" : [],
        }

        div = DOM.find('div',{'class','course-wrapper'})
        if div != None:

            # Title
            item = div.find(itemprop="name")
            if item != None:
                course['title'] = item.text

            # Description
            item = div.find(itemprop="about")
            if item != None:
                course['description'] = item.text

            # Author (only when logged in :/)
            item = div.find(itemprop="author")
            if item != None:
                course['author'] = item.find(itemprop="additionalName").text

            # Categories
            item = div.find('div',{'class','course-breadcrumb'})
            if item != None:
                for child in item.find_all('a'):
                    cat = child.attrs['href'].strip('/').split('/').pop()

                    if cat in categories_code:
                        course["breadcrumb"].append({
                            "id"  : categories_code[cat],
                            "name": cat
                        })

            # Photo + url
            item = div.find('a',{'class','course-photo'})
            if item != None:
                course["url"]   = item.attrs['href']
                course["photo"] = item.img.attrs['src']

        # List of levels
        div = DOM.find('div',{'class':'levels'})
        if div != None:

            for child in div.children:
                if not isinstance(child, Tag):
                    continue

                name   = child.find('div',{'class':'level-title'}).text.strip()
                idx    = child.find('div',{'class':'level-index'}).text.strip()
                ico    = child.find(attrs={'class':'level-ico'}).attrs['class'].pop()

                course["levels"][idx] = {
                    "name": name,
                    "type": (2 if ico == 'level-ico-multimedia-inactive' or ico == 'level-ico-multimedia' else 1)
                }
                if isLoggedIn:
                    status = child.find('div', {'class':'level-status'})
                    if status != None:
                        course["levels"][idx]["status"] = re.sub(r"\s+", " ", str(status))

        if isLoggedIn:
            stats = self._course_progress(DOM)
            if stats != None:
                course['stats'] = stats

        return course

    def _course_progress(self, DOM):
        stats = {
            "ignored": 0,
            "learned": 0,
            "percent_complete": 0,
            "review": 0,
            "num_things": 0
        }

        div = DOM.find('div',{'class','progress-box-course'})
        if div == None:
            return None

        # Ignored, learned, total
        item = div.find('div',{'class':'progress-box-title'})
        if item != None:
            text = item.find(text=True, recursive=False)
            if text:
                res = re.search(r"^(\d+) ?/ ?(\d+)", text.strip())
                if res:
                    stats["learned"]      = int(res.group(1))
                    stats["num_things"]   = int(res.group(2))

            text = item.find(attrs={"class":"pull-right"})
            if text:
                res = re.search(r"^(\d+)", text.text.strip())
                if res:
                    stats["ignored"]     = int(res.group(1))
                    stats["num_things"] += int(res.group(1))

            # Percentage complete
            if stats["learned"] > 0:
                if stats["num_things"] == 0:
                    stats["percent_complete"] = 100
                else:
                    stats["percent_complete"] = int(float(stats["learned"]) / (stats["num_things"] - stats["ignored"]) * 100)

        # Review
        item = div.find('a',{'class':'blue'})
        if item != None:
            res = re.search(r"\((\d+)\)", item.text)
            if res:
                stats["review"] = int(res.group(1))

        return stats

    #+-----------------------------------------------------
    #| COURSE > LEVEL
    #+-----------------------------------------------------
    def level_multimedia(self, html):
        DOM  = BeautifulSoup(html, "html5lib", from_encoding='utf-8')
        data = None

        # Look for value of js variable "level_multimedia"
        VAR_MULTIMEDIA = "var level_multimedia = "
        scripts = DOM.html.body.find_all("script", string=True, recursive=False)
        for script in scripts:
            text = script.string.strip()

            if text and text.startswith(VAR_MULTIMEDIA):
                data = text[len(VAR_MULTIMEDIA):].strip(';')
                break

        return data

    #+-----------------------------------------------------
    #| USER
    #+-----------------------------------------------------
    def user(self, username, html):
        DOM  = BeautifulSoup(html, "html5lib", from_encoding='utf-8')
        user = {
            "username": username,
            "photo"   : "",
            "points"  : 0,
            "rank"    : 0,
            "stats"   : {}
        }

        div = DOM.find(id="page-head")
        if div != None:

            # Get avatar
            item = div.find('img', {'class':'avatar'})
            if item != None:
                user['photo'] = item.attrs['src']

            # Get stats (num followers, following, word|words|word|wörter, leaderboard)
            # Note that we're supposed to request memrise in english
            div = div.find(attrs={'class' : 'profile-stats'})
            for child in div.children:
                if not isinstance(child, Tag):
                    continue

                text   = child.text.strip()
                result = re.search(r'([0-9,]+)([\n\w ]*)', text)
                if result:
                    link = child.find('a')
                    if link:
                        tab = link.attrs['href'].strip('/').split('/')[-1]
                    else:
                        tab = result.group(2).strip().lower()

                    if tab == "leaderboard":
                        tab = "points"
                    elif tab == "word":
                        tab = "words"

                    user["stats"][tab] = result.group(1)

        if "points" in user["stats"]:
            points = int(user["stats"]["points"].replace(",",""))
            rank   = 0

            for i, threshold in enumerate(levels):
                if threshold < points:
                    rank = i
                else:
                    break
            user["rank"] = rank+1

        div = DOM.find(id="content")
        if div != None:

            # Get stats
            # {'following': '1', '': '1', 'wort': '0', 'punkte': '660', 'learning': '1', 'teaching': '61'}
            item = div.find('div',{'class','btn-group'})
            if item != None:
                for child in item.children:
                    if not isinstance(child, Tag):
                        continue

                    result = re.search(r'\(([0-9,]+)\)', child.text)
                    if result:
                        tab = child.attrs['href'].strip('/').split('/')[-1]
                        user["stats"][tab] = result.group(1)
                    else:
                        tab = ""

        return user

    def user_mempals(self, username, page, html):
        DOM   = BeautifulSoup(html, "html5lib", from_encoding='utf-8')
        data  = {
            "page": page,
            "lastpage": 0,
            "users": []
        }

        # Get list of followers
        div   = DOM.find(id="content")
        if div != None:
            users = div.find_all(attrs={'class': 'user-box'})
            for user in users:
                username = user.find(attrs={'class': 'username'})
                img      = user.find('img')
                if username == None:
                    continue

                item = {
                    "name" : username.text.strip(),
                    "photo": img.attrs['src'] if img else ""
                }
                data["users"].append(item)

        # Get current page + max page number
        div  = DOM.find('ul', {'class':'pagination'})
        currentPage = page
        lastpage    = 0

        if div != None:
            for child in div.children:
                if not isinstance(child, Tag):
                    continue

                text = child.text.strip()
                if not re.match('[0-9]+', text):
                    continue

                lastpage = int(text)
                if 'class' in child.attrs and 'active' in child.attrs['class']:
                    currentPage = lastpage

            data['page']     = currentPage
            data['lastpage'] = lastpage
            data['has_next'] = data['page'] < data['lastpage']

        return data

    #+-----------------------------------------------------
    #| USER's COURSES
    #+-----------------------------------------------------
    def user_courses(self, html):
        DOM  = BeautifulSoup(html, "html5lib", from_encoding='utf-8')
        courses = {
            "nbCourse": 0,
            "content": []
        }

        # Get list of courses
        div = DOM.find(id="content")
        if div != "None":
            content = div.find_all("div",{"class":"course-box-wrapper"})

            for wrapper in content:
                courses["content"].append(str(wrapper))
                courses["nbCourse"] += 1

        return courses

    #+-----------------------------------------------------
    #| EDIT
    #+-----------------------------------------------------
    def course_edit_get(self, data_pointer, html):
        data = data_pointer
        DOM  = BeautifulSoup(html, "html5lib", from_encoding='utf-8')

        # Course data
        div = DOM.find(id="page-head")
        if div != None:
            item = div.find('div', {'class':'course-details'})
            if item != None:
                data['url']   = item.a.attrs['href']
                data['title'] = item.text.strip()

        # Levels
        div    = DOM.find(id="levels")
        levels = []

        if div != None:
            for child in div.findChildren(attrs={"class":"level"}):
                level  = {"id": child.attrs['data-level-id']}
                header = child.find('div', {"class": "level-header"}, recursive=False)

                if "data-pool-id" in child.attrs:
                    level["pool"] = child.attrs["data-pool-id"]

                if header != None:
                    level["name"] = header.h3.text.strip()

                levels.append(level)
        data['levels'] = levels

        return data


class ApiMemrise(Memrise):
    def __init__(self):
        self.requestor = Requestor()
        self.scraper = Scraper()

    def _login_as_anonymous(self):
        """
            Retrieve sessionid to retrieve content (using our own account)

            @return string - sessionid
        """
        session = self.login("66b1d91e8e", "66b1d91e8e66b1d91e8e!")
        return session['sessionid']

    def login(self, username, password):
        return self.requestor.login(username, password)

    def whoami(self, sessionid):
        html = self.requestor.whoami(sessionid)

        return self.scraper.whoami(sessionid, html)

    def whatistudy(self, sessionid):
        nbperpage = 4
        offset    = 0

        while True:
            data    = self.requestor.whatistudy(sessionid, offset, nbperpage)
            offset += nbperpage
            yield data['courses']

            if not 'has_more_pages' in data or not data['has_more_pages']:
                break

    def my_leaderboard(self, sessionid, period):
        return self.requestor.my_leaderboard(sessionid, period)

    def track_progress(self, path, data, sessionid, csrftoken, referer):
        return self.requestor.track_progress(path, data, sessionid, csrftoken, referer)

    def courses(self, lang, page=1, cat="", query=""):
        if not isinstance(page, int) and not page.isdigit():
            page = 0

        return self.requestor.courses(lang=lang, page=page, cat=cat, query=query)

    def categories(self, lang):
        html = self.requestor.categories(lang)

        return self.scraper.categories(html)

    def course(self, idCourse, sessionid=False, csrftoken=None):
        html = self.requestor.course(sessionid, idCourse)

        return self.scraper.course(idCourse, html, isLoggedIn=sessionid)

    def level(self, idCourse, slugCourse, lvl, slug="preview", sessionid=False, csrftoken=None):
        if not sessionid:
            is_anonymous_session = True
            sessionid = self._login_as_anonymous()
        else:
            is_anonymous_session = False

        if not csrftoken:
            csrftoken = "ZS9AlStmGDO0tpKhS8bnz1bz0q4GqN0"

        if slug == "speed_review":
            slug = "classic_review"

        # Retrieve level info
        retry_login = True
        level = {}
        while retry_login:
            try:
                level = self.requestor.level(sessionid, csrftoken, idCourse, lvl)
            except requests.exceptions.HTTPError as e:

                # Try reauthenticate
                if e.response.status_code == 403 and is_anonymous_session and retry_login:
                    sessionid = self._login_as_anonymous(True)
                else:
                    raise e
            finally:
                retry_login = False

        # Start learning session (to be able to send results to memrise)
        if not is_anonymous_session and slug != "preview":
            session = self.requestor.level_learning_session(sessionid, idCourse, slugCourse, sessionType=slug)
            level.update(session)

        return level

    def level_multimedia(self, urlCourse, lvl):
        html = self.requestor.level_multimedia(urlCourse, lvl)

        return self.scraper.level_multimedia(html)

    def course_leaderboard(self, idCourse, period):
        sessionid = self._login_as_anonymous()
        retry_login = True
        ldboard = {}
        while retry_login:
            try:
                ldboard = self.requestor.course_leaderboard(sessionid, idCourse, period)
            except requests.exceptions.HTTPError as e:

                # Try reauthenticate
                if e.response.status_code == 403 and retry_login:
                    sessionid = self._login_as_anonymous(True)
                else:
                    raise e
            finally:
                retry_login = False

        return {
            "rows": ldboard.get("users", []),
        }

    def user(self, username):
        html = self.requestor.user(username)

        return self.scraper.user(username, html)

    def user_mempals(self, tab, username, page=1):
        html = self.requestor.user_mempals(tab, username, page)

        return self.scraper.user_mempals(username, page, html)

    def user_courses(self, tab, username):
        html = self.requestor.user_courses(tab, username)

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

    def course_edit_get(self, sessionid, idCourse, slugCourse):
        data = self.requestor.course_edit_get(sessionid, idCourse, slugCourse)
        html = data.pop("html")
        self.scraper.course_edit_get(data, html)

        return data
