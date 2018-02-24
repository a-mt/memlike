import requests
import time
from cache import mc

class Memrise:
    def courses(self, lang="french", page=1, cat="", query=""):
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

memrise = Memrise()