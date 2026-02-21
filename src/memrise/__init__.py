from settings import MEMRISE_BACKEND
from utils.module_loading import import_string
from . import backends  # noqa F401


def load_memrise(backend=None):
    klass = import_string(backend or MEMRISE_BACKEND)
    return klass()


# Load a backend with the default settings
memrise = load_memrise()
