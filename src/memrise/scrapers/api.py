import re

from bs4 import BeautifulSoup, Tag
from variables import categories_code, USER_RANKS, languages


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
    # | COURSES
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
    def course(self, course_id, html, is_logged_in=False):
        assert len(html) > 0

        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")
        course = {
            "id": course_id,
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
            if item is None:
                item = div.find(rel="author")

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
                index = child.find("div", {"class": "level-index"}).text.strip()
                ico = child.find(attrs={"class": "level-ico"}).attrs["class"].pop()

                course["levels"][index] = {
                    "name": name,
                    "type": (2 if ico == "level-ico-multimedia-inactive" or ico == "level-ico-multimedia" else 1),
                }
                if is_logged_in:
                    status = child.find("div", {"class": "level-status"})
                    if status is not None:
                        course["levels"][index]["status"] = re.sub(r"\s+", " ", str(status))

        # List of things (course without levels)
        div = DOM.find("div", {"class": "things"})
        if div is not None:
            things = 0

            for child in div.find_all("div", {"class": "thing"}, recursive=False):
                things += 1

            course["nb_things"] = things

        if is_logged_in:
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
            "nb_things": 0,
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
                    stats["nb_things"] = int(res.group(2))

            text = item.find(attrs={"class": "pull-right"})
            if text:
                res = re.search(r"^(\d+)", text.text.strip())
                if res:
                    stats["ignored"] = int(res.group(1))
                    stats["nb_things"] += int(res.group(1))

            # Percentage complete
            if stats["learned"] > 0:
                if stats["nb_things"] == 0:
                    stats["percent_complete"] = 100
                else:
                    percent = float(stats["learned"])
                    percent /= float(stats["nb_things"]) - float(stats["ignored"])
                    stats["percent_complete"] = int(percent * 100)

        # Review
        item = div.find("div", {"class": "actions-right"})
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

            for i, threshold in enumerate(USER_RANKS):
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
    # | USER > COURSES
    # +-----------------------------------------------------
    def user_courses(self, html):
        assert len(html) > 0

        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")
        courses = {
            "nb_courses": 0,
            "content": [],
        }

        # Get list of courses
        div = DOM.find(id="content")
        if div != "None":
            content = div.find_all("div", {"class": "course-box-wrapper"})

            for wrapper in content:
                courses["content"].append(str(wrapper))
                courses["nb_courses"] += 1

        return courses

    # +-----------------------------------------------------
    # | COURSE EDIT
    # +-----------------------------------------------------

    def course_get_editpage(self, data_pointer, html):
        assert len(html) > 0

        data = data_pointer
        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")

        # Course data
        div = DOM.find(id="page-head")
        if div is not None:
            item = div.find("div", {"class": "course-details"})
            if item is not None:
                data["url"] = item.a.attrs["href"]
                data["slug"] = data["url"].strip("/").split("/")[-1]
                data["title"] = item.text.strip()

        # Levels
        last_pool_id = None
        div = DOM.find(id="levels")
        levels = []

        if div is not None:
            for child in div.find_all(attrs={"class": "level"}, recursive=False):
                level = {"id": child.attrs["data-level-id"]}
                header = child.find("div", {"class": "level-header"}, recursive=False)

                if "data-pool-id" in child.attrs:
                    last_pool_id = level["pool_id"] = child.attrs["data-pool-id"]

                if header is not None:
                    level["name"] = header.h3.text.strip()

                levels.append(level)
        data["levels"] = levels

        # Pool-id
        if last_pool_id is None:
            actions = div.find_previous_sibling("div", {"class": "row-fluid"})
            if actions is not None:
                item = actions.find_all("a", {"data-pool-id": True})

                last_pool_id = item.attrs["data-pool-id"]

        data["last_pool_id"] = last_pool_id
        return data

    def _get_form_iteminput_value(self, node):
        nodeType = node.attrs.get("type", "text")

        match nodeType:
            case "hidden":
                return node.attrs.get("value", "")
            case "text":
                return node.attrs.get("value", "")
            case "checkbox":
                return node.attrs.get("checked", None) is not None
            case _:
                raise NotImplementedError(f"inputs of type {nodeType} aren't handled")

    def _get_form_item_value(self, node):
        match node.name:
            case "input":
                return self._get_form_iteminput_value(node)
            case "textarea":
                return node.text.strip()
            case "select":
                opt = node.find("option", attrs={"selected": True})
                if opt is not None:
                    return opt.attrs.get("value", "")
            case _:
                raise NotImplementedError(f"items of type {node.name} aren't handled")

    def course_get_editdetails(self, html):
        assert len(html) > 0

        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")
        div = DOM.find(id="content")

        aria_invalid = {}
        data = {
            "aria_invalid": aria_invalid,
        }

        # All form elements
        course_details = div.find(attrs={"class": "course-details-form"})
        if course_details is not None:
            items = course_details.find_all(attrs={"name": True})

            for item in items:
                name = item.attrs["name"]
                data[name] = self._get_form_item_value(item)

                # Check if there's an associated error
                is_invalid = item.attrs.get("aria-invalid", None)
                if is_invalid:
                    error = item.find_next_sibling("ul", {"class": "errorlist"})

                    aria_invalid[name] = error.text.strip() if error else ""

        # Photo
        course_photo = div.find(attrs={"class": "course-photo-form"})
        if course_photo is not None:
            img = course_photo.find("img")

            if img is not None:
                data["photo"] = img.attrs["src"]

        return data

    def course_add(self, html):
        DOM = BeautifulSoup(html, "html5lib", from_encoding="utf-8")

        div = DOM.find("form")
        errors = []

        if not div:
            return errors

        for child in div.find_all("div", {"class": "control-group"}, recursive=False):
            error = child.find("ul", {"class": "errorlist"})

            if not error:
                continue

            label = child.find("label")
            if not label:
                continue

            errors.append(
                {
                    "id": label.attrs["for"],
                    "message": error.text.strip(),
                }
            )
        return errors
