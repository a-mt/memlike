import imp

class Lang(object):
    """Translations management for web.py
    """
    def __init__(self, app, session):
        self.session = session
        self._data = {}
        self.__getitem__ = self._data.__getitem__

        if app:
            app.add_processor(self._processor)

    def __contains__(self, name):
        return name in self._data

    def __getattr__(self, name):
        return getattr(self._data[self.session['lang']], name)

    def _processor(self, handler):
        self._load()
        return handler()

    def _load(self):
        lang = self.session['lang']
        if not lang in self._data:
            self._data[lang] = imp.load_source(lang, 'src/locales/' + lang + '.py')