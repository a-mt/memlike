import imp

class Lang(object):
    """Translations management for web.py
    """
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
        return self.session.get('lang', 'english')

    def _processor(self, handler):
        self._load()
        return handler()

    def _load(self):
        lang = self.lang
        if not lang in self._data:
            self._data[lang] = imp.load_source(lang, self.pwd + '/locales/' + lang + '.py')
