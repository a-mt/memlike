import requests
import time
from cache import mc
from bs4 import BeautifulSoup, Tag
from variables import categories_code

class Memrise:

    def get_auth(self, force=False):
        """
            Retrieve sessionid
            Is cached via memcached for 31days

            @param boolean force - [False] Force cache refresh
            @return string       - sessionid
        """
        cache_key = "login"
        sessionid = mc.get(cache_key)

        if force or sessionid == None:
            print 'GET ' + cache_key

            sessionid = self.auth()
            mc.set(cache_key, sessionid, time=31*60*60*24)

        return sessionid

    def auth(self):
        """
            Authenticate on Memrise (no caching)

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
        data["username"] = "66b1d91e8e"
        data["password"] = "66b1d91e8e66b1d91e8e!"

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
        else:
            return None

    def courses(self, lang="french", page=1, cat="", query=""):
        """
            Retrieve the list of courses for the given language, category, query string and page
            Is cached via memcached for 24hours (except if query != "")

            @param string lang  - ["french"]
            @param integer page - [1]
            @param string cat   - [""]
            @param string query - [""]
            @return string      - Retrieved JSON
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
            print 'GET ' + cache_key
            url  = 'https://www.memrise.com/ajax/browse/?s_cat=' + lang
            if cat != "":
                url += "&cat=" + cat
            if query != "":
                url += "&q=" + query
            url += '&page=' + str(page) + '&_=' + str(time.time())

            courses = requests.get(url, headers={"Accept-Language": "fr;q=0.8,en-US;q=0.5,en;q=0.3"}).text
            if cache_key:
                mc.set(cache_key, courses, time=60*60*24)

        return courses

    def categories(self, lang="french"):
        """
            Retrieve  the list of categories that have courses for the given language
            Is cached via memcached for 24hours

            @param string lang - ["french"]
            @return dict       - {<idCourse>: True}
        """

        cache_key  = lang + "_categories"
        categories = mc.get(cache_key)

        # Query memrise
        if categories == None:
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

    def course(self, id):
        """
            Retrieve the info about a course
            Is cached via memcached for 24hours

            @throws requests.exceptions.HTTPError
            @param integer id
            @return dict - {id, title, url, author, description, photo, levels, breadcrumb}
        """
        cache_key = "course_" + id
        course    = mc.get(cache_key)

        if course == None:
            print 'GET ' + cache_key
            response = requests.get("https://www.memrise.com/course/" + id)
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

                    name = child.find('div',{'class':'level-title'}).text.strip()
                    idx  = child.find('div',{'class':'level-index'}).text.strip()
                    course["levels"][idx] = name

            mc.set(cache_key, course, time=60*60*24)

        return course

    def level(self, idCourse, lvl):
        """
            Retrieve the info about a course's level
            Is cached via memcached for 24hours

            @throws requests.exceptions.HTTPError
            @param integer idCourse
            @param integer lvl
            @return dict - Retrieved JSON
        """

        cache_key = "course_" + idCourse + "_" + lvl
        level     = mc.get(cache_key)

        if level == None:
            sessionid = self.get_auth()
            print 'GET ' + cache_key

            url      = "https://www.memrise.com/ajax/session/?course_id=" + idCourse + "&level_index=" + lvl + "&session_slug=preview"
            response = requests.get(url, cookies={"sessionid": sessionid})

            # Try reauthenticate
            if response.status_code == 403:
                sessionid = self.get_auth(True)
                response  = requests.get(url, cookies={"sessionid": sessionid})

            response.raise_for_status()
            level = response.json()

            mc.set(cache_key, level, time=60*60*24)
        return level

memrise = Memrise()