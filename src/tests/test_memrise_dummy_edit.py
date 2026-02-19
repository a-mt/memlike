from memrise import load_memrise
from textwrap import dedent
import settings
import web
from .testcases import SimpleTestCase


COURSE_ID = '6717861'
COURSE_SLUG = 'german'

LEVEL_ID = '16266974'
LEVEL_MULTIMEDIA_ID = '16266978'


class MemriseDummyEditTest(SimpleTestCase):
    session = {}
    idThing = '478400195'
    memrise = load_memrise('memrise.backends.DummyMemrise')

    def setUp(self):
        if 'session_id' in self.session:
            return

        self.init_context()
        self.init_memrise_login()

    def init_context(self):
        """
        Ensure web.ctx exists
        """
        response = self.client.request('/')
        self.assertEqual(response.status_code, 200)

    def init_memrise_login(self):
        username = settings.MEMRISE_ANON_USERNAME or 'bob'
        password = settings.MEMRISE_ANON_PASSWORD or 'pass'

        result = self.memrise.login(username, password)

        self.assertIsNotNone(result)
        self.assertIs(type(result), dict)
        self.assertEqual(result.get('username', None), username)
        self.assertIsNotNone(result.get('sessionid', None))
        self.assertIsNotNone(result.get('csrftoken', None))

        self.session['session_id'] = result['sessionid']
        self.session['csrftoken'] = result['csrftoken']

    def test_memrise_course_edit_get(self):
        result = self.memrise.course_edit_get(
            idCourse=COURSE_ID,
            slugCourse=COURSE_SLUG,
            sessionid=self.session['session_id'],
        )

        self.assertIs(type(result), dict)
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
        result = self.memrise.level_edit_get(idLevel=LEVEL_ID, sessionid=self.session['session_id'])

        self.assertIs(type(result), dict)
        self.assertTrue(result.get('success', False))
        self.assertIs(type(result.get('rendered', None)), str)

    # -------------------------------------------------------------------------
    # THINGS
    # -------------------------------------------------------------------------
    def test_memrise_course_level_thing_add(self):
        result = self.memrise.level_thing_add(
            idLevel=LEVEL_ID,
            data='{"1":"a","2":"b"}',
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
        )

        self.assertIs(type(result), dict)
        self.assertTrue(result.get('success', False))
        self.assertIs(type(result.get('rendered_thing', None)), str)
        self.assertIs(type(result.get('thing', None)), dict)

        thing = result['thing']
        self.assertIsNotNone(thing.get('id', None))
        self.assertIsNotNone(thing.get('pool_id', None))
        self.assertIs(type(thing.get('columns', None)), dict)
        self.assertIs(type(thing.get('attributes', None)), dict)
        self.assertTrue("1" in thing['columns'])

        self.idThing = thing.get('id', None)

        column = thing['columns']['1']
        self.assertIs(type(column.get('alts', None)), list)
        self.assertIs(type(column.get('choices', None)), list)
        self.assertIs(type(column.get('accepted', None)), list)
        self.assertIs(type(column.get('distractors', None)), dict)
        self.assertEqual(column.get('val', None), 'a')
        self.assertEqual(column.get('kind', None), 'text')

    def test_memrise_course_level_thing_get(self):
        result = self.memrise.level_thing_get(
            idThing=self.idThing,
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
        )
        self.assertIs(type(result), dict)
        self.assertIs(type(result.get('thing', None)), dict)

        thing = result['thing']
        self.assertIsNotNone(thing.get('id', None), self.idThing)
        self.assertIsNotNone(thing.get('pool_id', None))
        self.assertIs(type(thing.get('columns', None)), dict)
        self.assertIs(type(thing.get('attributes', None)), dict)
        self.assertTrue("1" in thing['columns'])

        column = thing['columns']['1']
        self.assertIs(type(column.get('alts', None)), list)
        self.assertIs(type(column.get('choices', None)), list)
        self.assertIs(type(column.get('accepted', None)), list)
        self.assertIs(type(column.get('distractors', None)), dict)
        self.assertEqual(column.get('val', None), 'a')
        self.assertEqual(column.get('kind', None), 'text')

    def test_memrise_course_level_thing_edit(self):
        result = self.memrise.level_thing_edit(
            idThing=self.idThing,
            cellId='2',
            cellValue='b2',
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
        )

        self.assertIs(type(result), dict)
        self.assertIsNone(result.get('success', False))

    def test_memrise_course_level_thing_alt_edit(self):
        result = self.memrise.level_thing_alt_edit(
            idThing=self.idThing,
            column_key='2',
            alts='["a2","a3"]',
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
        )

        self.assertIs(type(result), dict)
        self.assertIsNone(result.get('success', False))

    def test_memrise_course_level_thing_upload(self):

        # cgi.FieldStorage / multipart.MultipartPart
        audio = b'\xff\xe3Hd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Xing\x00\x00\x00\x0f\x00\x00\x00\x02\x00\x00\x01\xb0\x00\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00PLAME3.100\x04(\x00\x00\x00\x00\x00\x00\x00\x005\x08$\x02@-\x00\x01\xe0\x00\x00\x01\xb0\xe8W}\xab\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xe3\x18d\x00\x00\x00\x01\xa4\x00\x00\x00\x00\x00\x00\x03H\x00\x00\x00\x00LAME3.100UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU\xff\xe3\x18d3\x00\x00\x01\xa4\x00\x00\x00\x00\x00\x00\x03H\x00\x00\x00\x00UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU' # noqa: E501
        file = web.storage({
            'filename': 'file.mp3',
            'value': audio,
        })
        result = self.memrise.level_thing_upload(
            idThing=self.idThing,
            cellId='3',
            file=file,
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
        )
        self.assertIs(type(result), dict)
        self.assertIsNone(result.get('message', None))
        self.assertTrue(result.get('success', False))
        self.assertIs(type(result.get('rendered', None)), str)

    def test_memrise_course_level_thing_upload_remove(self):
        result = self.memrise.level_thing_upload_remove(
            idThing=self.idThing,
            cellId='3',
            fileId='1',
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
        )

        self.assertIs(type(result), dict)
        self.assertTrue(result.get('success', False))
        self.assertIs(type(result.get('rendered', None)), str)

    def test_memrise_course_level_thing_remove(self):
        result = self.memrise.level_thing_remove(
            idLevel=LEVEL_ID,
            idThing=self.idThing,
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
        )

        self.assertIs(type(result), dict)
        self.assertTrue(result.get('success', False))

    # -------------------------------------------------------------------------
    # MULTIMEDIA
    # -------------------------------------------------------------------------

    def test_memrise_course_level_multimedia_edit(self):
        txt = dedent('''
        <b>img:http://cdni.wired.co.uk/620x413/a_c/ALEX_LAKE.jpg</b>.

        <br />
        2. Für Youtube-Videos, schreibe "embed:" vor die URL, z.B.

        <br /><b>embed:https://www.youtube.com/watch?v=P5f1Y3CWTc0</b>.

        <br />
        3. Um deinen Text fett erscheinen zu lassen, klammer ihn mit "**" ein, z.B.

        <br /><b>"spiel **nicht** mit dem Feuer"</b>.
        " name="new_val">
        ''')
        result = self.memrise.level_multimedia_edit(
            idLevel=LEVEL_MULTIMEDIA_ID,
            txt=txt,
            sessionid=self.session['session_id'],
            csrftoken=self.session['csrftoken'],
            referer='',
        )

        self.assertIs(type(result), dict)
        self.assertTrue(result.get('success', False))
        self.assertIs(type(result.get('multimedia', None)), str)
