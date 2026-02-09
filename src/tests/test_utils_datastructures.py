import unittest

from utils.datastructures import CaseInsensitiveMapping, SimpleCookie


class UtilsDatastructuresTest(unittest.TestCase):
    def test_case_insensitive_mapping(self):
        ci_map = CaseInsensitiveMapping({'name': 'Jane'})
        
        self.assertEqual(ci_map['Name'], 'Jane')
        self.assertEqual(ci_map['NAME'], 'Jane')
        self.assertEqual(ci_map['name'], 'Jane')
        self.assertEqual(ci_map, {'name': 'Jane'})

    def test_case_insensitive_mapping_tuples(self):
        ci_map = CaseInsensitiveMapping([('Content-Type', 'text/html'), ('Location', 'http://0.0.0.0:8080/')])

        self.assertEqual(ci_map['content-type'], 'text/html')
        self.assertEqual(ci_map.get('content-type', None), 'text/html')
        self.assertIsNone(ci_map.get('cookies', None))

    def test_cookiejar(self):

        cookies = SimpleCookie([
            'a=1; expires=Mon, 09 Feb 2026 13:29:21 GMT; Path=/login/',
            'b=2; expires=Mon, 09 Feb 2026 13:29:21 GMT; Path=/login/',
            'webpy_session_id=b677da8dc0316a12709bd90be8836c29e69571a5; HttpOnly; Path=/',
        ])
        self.assertIsNotNone(cookies.get('a', None))
        self.assertEqual(cookies['a'].value, '1')
        self.assertEqual(cookies['a']['path'], '/login/')
