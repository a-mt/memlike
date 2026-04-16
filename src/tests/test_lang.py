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

    def assert_dict_keys(self, VAR1, VAR2, msg):
        for k in VAR1.keys():
            self.assertTrue(k in VAR2, f"{msg}.{k}")

    def assert_module_vars(self, I18N, PREV_I18N):
        for name, var in vars(I18N).items():
            if name.startswith("__"):
                continue

            msg = PREV_I18N.__name__ + " is missing " + name
            self.assertTrue(hasattr(PREV_I18N, name), msg)

            if type(var) is dict:
                self.assert_dict_keys(var, getattr(PREV_I18N, name), msg)

    def test_locales(self):
        locales = lang.get_locales()
        PREV_I18N = None
        FIRST_I18N = None

        for locale in locales:
            I18N = lang.get_module(locale)

            if PREV_I18N:
                self.assert_module_vars(I18N, PREV_I18N)
            else:
                FIRST_I18N = I18N
            PREV_I18N = I18N

        if FIRST_I18N and PREV_I18N:
            self.assert_module_vars(FIRST_I18N, PREV_I18N)

    def test_localized_languages_fr(self):
        """
        localized_languages is a dict(slug: {localized_name, ...}) ordered by localized_name (french)
        """
        I18N = lang.get_module("french")
        languages = lang.get_localized_languages(I18N)

        self.assertEqual(languages["dutch"]["localized_name"], "Néerlandais")
        self.assertEqual(languages["french"]["localized_name"], "Français")

        keys = list(languages.keys())
        self.assertGreater(keys.index("dutch"), keys.index("french"))

    def test_localized_languages_en(self):
        """
        localized_languages is a dict(slug: {localized_name, ...}) ordered by localized_name (french)
        """
        I18N = lang.get_module("english")
        languages = lang.get_localized_languages(I18N)

        self.assertEqual(languages["dutch"]["localized_name"], "Dutch")
        self.assertEqual(languages["french"]["localized_name"], "French")

        keys = list(languages.keys())
        self.assertLess(keys.index("dutch"), keys.index("french"))
