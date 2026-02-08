import importlib
from os.path import isfile


class Lang(object):
    """Translations management for web.py
    """
    DEFAULT_LANG = 'english'

    def __init__(self, app, session, pwd):
        self.session = session
        self.pwd     = pwd
        self._data   = {}
        self.__getitem__ = self._data.__getitem__

        if app:
            app.add_processor(self._processor)

    def __contains__(self, name):
        return name in self._data

    def __getattr__(self, name):
        return getattr(self._data[self.lang], name)

    @property
    def lang(self):
        """
        Retrieve the language associated to the current session (saved to database)
        """
        return self.session.get('lang', self.DEFAULT_LANG)

    def _processor(self, handler):
        """
        Called by app before processing any request
        """
        self._load()
        return handler()

    def get_locale_path(self, lang):
        """
        Get the location of the file
        containing the translation strings for the given language
        """
        return self.pwd + '/locales/' + lang + '.py'

    def load_source(self, modname, filename):
        """
        Replaces imp.load_source with importlib logic
        """
        loader = importlib.machinery.SourceFileLoader(modname, filename)
        spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return module

    def _load(self, retry=True):
        """
        Puts the translation string of the current language into self._data
        """
        lang = self.lang

        if not lang in self._data:
            path = self.get_locale_path(lang)

            if isfile(path):
                self._data[lang] = self.load_source(lang, path)

            # Not supposed to happen
            # But the requested language doesn't have an associated file in locales/
            elif retry:
                self.session.lang = self.DEFAULT_LANG
                self._load(retry=False)
