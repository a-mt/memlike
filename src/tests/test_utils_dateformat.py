import datetime
import unittest
import web
from app import lang
from utils.dateformat import date_format


DATE = datetime.datetime(2020, 12, 31)


class UtilsDateFormatTest(unittest.TestCase):
    def test_date_format_en(self):
        self.assertEqual(date_format(DATE, "%a"), "Thu")
        self.assertEqual(date_format(DATE, "%A"), "Thursday")
        self.assertEqual(date_format(DATE, "%b"), "Dec")
        self.assertEqual(date_format(DATE, "%B"), "December")

        date_fmt = web.ctx.i18n.formats.get("DATE_FORMAT", "%x")

        self.assertEqual(date_format(DATE, date_fmt), "Dec 31, 2020")

    def test_date_format_fr(self):
        lang.switch_lang("french")

        self.assertEqual(date_format(DATE, "%a"), "Jeu")
        self.assertEqual(date_format(DATE, "%A"), "Jeudi")
        self.assertEqual(date_format(DATE, "%b"), "Déc")
        self.assertEqual(date_format(DATE, "%B"), "Décembre")

        date_fmt = web.ctx.i18n.formats.get("DATE_FORMAT", "%x")

        self.assertEqual(date_format(DATE, date_fmt), "31 Décembre 2020")
