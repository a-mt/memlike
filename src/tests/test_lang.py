import unittest

from app import lang


class LangTest(unittest.TestCase):
    def test_en(self):
        lang._load()
        self.assertEqual(lang.misc['404'], "The page you're looking for doesn't exist.")

    def test_fr(self):
        lang.session.lang = 'french'
        lang._load()
        self.assertEqual(lang.misc['404'], "La page que vous cherchez n'existe pas.")

    def test_unknown(self):
        lang.session.lang = 'err'
        lang._load()
        self.assertEqual(lang.misc['404'], "The page you're looking for doesn't exist.")
