from memrise import memrise

import unittest
import web

COURSE_ID = '6698294'
COURSE_SLUG = 'german-vocab'


class MemriseEditTest(unittest.TestCase):
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

    def test_memrise_course_edit_get(self):
        result = memrise.course_edit_get(sessionid=self.session['session_id'], idCourse=COURSE_ID, slugCourse=COURSE_SLUG)

        self.assertTrue(type(result) is dict)
        self.assertIsNotNone(result.get('csrftoken', None))
        self.assertIsNotNone(result.get('referer', None))
        self.assertIsNotNone(result.get('url', None))
        self.assertIsNotNone(result.get('title', None))
        self.assertIsNotNone(result.get('levels', None))
        self.assertTrue(len(result['levels']))

        level = result['levels'][0]
        self.assertIsNotNone(level.get('id', None))
        self.assertIsNotNone(level.get('pool', None))
        self.assertIsNotNone(level.get('name', None))

    def test_memrise_level_edit_get(self):
        result = memrise.level_edit_get(sessionid=self.session['session_id'], idLevel='16180581')

        self.assertTrue(type(result) is dict)
        self.assertTrue(result.get('success', False))
        self.assertTrue(type(result.get('rendered', None)) is str)

    # -------------------------------------------------------------------------
    # THINGS
    # -------------------------------------------------------------------------
    def test_memrise_course_level_thing_add(self):
        result = memrise.level_thing_add(
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
            idLevel='16258912',
            data={
                'columns': {"1":"a","2":"b","4":"plural"},
                'level_id': "16258912"
            }
        )

        self.assertTrue(type(result) is dict)
        self.assertTrue(result.get('success', False))
        self.assertTrue(type(result.get('rendered_thing', None)) is str)
        self.assertTrue(type(result.get('thing', None)) is dict)

        thing = result['thing']
        self.assertIsNotNone(thing.get('id', None))
        self.assertIsNotNone(thing.get('pool_id', None))
        self.assertIsNotNone(type(thing.get('columns', None)) is dict)
        self.assertIsNotNone(type(thing.get('attributes', None)) is dict)
        self.assertTrue("1" in thing['columns'])

        column = thing['columns']['1']
        self.assertTrue(type(column.get('alts', None)) is list)
        self.assertTrue(type(column.get('choices', None)) is list)
        self.assertTrue(type(column.get('accepted', None)) is list)
        self.assertTrue(type(column.get('distractors', None)) is dict)
        self.assertEqual(column.get('val', None), 'a')
        self.assertEqual(column.get('kind', None), 'text')

    def test_memrise_course_level_thing_get(self):
        result = memrise.level_thing_get(
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
            idThing='477757876',
        )
        self.assertTrue(type(result) is dict)
        self.assertTrue(type(result.get('thing', None)) is dict)

        thing = result['thing']
        self.assertIsNotNone(thing.get('id', None), '477757876')
        self.assertIsNotNone(thing.get('pool_id', None))
        self.assertIsNotNone(type(thing.get('columns', None)) is dict)
        self.assertIsNotNone(type(thing.get('attributes', None)) is dict)
        self.assertTrue("1" in thing['columns'])

        column = thing['columns']['1']
        self.assertTrue(type(column.get('alts', None)) is list)
        self.assertTrue(type(column.get('choices', None)) is list)
        self.assertTrue(type(column.get('accepted', None)) is list)
        self.assertTrue(type(column.get('distractors', None)) is dict)
        self.assertEqual(column.get('val', None), 'a')
        self.assertEqual(column.get('kind', None), 'text')

    def test_memrise_course_level_thing_edit(self):
        result = memrise.level_thing_edit(
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
            idThing='477757811',
            cellId='2',
            cellValue='b2',
        )

        self.assertTrue(type(result) is dict)
        self.assertIsNone(result.get('success', False))

    def test_memrise_course_level_thing_alt_edit(self):
        result = memrise.level_thing_alt_edit(
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
            idThing='477757811',
            column_key='2',
            alts='["a2","a3"]',
        )

        self.assertTrue(type(result) is dict)
        self.assertIsNone(result.get('success', False))

    def test_memrise_course_level_thing_upload(self):

        # cgi.FieldStorage / multipart.MultipartPart
        file = web.storage({
            'filename': 'file.txt',
            'value': 'Lorem ispum',
        })
        result = memrise.level_thing_upload(
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
            idThing='477757811',
            cellId='2',
            file=None,
        )
        self.assertTrue(type(result) is dict)
        self.assertTrue(result.get('success', False))
        self.assertTrue(type(result.get('rendered', None)) is str)

    def test_memrise_course_level_thing_upload_remove(self):
        result = memrise.level_thing_upload_remove(
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
            idThing='477757811',
            cellId='2',
            fileId='1',
        )

        self.assertTrue(type(result) is dict)
        self.assertTrue(result.get('success', False))
        self.assertTrue(type(result.get('rendered', None)) is str)

    def test_memrise_course_level_thing_remove(self):
        result = memrise.level_thing_remove(
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
            idLevel='16258912',
            idThing='16258912',
        )

        self.assertTrue(type(result) is dict)
        self.assertTrue(result.get('success', False))

    # -------------------------------------------------------------------------
    # MULTIMEDIA
    # -------------------------------------------------------------------------

    def test_memrise_course_level_multimedia_edit(self):
        result = memrise.level_multimedia_edit(
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
            idLevel='16258913',
            txt='',
        )

        self.assertTrue(type(result) is dict)
        self.assertTrue(result.get('success', False))
        self.assertTrue(type(result.get('multimedia', None)) is str)
