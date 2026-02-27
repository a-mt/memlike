import unittest

from app import lang


class LangTest(unittest.TestCase):
    def test_en(self):
        i18n = lang.get_module()  # DEFAULT_LANG is set to english for tests
        self.assertEqual(i18n.misc["404"], "The page you're looking for doesn't exist.")

    def test_fr(self):
        i18n = lang.get_module("french")
        self.assertEqual(i18n.misc["404"], "La page que vous cherchez n'existe pas.")

    def test_unknown(self):
        i18n = lang.get_module("err")
        self.assertEqual(i18n.misc["404"], "The page you're looking for doesn't exist.")
