from memrise import memrise

'''
memrise.course_edit(sessionid, idCourse, path)
memrise.course_edit(sessionid, idCourse, slug)
memrise.courses(_GET.lang, _GET.page, _GET.cat, _GET.q)
memrise.leaderboard(idCourse, _GET.period)
memrise.level(idCourse, slugCourse, "1", "preview", sessionid, csrftoken)
memrise.level(idCourse, slugCourse, lvl, "preview", sessionid, csrftoken)
memrise.level(idCourse, slugCourse, lvl, kind, sessionid, csrftoken)
memrise.level_edit(sessionid, idLevel)
memrise.level_multimedia("/course/" + idCourse + "/" + slug + "/", lvl)
memrise.level_multimedia(course['url'], lvl)
memrise.level_multimedia_edit(sessionid, _POST.csrftoken, _POST.referer, idLevel, _POST.txt)
memrise.level_thing_add(sessionid, _POST.csrftoken, _POST.referer, idLevel, _POST.data)
memrise.level_thing_alt(sessionid, _POST.csrftoken, _POST.referer, idThing, _POST.alts, _POST.cellId)
memrise.level_thing_get(sessionid, _POST.csrftoken, _POST.referer, idThing)
memrise.level_thing_remove(sessionid, _POST.csrftoken, _POST.referer, idLevel, _POST.id_thing)
memrise.level_thing_update(sessionid, _POST.csrftoken, _POST.referer, idThing, _POST.cellId, _POST.cellValue)
memrise.level_thing_upload(sessionid, _POST.csrftoken, _POST.referer, idThing, _POST.cellId, _POST.file)
memrise.level_thing_upload_remove(sessionid, _POST.csrftoken, _POST.referer, idThing, _POST.cellId, _POST.fileId)
memrise.user(web.ctx.session['loggedin']['username'], True)
memrise.user(username)
memrise.user_courses(tab, username)
memrise.user_leaderboard(sessionid, _GET.period)
'''
import unittest

SESSION_ID = 'zwrpo2uktmjzby5fla2wl23nlm0vcuto4'


class MemriseTest(unittest.TestCase):

    def test_memrise_whatistudy(self):
        pages = memrise.whatistudy(sessionid=SESSION_ID)

        self.assertTrue(type(pages) is list)
        self.assertTrue(len(pages) > 0)

        courses = pages[0]
        self.assertTrue(type(courses) is list)
        self.assertTrue(len(courses) > 0)

        course = courses[0]
        self.assertIsNotNone(course.get('id', None))
        self.assertIsNotNone(course.get('name', None))
        self.assertIsNotNone(course.get('slug', None))
        self.assertIsNotNone(course.get('is_official', None))
        self.assertIsNotNone(course.get('photo_url', None))
        self.assertIsNotNone(course.get('next_session', None))
        self.assertIsNotNone(course.get('progress', None))

    def test_memrise_categorie(self):
        lang_code = 'french'
        lang_id = '2'

        result = memrise.categories(lang_code)

        self.assertTrue(type(result) is dict)
        self.assertTrue(lang_id in result)
        self.assertTrue(result[lang_id])

        # at least the "french" category should have coursess - so {"2": True} is included in result
        self.assertTrue({lang_id: True}.items() <= result.items())

    def test_memrise_course(self):
        id_course = '6698294'
        result = memrise.course(id_course, sessionid=SESSION_ID)

        self.assertEqual(result.get('id', None), id_course)
        self.assertIsNotNone(result.get('title', None))
        self.assertIsNotNone(result.get('description', None))
        self.assertIsNotNone(result.get('author', None))
        self.assertIsNotNone(result.get('photo', None))
        self.assertIsNotNone(result.get('url', None))
        self.assertIsNotNone(result.get('levels', None))
        self.assertIsNotNone(result.get('breadcrumb', None))

        self.assertTrue(type(result['breadcrumb']) is list)
        self.assertTrue(len(result['breadcrumb']) > 0)
        self.assertIsNotNone(result['breadcrumb'][0].get('name', None))

        self.assertTrue(type(result['levels']) is dict)
        self.assertTrue(len(result['levels']) > 0)
        level = result['levels']['1']
        self.assertIsNotNone(level.get('name', None))
        self.assertIsNotNone(level.get('type', None))   # 1 | 2
        self.assertIsNotNone(level.get('status', None))  # <span class="ico ico-complete ico-correct ico-m ico-green"></span>

        self.assertIsNotNone(result.get('stats', None))
        self.assertIsNotNone(result['stats'].get('ignored', None))
        self.assertIsNotNone(result['stats'].get('learned', None))
        self.assertIsNotNone(result['stats'].get('percent_complete', None))
        self.assertIsNotNone(result['stats'].get('review', None))
        self.assertIsNotNone(result['stats'].get('num_things', None))

    def test_memrise_login(self):
        username = 'bob'
        password = 'pass'

        result = memrise.login(username, password)

        self.assertIsNotNone(result)
        self.assertTrue(type(result) is dict)
        self.assertEqual(result.get('username', None), username)

    def test_memrise_whoami(self):
        result = memrise.whoami(sessionid=SESSION_ID)

        self.assertTrue(type(result) is dict)
        self.assertIsNotNone(result.get('sessionid', None))
        self.assertIsNotNone(result.get('username', None))
        self.assertIsNotNone(result.get('photo', None))
        self.assertEqual(result['sessionid'], SESSION_ID)
