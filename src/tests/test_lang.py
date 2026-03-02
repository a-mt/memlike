import unittest

from app import lang


class LangTest(unittest.TestCase):
    def test_en(self):
        I18N = lang.get_module()  # DEFAULT_LANG_SLUG is set to english for tests
        self.assertEqual(I18N.misc["404"], "The page you're looking for doesn't exist.")

    def test_fr(self):
        I18N = lang.get_module("french")
        self.assertEqual(I18N.misc["404"], "La page que vous cherchez n'existe pas.")

    def test_unknown(self):
        I18N = lang.get_module("err")
        self.assertEqual(I18N.misc["404"], "The page you're looking for doesn't exist.")
