import requests, re
import time
from cache import mc
from bs4 import BeautifulSoup, Tag
from variables import categories_code

def get_time():
    return '%d' % (time.time() * 1000)

class Memrise:

    #+-----------------------------------------------------
    #| AUTH
    #+-----------------------------------------------------
    def get_auth(self, force=False):
        """
            Retrieve sessionid to retrieve content (using our own account)
            Is cached via memcached for 1day

            @param boolean force - [False] Force cache refresh
            @return string       - sessionid
        """
        cache_key = "login"
        sessionid = mc.get(cache_key)
        if force or sessionid == None:
            with mc.lock(cache_key) as retries:

                # Check if we set memcached while we were waiting for the lock
                if retries:
                    sessionid = mc.get(cache_key)
                    if sessionid:
                        return sessionid

                print 'GET ' + cache_key

                sessionid = self.login("66b1d91e8e", "66b1d91e8e66b1d91e8e!")
                mc.set(cache_key, sessionid, time=60*60*24)

        return sessionid

    def login(self, username, password):
        """
            Authenticate on Memrise (no caching) with the given username and password
            Throws 403 if the username or password isn't right

            @throws requests.exceptions.HTTPError
            @param string username
            @param string password
            @return string - sessionid
        """
        data     = {}
        cookies  = {}

        # Retrieve cookies and CRSF token
        response = requests.get("https://www.memrise.com/login/")
        cookies  = response.cookies
        html     = response.text.encode('utf-8').strip()
        DOM      = BeautifulSoup(html, "html5lib", from_encoding='utf-8')

        form = DOM.find(id="login")

        if form != None:
            for input in form.find_all('input'):
                if "value" in input.attrs and "name" in input.attrs:
                    data[input.attrs['name']] = input.attrs['value']

        # Login
        data["username"] = username
        data["password"] = password

        headers = {
            "Origin": "https://www.memrise.com",
            "Referer": "https://www.memrise.com/login/",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.167 Chrome/64.0.3282.167 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post("https://www.memrise.com/login/", data=data, cookies=cookies, headers=headers)
        response.raise_for_status()

        if "sessionid" in response.cookies:
            return response.cookies['sessionid']
        elif "sessionid_2" in response.cookies:
            return response.cookies['sessionid_2']
        else:
            return None

    def whoami(self, sessionid):
        """
            Retrieve the username and photo of current user

            @throws requests.exceptions.HTTPError
            @param string sessionid
            @return dict - {sessionid, username, photo}
        """
        response  = requests.get("https://www.memrise.com/settings/", cookies={"sessionid": sessionid})
        response.raise_for_status()

        html = response.text.encode('utf-8').strip()
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

    def whatistudy(self, sessionid):
        """
            Retrieve the list of courses of current user

            @throws requests.exceptions.HTTPError
            @param string sessionid
            @return dict
        """
        nbperpage = 4
        offset    = 0

        while True:
            url       = "https://www.memrise.com/ajax/courses/dashboard/?courses_filter=most_recent&offset=" + str(offset) + "&limit=" + str(nbperpage-1) + "&get_review_count=true"
            response  = requests.get(url, cookies={"sessionid": sessionid})
            response.raise_for_status()

            data      = response.json()
            offset   += nbperpage
            yield data['courses']

            if not 'has_more_courses' in data or not data['has_more_courses']:
                break

    def user_leaderboard(self, sessionid, period):
        """
            Retrieve the learderboard of the current user (50 first)

            @throws requests.exceptions.HTTPError
            @param string sessionid
            @param string period - month, week, alltime
            @return dict - Retrieved JSON
        """
        url      = "https://www.memrise.com/ajax/leaderboard/mempals/?period=" + period + "&how_many=50"
        response = requests.get(url, cookies={"sessionid": sessionid})
        response.raise_for_status()
        return response.json()

    def track_progress(self, path, data, sessionid, csrftoken, referer):
        """
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
            url = "https://www.memrise.com/ajax/session_end/"
        else:
            url = "https://www.memrise.com/api/garden/register/"

        response = requests.post(url, data=data, cookies={"sessionid": sessionid, "csrftoken": csrftoken}, headers={
            "Origin": "https://www.memrise.com",
            "Referer": referer,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.167 Chrome/64.0.3282.167 Safari/537.36",
            "X-CSRFToken": csrftoken
        })
        response.raise_for_status()
        return response.json()

    #+-----------------------------------------------------
    #| COURSES
    #+-----------------------------------------------------
    def courses(self, lang, page=1, cat="", query=""):
        """
            Retrieve the list of courses for the given language, category, query string and page
            Is cached via memcached for 24hours (except if query != "")

            @param string lang
            @param integer[optional] page - [1]
            @param string[optional] cat   - [""]
            @param string[optional] query - [""]
            @return string                - Retrieved JSON
        """
        if not isinstance(page, int) and not page.isdigit():
            page = 0

        # Check cache
        if query != "":
            cache_key = False
            courses   = None
        else:
            cache_key = lang + '_courses_' + str(page) + '_' + cat
            courses   = mc.get(cache_key)

        # Query memrise
        if courses == None:
            with mc.lock(cache_key) as retries:

                # Check if we set memcached while we were waiting for the lock
                if retries:
                    courses = mc.get(cache_key)
                    if courses:
                        return courses

                if cache_key:
                    print 'GET ' + cache_key

                url  = 'https://www.memrise.com/ajax/browse/?s_cat=' + lang
                if cat != "":
                    url += "&cat=" + cat
                if query != "":
                    url += "&q=" + query
                url += '&page=' + str(page) + '&_=' + get_time()

                courses = requests.get(url, headers={"Accept-Language": "fr;q=0.8,en-US;q=0.5,en;q=0.3"}).text
                if cache_key:
                    mc.set(cache_key, courses, time=60*60*24)

        return courses

    #+-----------------------------------------------------
    #| CATEGORIES
    #+-----------------------------------------------------
    def categories(self, lang):
        """
            Retrieve  the list of categories that have courses for the given language
            Is cached via memcached for 24hours

            @param string lang
            @return dict       - {<idCourse>: True}
        """

        cache_key  = lang + "_categories"
        categories = mc.get(cache_key)

        # Query memrise
        if categories == None:
            with mc.lock(cache_key) as retries:

                # Check if we set memcached while we were waiting for the lock
                if retries:
                    categories = mc.get(cache_key)
                    if categories:
                        return categories

                print 'GET ' + cache_key
                html = requests.get("https://www.memrise.com/fr/courses/" + lang + "/").text.encode('utf-8').strip()

                # Parse HTML
                DOM = BeautifulSoup(html, "html5lib", from_encoding='utf-8')
                ul  = DOM.find_all('ul',{'class':'categories-list'}).pop()

                def parseCategories(ul):
                    for li in ul.findChildren():
                        if not 'data-category-id' in li.attrs:
                            continue

                        id = li.attrs['data-category-id']
                        categories[id] = True

                        if li.ul:
                            parseCategories(li.ul)

                categories = {}
                parseCategories(ul)
                mc.set(cache_key, categories, time=60*60*24)

        return categories

    #+-----------------------------------------------------
    #| COURSE
    #+-----------------------------------------------------
    def course(self, id, sessionid=False):
        """
            Retrieve the info about a course
            Is cached via memcached for 24hours

            @throws requests.exceptions.HTTPError
            @param integer id
            @return dict - {id, title, url, author, description, photo, levels, breadcrumb}
        """
        if sessionid:
            cache_key = False
            course    = None
        else:
            cache_key = "course_" + id
            course    = mc.get(cache_key)

        if course == None:
            with mc.lock(cache_key) as retries:

                # Check if we set memcached while we were waiting for the lock
                if retries:
                    course = mc.get(cache_key)
                    if course:
                        return course

                if sessionid:
                    response = requests.get("https://www.memrise.com/course/" + id, cookies={"sessionid": sessionid})
                else:
                    print 'GET ' + cache_key
                    sessionid = self.get_auth()
                    response  = requests.get("https://www.memrise.com/course/" + id, cookies={"sessionid": sessionid})

                response.raise_for_status()
                html = response.text.encode('utf-8').strip()

                # Parse HTML
                DOM    = BeautifulSoup(html, "html5lib", from_encoding='utf-8')
                course = {
                    "id"         : id,
                    "title"      : "",
                    "url"        : "",
                    "author"     : "",
                    "description": "",
                    "photo"      : "",
                    "levels"     : {},
                    "breadcrumb" : []
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
                        if sessionid:
                            status = child.find('div', {'class':'level-status'})
                            if status != None:
                                course["levels"][idx]["status"] = re.sub("\s+", " ", str(status))

                if sessionid:
                    stats = self._course_progress(DOM)
                    if stats != None:
                        course['stats'] = stats

                if cache_key:
                    mc.set(cache_key, course, time=60*60*24)
        return course

    def _course_progress(self, DOM):
        """
            Retrieve the given user progress for a given course

            @throws requests.exceptions.HTTPError
            @param Node DOM
            @return dict - {ignored, learned, percent_complete, review_num_things}
        """
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
                res = re.search("^(\d+) ?/ ?(\d+)", text.strip())
                if res:
                    stats["learned"]      = int(res.group(1))
                    stats["num_things"]   = int(res.group(2))

            text = item.find(attrs={"class":"pull-right"})
            if text:
                res = re.search("^(\d+)", text.text.strip())
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
            res = re.search("\((\d+)\)", item.text)
            if res:
                stats["review"] = int(res.group(1))

        return stats

    #+-----------------------------------------------------
    #| COURSE > LEVEL
    #+-----------------------------------------------------
    def level(self, idCourse, slugCourse, lvl, slug="preview", sessionid=False):
        """
            Retrieve the list of items of a level (wont work for multimedia)
            Is cached via memcached for 24hours if sessionid isn't provided

            @throws requests.exceptions.HTTPError
            @param integer idCourse
            @param integer|string lvl - index | "all"
            @param string slug
            @param string session
            @return dict - Retrieved JSON
        """
        if slug == "speed_review":
            slug = "classic_review"

        if sessionid:
            user_session = True
            cache_key    = False
            level        = None
        else:
            user_session = False
            cache_key    = "course_" + idCourse + "_" + lvl + "_" + slug
            level        = mc.get(cache_key)

        if level == None:
            with mc.lock(cache_key) as retries:

                # Check if we set memcached while we were waiting for the lock
                if retries:
                    level = mc.get(cache_key)
                    if level:
                        return level

                if not sessionid:
                    sessionid = self.get_auth()
                    print 'GET ' + cache_key

                url = "https://www.memrise.com/ajax/session/?course_id=" + idCourse
                if lvl != "all":
                    url += "&level_index=" + lvl
                url += "&session_slug=" + slug

                if slug != "preview":
                    url += "&_=" + get_time()
                response = requests.get(url, cookies={"sessionid": sessionid})

                # Try reauthenticate
                if user_session == False and response.status_code == 403:
                    sessionid = self.get_auth(True)
                    response  = requests.get(url, cookies={"sessionid": sessionid})

                response.raise_for_status()
                level = response.json()

                if user_session and slug != "preview":
                    url      = "https://www.memrise.com/course/" + idCourse + "/" + slugCourse + "/garden/" + slug +"/"
                    response = requests.head(url, cookies={"sessionid": sessionid})
                    response.raise_for_status()
                    level['referer']   = url
                    level['csrftoken'] = response.cookies.get('csrftoken')

                if cache_key:
                    mc.set(cache_key, level, time=60*60*24)
        return level

    def level_multimedia(self, urlCourse, lvl):
        """
            Retrieve the content of a multimedia level
            Is cached via memcached for 24hours

            @throws requests.exceptions.HTTPError
            @param string urlCourse - ex "/course/43238/durham-university-medicine-year-one/"
            @param integer lvl
            @return dict - Retrieved JSON
        """
        pattern = re.search("/course/(\d+)/", urlCourse)
        if pattern:
            idCourse = pattern.group(1)
        else:
            return False

        cache_key = "course_" + idCourse + "_" + lvl + "_multimedia"
        data      = mc.get(cache_key)

        if data == None:
            with mc.lock(cache_key) as retries:

                # Check if we set memcached while we were waiting for the lock
                if retries:
                    data = mc.get(cache_key)
                    if data:
                        return data

                url      = "https://www.memrise.com" + urlCourse + lvl + "/"
                response = requests.get(url)
                response.raise_for_status()

                # Get response
                html = response.text.encode('utf-8').strip()
                DOM  = BeautifulSoup(html, "html5lib", from_encoding='utf-8')
                data = False

                # Look for value of js variable "level_multimedia"
                scripts = DOM.html.body.find_all("script", recursive=False)
                for script in scripts:
                    text = script.text.strip()
                    if text and text.startswith("var level_multimedia = "):
                        data = text[23:].strip(';')
                        break

                mc.set(cache_key, data, time=60*60*24)
        return data

    #+-----------------------------------------------------
    #| COURSE > LEADERBOARD
    #+-----------------------------------------------------
    def leaderboard(self, idCourse, period):
        """
            Retrieve the learderboard of a course (50 first)
            Is cached via memcached for 1hour

            @throws requests.exceptions.HTTPError
            @param integer idCourse
            @param string period - month, week, alltime
            @return dict - Retrieved JSON
        """
        cache_key = "course_" + idCourse + "_learderboard_" + period
        ldboard   = mc.get(cache_key)

        if ldboard == None:
            with mc.lock(cache_key) as retries:

                # Check if we set memcached while we were waiting for the lock
                if retries:
                    ldboard = mc.get(cache_key)
                    if ldboard:
                        return ldboard

                sessionid = self.get_auth()
                print 'GET ' + cache_key

                url      = "https://www.memrise.com/ajax/leaderboard/course/" + idCourse + "/?period=" + period + "&how_many=50"
                response = requests.get(url, cookies={"sessionid": sessionid})

                # Try reauthenticate
                if response.status_code == 403:
                    sessionid = self.get_auth(True)
                    response  = requests.get(url, cookies={"sessionid": sessionid})

                response.raise_for_status()
                ldboard = response.json()

                mc.set(cache_key, ldboard, time=60*60*24)
        return ldboard

    #+-----------------------------------------------------
    #| USER
    #+-----------------------------------------------------
    # https://www.memrise.com/api/user/get/?user_id=2224242&with_leaderboard=true&_=1520004351621
    def user(self, username, force=False):
        """
            Retrieve the info about a user
            Is cached via memcached for 1hour

            @throws requests.exceptions.HTTPError
            @param string username
            @param boolean[optional] force - [false] Get data from Memrise even if already cached
            @return dict - {username, photo, rank, stats}
        """
        cache_key = "user_" + username
        user      = None if force else mc.get(cache_key)

        if user == None:
            with mc.lock(cache_key) as retries:

                # Check if we set memcached while we were waiting for the lock
                if retries:
                    user = mc.get(cache_key)
                    if user:
                        return user

                print 'GET ' + cache_key
                response = requests.get("https://www.memrise.com/user/" + username + "/courses/teaching/")
                response.raise_for_status()

                html = response.text.encode('utf-8').strip()
                DOM  = BeautifulSoup(html, "html5lib", from_encoding='utf-8')
                user = {
                    "username": username,
                    "photo"   : "",
                    "rank"    : 0,
                    "stats"   : {}
                }

                div = DOM.find(id="page-head")
                if div != None:

                    # Get avatar
                    item = div.find('img', {'class':'avatar'})
                    if item != None:
                        user['photo'] = item.attrs['src']

                    # Get rank
                    item = div.find('img', {'class':'rank-icon'})
                    if item != None:
                        result = re.search('/([^/]*)_(\d+)\.(.*)$', item.attrs['src'])
                        if result:
                            user['rank'] = int(result.group(2))

                    # Get stats (num followers, following, words, points)
                    div = div.find(attrs={'class' : 'profile-stats'})
                    for child in div.children:
                        if not isinstance(child, Tag):
                            continue

                        text   = child.text.strip()
                        result = re.search('([0-9,]+)([\n\w ]*)', text)
                        if result:
                            tab = result.group(2).strip().lower()

                            # force plural
                            if tab == "follower":
                                tab = "followers"
                            elif tab == "word":
                                tab = "words"
                            user["stats"][tab] = result.group(1)

                div = DOM.find(id="content")
                if div != None:

                    # Get nb courses
                    item = div.find('div',{'class','btn-group'})
                    if item != None:
                        for child in item.children:
                            if not isinstance(child, Tag):
                                continue

                            result = re.search('\(([0-9,]+)\)', child.text)
                            if result:
                                tab = child.attrs['href'].strip('/').split('/')[-1]
                                user["stats"][tab] = result.group(1)

                mc.set(cache_key, user, time=60*60)
        return user

    def user_followers(self, username, page=1):
        return self._user_mempals("followers", username, page)

    def user_following(self, username, page=1):
        return self._user_mempals("following", username, page)

    def _user_mempals(self, mempals, username, page=1):
        """
            Retrieve the list of followers of a user or followed users
            Is cached via memcached for 1hour

            @throws requests.exceptions.HTTPError
            @param string mempals - followers  following
            @param string username
            @param integer page - [1]
            @return dict - {page, lastpage, users}
        """
        if not isinstance(page, int):
            if page.isdigit():
                page = int(page)
            else:
                page = 1

        cache_key    = "user_" + username + "_" + mempals
        cache_paging = True
        data         = mc.get(cache_key)

        # Check we dont cache the last page multiple times
        if data != None:
            cache_paging = False
            if page > data:
                page = data
            data = mc.get(cache_key + "_" + str(page))

        # Get the given page
        cache_key_page = cache_key + "_" + str(page)
        if data == None:
            with mc.lock(cache_key_page) as retries:

                # Check if we set memcached while we were waiting for the lock
                if retries:
                    data = mc.get(cache_key_page)
                    if data:
                        return data

                print 'GET ' + cache_key_page
                response = requests.get("https://www.memrise.com/user/" + username + "/mempals/" + mempals + "/?page=" + str(page))
                response.raise_for_status()

                html = response.text.encode('utf-8').strip()
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

                    data['page']    = currentPage
                    data['lastpage'] = lastpage

                    if cache_paging:
                        mc.set(cache_key, data['lastpage'], time=60*60)

                mc.set(cache_key + '_' + str(currentPage), data, time=60*60)

        data['has_next'] = data['page'] < data['lastpage']
        return data

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
            Is cached via memcached for 1hour

            @throws requests.exceptions.HTTPError
            @param string tab      - teaching | learning
            @param string username
            @return dict - {content, nbCourse}
        """
        cache_key = "user_" + username + "_" + tab
        courses   = mc.get(cache_key)

        if courses == None:
            with mc.lock(cache_key) as retries:

                # Check if we set memcached while we were waiting for the lock
                if retries:
                    courses = mc.get(cache_key)
                    if courses:
                        return courses

                print 'GET ' + cache_key
                response = requests.get("https://www.memrise.com/user/" + username + "/courses/" + tab + "/")
                response.raise_for_status()

                html = response.text.encode('utf-8').strip()
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

                mc.set(cache_key, courses, time=60*60)
        return courses

    #+-----------------------------------------------------
    #| EDIT
    #+-----------------------------------------------------
    def level_edit(self, sessionid, idLevel):
        url      = "https://www.memrise.com/ajax/level/editing_html/?level_id=" + idLevel + "&_=" + get_time()
        response = requests.get(url, cookies={"sessionid": sessionid})
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_add(self, sessionid, csrftoken, referer, idLevel, data):
        url      = "https://www.memrise.com/ajax/level/thing/add/"

        response = requests.post(url, data={"columns":data, "level_id":idLevel}, cookies={"sessionid": sessionid, "csrftoken": csrftoken}, headers={
            "Origin": "https://www.memrise.com",
            "Referer": referer,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.167 Chrome/64.0.3282.167 Safari/537.36",
            "X-CSRFToken": csrftoken,
            "X-Requested-With": "XMLHttpRequest"
        })
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_update(self, sessionid, csrftoken, referer, idThing, cellId, cellValue):
        url      = "https://www.memrise.com/ajax/thing/cell/update/"

        response = requests.post(url,
            data={
                "cell_id": cellId,
                "cell_type": "column",
                "new_val": cellValue,
                "thing_id": idThing
            },
            cookies={"sessionid": sessionid, "csrftoken": csrftoken},
            headers={
                "Origin": "https://www.memrise.com",
                "Referer": referer,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.167 Chrome/64.0.3282.167 Safari/537.36",
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest"
            })
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_upload(self, sessionid, csrftoken, referer, idThing, cellId, file):
        url      = "https://www.memrise.com/ajax/thing/cell/upload_file/"

        response = requests.post(url,
            data={
                "cell_id": cellId,
                "cell_type": "column",
                "thing_id": idThing
            },
            files={"f": (file.filename, file.value)},
            cookies={"sessionid": sessionid, "csrftoken": csrftoken},
            headers={
                "Origin": "https://www.memrise.com",
                "Referer": referer,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.167 Chrome/64.0.3282.167 Safari/537.36",
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest"
            })
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_upload_remove(self, sessionid, csrftoken, referer, idThing, cellId, fileId):
        url      = "https://www.memrise.com/ajax/thing/column/delete_from/"

        response = requests.post(url,
            data={
                "column_key": cellId,
                "cell_type": "column",
                "thing_id": idThing,
                "file_id": fileId
            },
            cookies={"sessionid": sessionid, "csrftoken": csrftoken},
            headers={
                "Origin": "https://www.memrise.com",
                "Referer": referer,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.167 Chrome/64.0.3282.167 Safari/537.36",
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest"
            })
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_remove(self, sessionid, csrftoken, referer, idLevel, idThing):
        url      = "https://www.memrise.com/ajax/level/thing_remove/"

        response = requests.post(url, data={"thing_id":idThing, "level_id":idLevel}, cookies={"sessionid": sessionid, "csrftoken": csrftoken}, headers={
            "Origin": "https://www.memrise.com",
            "Referer": referer,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.167 Chrome/64.0.3282.167 Safari/537.36",
            "X-CSRFToken": csrftoken,
            "X-Requested-With": "XMLHttpRequest"
        })
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_get(self, sessionid, csrftoken, referer, idThing):
        url      = "https://www.memrise.com/api/thing/get/?thing_id=" + idThing + "&_=" + get_time()

        response = requests.get(url,
            cookies={"sessionid": sessionid, "csrftoken": csrftoken},
            headers={
                "Origin": "https://www.memrise.com",
                "Referer": referer,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.167 Chrome/64.0.3282.167 Safari/537.36",
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest"
            })
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_thing_alt(self, sessionid, csrftoken, referer, idThing, alts, column_key):
        url      = "https://www.memrise.com/ajax/thing/column/update_alts/"
        response = requests.post(url,
            data={
                "alts": alts,
                "column_key": column_key,
                "thing_id": idThing
            },
            cookies={"sessionid": sessionid, "csrftoken": csrftoken},
            headers={
                "Origin": "https://www.memrise.com",
                "Referer": referer,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.167 Chrome/64.0.3282.167 Safari/537.36",
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest"
            })
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def level_multimedia_edit(self, sessionid, csrftoken, referer, idLevel, txt):
        url      = "https://www.memrise.com/ajax/level/set_multimedia/"

        response = requests.post(url, data={"multimedia":txt, "level_id":idLevel}, cookies={"sessionid": sessionid, "csrftoken": csrftoken}, headers={
            "Origin": "https://www.memrise.com",
            "Referer": referer,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.167 Chrome/64.0.3282.167 Safari/537.36",
            "X-CSRFToken": csrftoken,
            "X-Requested-With": "XMLHttpRequest"
        })
        response.raise_for_status()
        return response.text.encode('utf-8').strip()

    def course_edit(self, sessionid, idCourse, slugCourse):
        url      = "https://www.memrise.com/course/" + idCourse + "/" + slugCourse + "/edit/"
        response = requests.get(url, cookies={"sessionid": sessionid})
        response.raise_for_status()

        html = response.text.encode('utf-8').strip()
        DOM  = BeautifulSoup(html, "html5lib", from_encoding='utf-8')
        data = {
            "csrftoken": response.cookies.get('csrftoken'),
            "referer": url
        }

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

memrise = Memrise()
