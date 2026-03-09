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

    def A(self):  # NOQA: E743, E741
        "Day of the week, textual, long; e.g. 'Friday'"
        return self.i18n.WEEKDAYS[self.data.weekday()]

    def a(self):  # NOQA: E743, E741
        "Day of the week, 3 letters; e.g. 'Fri'"
        return self.i18n.WEEKDAYS_ABBR[self.data.weekday()]


def date_format(value, format_string):
    """
    Use date_format(dt, "%d %a %Y") instead of dt.strftime("%d %a %Y")
    to retrieve the week name (monday..sunday) and month name (jan..dec)
    localized with our i18n module

    :param Date|DateTime value
    :param string format_string - strftime compatible string
    """
    i18n_format_string = DateFormat(value).format(format_string)

    return value.strftime(i18n_format_string)
