from memrise import memrise

'''
memrise.level(idCourse, slugCourse, "1", "preview", sessionid, csrftoken)
memrise.level(idCourse, slugCourse, lvl, "preview", sessionid, csrftoken)
memrise.level(idCourse, slugCourse, lvl, kind, sessionid, csrftoken)
'''
import unittest

COURSE_ID = '6698294'
COURSE_SLUG = 'german-vocab'


class MemriseGetTest(unittest.TestCase):
    session = {}

    def test_first_memrise_login(self):
        username = 'bob'
        password = 'pass'

        result = memrise.login(username, password)

        self.assertIsNotNone(result)
        self.assertTrue(type(result) is dict)
        self.assertEqual(result.get('username', None), username)
        self.assertIsNotNone(result.get('sessionid', None))
        self.assertIsNotNone(result.get('csrftoken', None))

        self.session['session_id'] = result['sessionid']
        self.session['csrftoken'] = result['csrftoken']

    def test_memrise_whoami(self):
        self.assertIsNotNone(self.session['session_id'])

        result = memrise.whoami(sessionid=self.session['session_id'])

        self.assertTrue(type(result) is dict)
        self.assertIsNotNone(result.get('sessionid', None))
        self.assertIsNotNone(result.get('username', None))
        self.assertIsNotNone(result.get('photo', None))
        self.assertEqual(result['sessionid'], self.session['session_id'])

    def test_memrise_whatistudy(self):
        self.assertIsNotNone(self.session['session_id'])

        pages = memrise.whatistudy(sessionid=self.session['session_id'])

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

    def test_memrise_leaderboard(self):
        self.assertIsNotNone(self.session['session_id'])

        result = memrise.my_leaderboard(self.session['session_id'], period='alltime')

        self.assertTrue(type(result) is dict)
        self.assertTrue('rows' in result)
        self.assertTrue(len(result['rows']) > 0)

        row = result['rows'][0]

        self.assertEqual(row['position'], 1)
        self.assertIsNotNone(row.get('points', None))
        self.assertIsNotNone(row.get('username', None))
        self.assertIsNotNone(row.get('photo', None))
        self.assertIsNotNone(row.get('uid', None))

    def test_memrise_categories(self):
        lang_code = 'french'
        lang_id = '2'

        result = memrise.categories(lang_code)

        self.assertTrue(type(result) is dict)
        self.assertTrue(lang_id in result)
        self.assertTrue(result[lang_id])

        # at least the "french" category should have coursess - so {"2": True} is included in result
        self.assertTrue({lang_id: True}.items() <= result.items())

    def test_course_leaderboard(self):
        result = memrise.course_leaderboard(COURSE_ID, period='alltime')

        self.assertTrue(type(result) is dict)
        self.assertTrue('rows' in result)
        self.assertTrue(len(result['rows']) > 0)

        row = result['rows'][0]

        self.assertEqual(row['position'], 1)
        self.assertIsNotNone(row.get('points', None))
        self.assertIsNotNone(row.get('username', None))
        self.assertIsNotNone(row.get('photo', None))
        self.assertIsNotNone(row.get('uid', None))

    def test_memrise_user(self):
        result = memrise.user(username='bob')

        self.assertTrue(type(result) is dict)
        self.assertIsNotNone(result.get('username', None))
        self.assertIsNotNone(result.get('photo', None))
        self.assertIsNotNone(result.get('rank', None))
        self.assertIsNotNone(result.get('stats', None))

        stats = result['stats']
        self.assertIsNotNone(stats.get('following', None))
        self.assertIsNotNone(stats.get('followers', None))
        self.assertIsNotNone(stats.get('words', None))
        self.assertIsNotNone(stats.get('points', None))
        self.assertIsNotNone(stats.get('learning', None))
        self.assertIsNotNone(stats.get('teaching', None))

    def test_user_courses(self):
        result = memrise.user_courses(tab='teaching', username='bob')

        self.assertTrue(type(result) is dict)
        self.assertTrue(result.get('nbCourse', 0) > 0)
        self.assertIsNotNone(result.get('content', None))
        self.assertTrue(len(result['content']) > 0)
        self.assertTrue(type(result['content'][0]) is str)

    def test_courses(self):
        result = memrise.courses(lang='french', page=1)

        self.assertTrue(type(result) is dict)
        self.assertEqual(result['page'], 1)
        self.assertIsNotNone(result.get('has_next', None))
        self.assertTrue(type(result.get('content', None)) is str)

    def test_memrise_course(self):
        self.assertIsNotNone(self.session['session_id'])

        result = memrise.course(COURSE_ID, sessionid=self.session['session_id'], csrftoken=self.session['csrftoken'])

        self.assertEqual(result.get('id', None), COURSE_ID)
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

    def test_memrise_level_multimedia(self):
        result = memrise.level_multimedia(f"/course/{COURSE_ID}/{COURSE_SLUG}/", "1")

        self.assertTrue(type(result) is str)

    def disable_test_memrise_level(self):
        self.assertIsNotNone(self.session['session_id'])

        result = memrise.level(
            COURSE_ID,
            COURSE_SLUG,
            '1',
            'preview',
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
        )
        self.assertTrue('todo' is False)
