from memrise import memrise
from inspect import isgenerator
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
        self.assertIs(type(result), dict)
        self.assertEqual(result.get('username', None), username)
        self.assertIsNotNone(result.get('sessionid', None))
        self.assertIsNotNone(result.get('csrftoken', None))

        self.session['session_id'] = result['sessionid']
        self.session['csrftoken'] = result['csrftoken']

    def test_memrise_whoami(self):
        self.assertIsNotNone(self.session['session_id'])

        result = memrise.whoami(sessionid=self.session['session_id'])

        self.assertIs(type(result), dict)
        self.assertIsNotNone(result.get('sessionid', None))
        self.assertIsNotNone(result.get('username', None))
        self.assertIsNotNone(result.get('photo', None))
        self.assertEqual(result['sessionid'], self.session['session_id'])

    def test_memrise_whatistudy(self):
        self.assertIsNotNone(self.session['session_id'])

        pages = memrise.whatistudy(sessionid=self.session['session_id'])

        # Depending on the backend we might retrieve a generator or a list
        if isgenerator(pages):
            data = next(pages)
        else:
            self.assertIs(type(pages), list)
            self.assertTrue(len(pages) > 0)
            data = pages[0]

        self.assertIs(type(data.get('courses', None)), list)
        self.assertTrue(len(data['courses']) > 0)

        course = data['courses'][0]
        self.assertIsNotNone(course.get('id', None))
        self.assertIsNotNone(course.get('name', None))
        self.assertIsNotNone(course.get('slug', None))
        self.assertIsNotNone(course.get('is_official', None))
        self.assertIsNotNone(course.get('photo_url', None))
        self.assertIsNotNone(course.get('next_session', None))
        self.assertIsNotNone(course.get('progress', None))

    def test_memrise_leaderboard(self):
        self.assertIsNotNone(self.session['session_id'])

        result = memrise.my_leaderboard(period='alltime', sessionid=self.session['session_id'])

        self.assertIs(type(result), dict)
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

        self.assertIs(type(result), dict)
        self.assertTrue(lang_id in result)
        self.assertTrue(result[lang_id])

        # at least the "french" category should have coursess - so {"2": True} is included in result
        self.assertTrue({lang_id: True}.items() <= result.items())

    def test_course_leaderboard(self):
        result = memrise.course_leaderboard(COURSE_ID, period='alltime')

        self.assertIs(type(result), dict)
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

        self.assertIs(type(result), dict)
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

        self.assertIs(type(result), dict)
        self.assertTrue(result.get('nbCourse', 0) > 0)
        self.assertIsNotNone(result.get('content', None))
        self.assertTrue(len(result['content']) > 0)
        self.assertIs(type(result['content'][0]), str)

    def test_courses(self):
        result = memrise.courses(lang='french', page=1)

        self.assertIs(type(result), dict)
        self.assertEqual(result['page'], 1)
        self.assertIsNotNone(result.get('has_next', None))
        self.assertIs(type(result.get('content', None)), str)

    def test_memrise_course(self):
        self.assertIsNotNone(self.session['session_id'])

        result = memrise.course(
            COURSE_ID,
            COURSE_SLUG,
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
        )

        self.assertEqual(result.get('id', None), COURSE_ID)
        self.assertIsNotNone(result.get('title', None))
        self.assertIsNotNone(result.get('description', None))
        self.assertIsNotNone(result.get('author', None))
        self.assertIsNotNone(result.get('photo', None))
        self.assertIsNotNone(result.get('url', None))
        self.assertIsNotNone(result.get('levels', None))
        self.assertIsNotNone(result.get('breadcrumb', None))

        self.assertIs(type(result['breadcrumb']), list)
        self.assertTrue(len(result['breadcrumb']) > 0)
        self.assertIsNotNone(result['breadcrumb'][0].get('name', None))

        self.assertIs(type(result['levels']), dict)
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
        self.assertIs(type(result), str)

        first_char = result[0]
        self.assertTrue(first_char == '"' or first_char == "'", 'Expecting a valid JS var [var multimedia = result]')

    def test_memrise_level(self):
        self.assertIsNotNone(self.session['session_id'])

        result = memrise.level(
            COURSE_ID,
            COURSE_SLUG,
            '1',
            'preview',
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
        )

        self.assertIs(type(result), dict)
        self.assertIs(type(result.get('learnables', None)), list)
        self.assertTrue(len(result['learnables']) > 0)
        self.assertIs(type(result.get('progress', None)), list)
        self.assertIs(type(result.get('session_source_info', None)), dict)
        self.assertIs(type(result.get('settings', None)), dict)

        item = result['learnables'][0]
        self.assertIsNotNone(item.get('id', None))
        self.assertIs(type(item.get('screens', None)), dict)  # SCREEN_ID: SCREEN

        screens = list(item['screens'].values())
        self.assertTrue(len(screens) > 0)

        screen = screens[0]
        self.assertIs(type(screen), dict)
        self.assertEqual(screen.get('template', None), 'presentation')
        self.assertIs(type(screen.get('item', None)), dict)
        self.assertIs(type(screen.get('definition', None)), dict)
        self.assertIs(type(screen.get('visible_info', None)), list)
        self.assertIs(type(screen.get('hidden_info', None)), list)
        self.assertIs(type(screen.get('attributes', None)), list)
        self.assertTrue('audio' in screen)
        self.assertTrue('video' in screen)

        screen = screens[1]
        self.assertEqual(screen.get('template', None), 'multiple_choice')
        self.assertIs(type(screen.get('prompt', None)), dict)
        self.assertIs(type(screen.get('answer', None)), dict)
        self.assertIs(type(screen.get('choices', None)), list)
        self.assertIs(type(screen.get('correct', None)), list)
        self.assertIs(type(screen.get('attributes', None)), list)
        self.assertTrue('audio' in screen)
        self.assertTrue('is_strict' in screen)
