from os.path import isfile
from settings import DEFAULT_LANG, ROOTDIR
from utils.module_loading import load_source
import web
import logging


logger = logging.getLogger(__name__)


class Lang(object):
    """
    Translations management for web.py
    """
    def __init__(self, app=None):
        self.locales = {}

        if app:
            app.add_processor(self._processor)

    def get_locale_path(self, lang):
        """
        Get the location of the file
        containing the translation strings for the given language
        """
        return ROOTDIR + '/locales/' + lang + '.py'

    def get_module(self, lang=None, retry=True):
        if lang is None:
            lang = DEFAULT_LANG

        if not lang in self.locales:
            logger.debug(f'Loading lang={lang}')

            path = self.get_locale_path(lang)
            if isfile(path):
                self.locales[lang] = load_source(lang, path)

            # Session.lang contains a language that doesn't have
            # an associated file in locales/ (not supposed to happen)
            else:
                if retry:
                    logger.warning(f'lang={lang} does not exist')
                    return self.get_module(retry=False)

                raise Exception(f'Could not load lang={lang}')

        return self.locales[lang]

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
        lang = web.ctx.session.get('lang', DEFAULT_LANG)
        mod = self.get_module(lang=lang)
        web.ctx.lang = mod

        # Make it accessible in templates
        web.config.template['LANG'] = mod
