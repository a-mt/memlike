from memrise.backends.api import Requestor
import unittest
import settings


COURSE_ID = '6698294'
COURSE_SLUG = 'german-vocab'

requestor = Requestor()


class MemriseBackendApiRequestorTest(unittest.TestCase):
    session = {}

    def test_first_memrise_login(self):
        data = requestor.login(settings.MEMRISE_ANON_USERNAME, settings.MEMRISE_ANON_PASSWORD)
        '''
        data = {
            'username': '66b1d91e8e',
            'is_new': False,
            'id': 34497740,
            'sessionid': '3kynx9h9rz3y39dnlbettooa7tmmdfri1',
            'csrftoken': 'FLGeZ73gj52vXs0loEw7TkhgtS9URX5d',
        }
        '''
        self.assertIsNotNone(data.get('username', None))
        self.assertIsNotNone(data.get('sessionid', None))
        self.assertIsNotNone(data.get('csrftoken', None))

        self.session['session_id'] = data['sessionid']
        self.session['csrftoken'] = data['csrftoken']

    def test_memrise_requestor_course(self):
        self.assertIsNotNone(self.session.get('session_id'))

        result = requestor.course(
            COURSE_ID,
            COURSE_SLUG,
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
        )
        self.assertIs(type(result), bytes)

        # Second request with the same csrftoken is still working
        result = requestor.course(
            COURSE_ID,
            COURSE_SLUG,
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
        )
        self.assertIs(type(result), bytes)

    def test_memrise_requestor_level(self):
        self.assertIsNotNone(self.session.get('session_id'))

        result = requestor.level(
            COURSE_ID,
            '1',
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
        )
        self.assertIs(type(result), dict)
        self.assertIsNotNone(result.get('learnables', None))

    def test_memrise_requestor_leaderboard(self):
        self.assertIsNotNone(self.session.get('session_id'))

        result = requestor.course_leaderboard(
            COURSE_ID,
            period='alltime',
            sessionid=self.session['session_id'],
        )
        self.assertIs(type(result), dict)
        self.assertIsNotNone(result.get('rows', None))
