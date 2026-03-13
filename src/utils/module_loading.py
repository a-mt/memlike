import importlib
import sys


def cached_import(module_path, class_name):
    # Check whether module is loaded and fully initialized.
    module = sys.modules.get(module_path)
    if module:
        spec = getattr(module, "__spec__", None)
        if spec and getattr(spec, "_initializing", False):
            module = importlib.import_module(module_path)

    return getattr(module, class_name)


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by
    the last name in the path. Raise ImportError if the import failed.

    Example: umport_string("memrise.backends.CachedApiMemrise")
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    try:
        return cached_import(module_path, class_name)
    except AttributeError as err:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (module_path, class_name)) from err


def load_source(modname, filename):
    """
    Replaces imp.load_source with importlib logic

    Exemple: load_source("french", "/srv/locales/french.py")
    to import french.py as the module "french"
    """
    loader = importlib.machinery.SourceFileLoader(modname, filename)
    spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module
