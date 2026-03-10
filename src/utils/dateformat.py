import datetime
import re
import web
from settings import lang


re_formatchars = re.compile(r"(?<!\\)%([aAbB])")


class Formatter:
    def format(self, formatstr):
        pieces = []
        for i, piece in enumerate(re_formatchars.split(str(formatstr))):
            if i % 2:
                pieces.append(str(getattr(self, piece[-1])()))
            elif piece:
                pieces.append(piece)
        return "".join(pieces)


class DateFormat(Formatter):
    def __init__(self, obj):
        self.data = obj
        self.i18n = web.ctx.get("i18n", None) or lang.switch_lang()

    def B(self):
        "Month, textual, long; e.g. 'January'"
        return self.i18n.MONTHS[self.data.month - 1]

    def b(self):
        "Month, textual, 3 letters; e.g. 'Jan'"
        return self.i18n.MONTHS_ABBR[self.data.month - 1]

    def A(self):
        "Day of the week, textual, long; e.g. 'Friday'"
        return self.i18n.WEEKDAYS[self.data.weekday()]

    def a(self):
        "Day of the week, 3 letters; e.g. 'Fri'"
        return self.i18n.WEEKDAYS_ABBR[self.data.weekday()]


def date_format(value, format_string):
    """
    Date formatter
    Use date_format(dt, "%d %a %Y") instead of dt.strftime("%d %a %Y")
    to retrieve the week name (monday..sunday) and month name (jan..dec)
    localized with our i18n module

    :param Date|DateTime value
    :param string format_string - strftime compatible string
    """
    i18n_format_string = DateFormat(value).format(format_string)

    return value.strftime(i18n_format_string)


class Parser:
    def __init__(self, obj):
        self.data = obj
        self.i18n = web.ctx.get("i18n", None) or lang.switch_lang()

    def __get_regex_repl(self, mapping):
        def repl(match):
            k = list(mapping.values()).index(match[0])
            return list(mapping.keys())[k]

        return "|".join(mapping.values()), repl

    def B(self):
        "Month, textual, long; e.g. 'January'"
        return self.__get_regex_repl(self.i18n.months)

    def b(self):
        "Month, textual, 3 letters; e.g. 'Jan'"
        return self.__get_regex_repl(self.i18n.months_abbr)

    def A(self):  # NOQA: E743, E741
        "Day of the week, textual, long; e.g. 'Friday'"
        return self.__get_regex_repl(self.i18n.weekdays)

    def a(self):  # NOQA: E743, E741
        "Day of the week, 3 letters; e.g. 'Fri'"
        return self.__get_regex_repl(self.i18n.weekdays_abbr)

    def parse(self, format_string):
        value = self.data

        for directive in re_formatchars.findall(str(format_string)):
            regex, repl = getattr(self, directive)()
            value = re.sub(regex, repl, value)

        return datetime.datetime.strptime(value, format_string)


def date_parse(value, format_string):
    """
    Date parser

    Use date_parse(str, "%d %a %Y") instead of datetime.strptime(str, "%d %a %Y")
    to use our i18n module
    """
    return Parser(value).parse(format_string)
