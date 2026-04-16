from os.path import isfile
from pathlib import Path
from settings import DEFAULT_LANG_SLUG, ROOTDIR
from utils.module_loading import load_source
from unidecode import unidecode

import locales  # noqa F401
import web
import logging
import variables


logger = logging.getLogger(__name__)


def get_localized_languages(I18N=None):
    if I18N is None:
        I18N = web.ctx.get("i18n", None) or web.config.lang.switch_lang()

    res = []
    for slug in variables.source_languages:
        category = variables.categories_slug.get(slug, None)
        if category is None:
            continue

        item = category
        item["localized_name"] = I18N.languages.get(slug, slug)

        res.append((slug, item))

    return dict(sorted(res, key=lambda x: unidecode(x[1]["localized_name"])))


class Lang(object):
    """
    Translations management for web.py
    """

    def __init__(self, app=None):
        self.locales = {}

        if app:
            app.add_processor(self._processor)

    def get_locales(self):
        return [item.stem for item in Path(f"{ROOTDIR}/locales").glob("*.py") if item.stem[0] != "_"]

    def get_locale_path(self, lang_slug):
        """
        Get the location of the file
        containing the translation strings for the given language
        """
        return ROOTDIR + "/locales/" + lang_slug + ".py"

    def get_module(self, lang_slug=None, retry=True):
        """
        :param string lang_slug - engish | french
        :param boolean retry
        """
        if lang_slug is None:
            lang_slug = DEFAULT_LANG_SLUG

        if lang_slug not in self.locales:
            logger.debug(f"Loading lang_slug={lang_slug}")

            path = self.get_locale_path(lang_slug)
            if isfile(path):
                self.locales[lang_slug] = load_source(lang_slug, path)

            # Session.lang_slug contains a language that doesn't have
            # an associated file in locales/ (not supposed to happen)
            else:
                if retry:
                    logger.warning(f"lang_slug={lang_slug} does not exist")
                    return self.get_module(retry=False)

                raise Exception(f"Could not load lang_slug={lang_slug}")

        return self.locales[lang_slug]

    def _processor(self, handler):
        """
        Called by app before processing any request
        """
        self._load()
        return handler()

    def _load(self):
        """
        Puts the translation string of the current language into self._data
        """
        self.switch_lang()

    def switch_lang(self, lang_slug=None):
        if lang_slug is None:
            if web.ctx.get("session", None):
                lang_slug = web.ctx.session.get("lang_slug", None)

            lang_slug = lang_slug or DEFAULT_LANG_SLUG

        mod = self.get_module(lang_slug=lang_slug)
        lang_code = lang_slug[:2]

        web.ctx.i18n = mod
        web.ctx.lang_code = lang_code

        # Make it accessible in templates
        web.config.template["I18N"] = mod
        web.config.template["LANG"] = lang_code
        return mod

    def get_localized_languages(self, I18N=None):
        return get_localized_languages(I18N)
