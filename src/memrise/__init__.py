from settings import MEMRISE_BACKEND
from utils.module_loading import import_string

from . import backends


# memrise.backends.dummy.DummyMemrise
def load_memrise():
    klass = import_string(MEMRISE_BACKEND)
    return klass()


memrise = load_memrise()
