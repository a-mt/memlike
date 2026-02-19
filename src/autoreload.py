# ruff: noqa
# Based on https://github.com/ipython/ipython/blob/main/IPython/extensions/autoreload.py

# -----------------------------------------------------------------------------
#  Copyright (C) 2000 Thomas Heller
#  Copyright (C) 2008 Pauli Virtanen <pav@iki.fi>
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# -----------------------------------------------------------------------------
#
# This IPython module is written by Pauli Virtanen, based on the autoreload
# code by Thomas Heller.

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import os
import sys
import traceback
import types
import weakref
import gc
import logging
from importlib import import_module, reload
from importlib.util import source_from_cache

# ------------------------------------------------------------------------------
# Autoreload functionality
# ------------------------------------------------------------------------------


class ModuleReloader:
    enabled = False
    """Whether this reloader is enabled"""

    check_all = True
    """Autoreload all modules, not just those listed in 'modules'"""

    autoload_obj = False
    """Autoreload all modules AND autoload all new objects"""

    def __init__(self):
        # Modules that failed to reload: {module: mtime-on-failed-reload, ...}
        self.failed = {}
        # Modules specially marked as autoreloadable.
        self.modules = {}
        # Modules specially marked as not autoreloadable.
        self.skip_modules = {}
        # (module-name, name) -> weakref, for replacing old code objects
        self.old_objects = {}
        # Module modification timestamps
        self.modules_mtimes = {}

        # Reporting callable for verbosity
        self._report = lambda msg: None  # by default, be quiet.

        # Persistent import tracker for from-imports
        self.import_from_tracker = ImportFromTracker({}, {})

        # Cache module modification times
        self.check(check_all=True, do_reload=False)

        # To hide autoreload errors
        self.hide_errors = False

    def mark_module_skipped(self, module_name):
        """Skip reloading the named module in the future"""
        try:
            del self.modules[module_name]
        except KeyError:
            pass
        self.skip_modules[module_name] = True

    def mark_module_reloadable(self, module_name):
        """Reload the named module in the future (if it is imported)"""
        try:
            del self.skip_modules[module_name]
        except KeyError:
            pass
        self.modules[module_name] = True

    def clear_import_tracker(self):
        """Clear the persistent import tracker state"""
        self.import_from_tracker = ImportFromTracker({}, {})

    def aimport_module(self, module_name):
        """Import a module, and mark it reloadable

        Returns
        -------
        top_module : module
            The imported module if it is top-level, or the top-level
        top_name : module
            Name of top_module

        """
        self.mark_module_reloadable(module_name)

        import_module(module_name)
        top_name = module_name.split(".")[0]
        top_module = sys.modules[top_name]
        return top_module, top_name

    def filename_and_mtime(self, module):
        if not hasattr(module, "__file__") or module.__file__ is None:
            return None, None

        if getattr(module, "__name__", None) in [None, "__mp_main__", "__main__"]:
            # we cannot reload(__main__) or reload(__mp_main__)
            return None, None

        filename = module.__file__
        path, ext = os.path.splitext(filename)

        if ext.lower() == ".py":
            py_filename = filename
        else:
            try:
                py_filename = source_from_cache(filename)
            except ValueError:
                return None, None

        try:
            pymtime = os.stat(py_filename).st_mtime
        except OSError:
            return None, None

        return py_filename, pymtime

    def check(self, check_all=False, do_reload=True, execution_info=None):
        """Check whether some modules need to be reloaded."""

        if not self.enabled and not check_all:
            return

        if check_all or self.check_all:
            modules = list(sys.modules.keys())
        else:
            modules = list(self.modules.keys())

        # Use the persistent import_from_tracker
        import_from_tracker = (
            self.import_from_tracker if self.import_from_tracker.imports_froms else None
        )
        for modname in modules:
            m = sys.modules.get(modname, None)

            if modname in self.skip_modules:
                continue

            py_filename, pymtime = self.filename_and_mtime(m)
            if py_filename is None:
                continue

            try:
                if pymtime <= self.modules_mtimes[modname]:
                    continue
            except KeyError:
                self.modules_mtimes[modname] = pymtime
                continue
            else:
                if self.failed.get(py_filename, None) == pymtime:
                    continue

            self.modules_mtimes[modname] = pymtime

            # If we've reached this point, we should try to reload the module
            if do_reload:
                self._report(f"Reloading '{modname}'.")
                try:
                    if self.autoload_obj:
                        superreload(
                            m,
                            reload,
                            self.old_objects,
                            import_from_tracker=import_from_tracker,
                        )
                    else:
                        superreload(m, reload, self.old_objects)
                    if py_filename in self.failed:
                        del self.failed[py_filename]
                except:
                    if not self.hide_errors:
                        logger = logging.getLogger("autoreload")
                        logger.exception(
                            f"Failed to reload module '{modname}' from file '{py_filename}'"
                        )
                        print(
                            "[autoreload of {} failed: {}]".format(
                                modname, traceback.format_exc(10)
                            ),
                            file=sys.stderr,
                        )
                    self.failed[py_filename] = pymtime


# ------------------------------------------------------------------------------
# superreload
# ------------------------------------------------------------------------------


func_attrs = [
    "__code__",
    "__defaults__",
    "__doc__",
    "__closure__",
    "__globals__",
    "__dict__",
]


def update_function(old, new):
    """Upgrade the code object of a function"""
    for name in func_attrs:
        try:
            setattr(old, name, getattr(new, name))
        except (AttributeError, TypeError):
            pass


def update_instances(old, new):
    """Use garbage collector to find all instances that refer to the old
    class definition and update their __class__ to point to the new class
    definition"""

    refs = gc.get_referrers(old)

    for ref in refs:
        if type(ref) is old:
            object.__setattr__(ref, "__class__", new)


def update_class(old, new):
    """Replace stuff in the __dict__ of a class, and upgrade
    method code objects, and add new methods, if any"""
    for key in list(old.__dict__.keys()):
        old_obj = getattr(old, key)
        try:
            new_obj = getattr(new, key)
            # explicitly checking that comparison returns True to handle
            # cases where `==` doesn't return a boolean.
            if (old_obj == new_obj) is True:
                continue
        except AttributeError:
            # obsolete attribute: remove it
            try:
                delattr(old, key)
            except (AttributeError, TypeError):
                pass
            continue
        except ValueError:
            # can't compare nested structures containing
            # numpy arrays using `==`
            pass

        if update_generic(old_obj, new_obj):
            continue

        try:
            setattr(old, key, getattr(new, key))
        except (AttributeError, TypeError):
            pass  # skip non-writable attributes

    for key in list(new.__dict__.keys()):
        if key not in list(old.__dict__.keys()):
            try:
                setattr(old, key, getattr(new, key))
            except (AttributeError, TypeError):
                pass  # skip non-writable attributes

    # update all instances of class
    update_instances(old, new)


def update_property(old, new):
    """Replace get/set/del functions of a property"""
    update_generic(old.fdel, new.fdel)
    update_generic(old.fget, new.fget)
    update_generic(old.fset, new.fset)


def isinstance2(a, b, typ):
    return isinstance(a, typ) and isinstance(b, typ)


UPDATE_RULES = [
    (lambda a, b: isinstance2(a, b, type), update_class),
    (lambda a, b: isinstance2(a, b, types.FunctionType), update_function),
    (lambda a, b: isinstance2(a, b, property), update_property),
]
UPDATE_RULES.extend(
    [
        (
            lambda a, b: isinstance2(a, b, types.MethodType),
            lambda a, b: update_function(a.__func__, b.__func__),
        ),
    ]
)


def update_generic(a, b):
    for type_check, update in UPDATE_RULES:
        if type_check(a, b):
            update(a, b)
            return True
    return False


class StrongRef:
    def __init__(self, obj):
        self.obj = obj

    def __call__(self):
        return self.obj


mod_attrs = [
    "__name__",
    "__doc__",
    "__package__",
    "__loader__",
    "__spec__",
    "__file__",
    "__cached__",
    "__builtins__",
]


class ImportFromTracker:
    def __init__(self, imports_froms: dict, symbol_map: dict):
        self.imports_froms = imports_froms
        # symbol_map maps original_name -> list of resolved_names
        self.symbol_map = {}
        if symbol_map:
            for module_name, mappings in symbol_map.items():
                self.symbol_map[module_name] = {}
                for original_name, resolved_names in mappings.items():
                    if isinstance(resolved_names, list):
                        self.symbol_map[module_name][original_name] = resolved_names[:]
                    else:
                        self.symbol_map[module_name][original_name] = [resolved_names]
        else:
            self.symbol_map = symbol_map or {}

    def add_import(
        self, module_name: str, original_name: str, resolved_name: str
    ) -> None:
        """Add an import, handling conflicts with existing imports.

        This method is called after successful code execution, so we know the import is valid.
        """
        if module_name not in self.imports_froms:
            self.imports_froms[module_name] = []
        if module_name not in self.symbol_map:
            self.symbol_map[module_name] = {}

        # Check if there's already a different mapping for the same resolved_name from a different original_name
        # We need to remove any conflicting mappings
        for orig_name, res_names in list(self.symbol_map[module_name].items()):
            if resolved_name in res_names and orig_name != original_name:
                # Remove the conflicting resolved_name from the other original_name's list
                res_names.remove(resolved_name)
                if (
                    not res_names
                ):  # If the list is now empty, remove the original_name entirely
                    if orig_name in self.imports_froms[module_name]:
                        self.imports_froms[module_name].remove(orig_name)
                    del self.symbol_map[module_name][orig_name]

        # Add the new mapping
        if original_name not in self.imports_froms[module_name]:
            self.imports_froms[module_name].append(original_name)

        if original_name not in self.symbol_map[module_name]:
            self.symbol_map[module_name][original_name] = []

        # Add the resolved_name if it's not already in the list
        if resolved_name not in self.symbol_map[module_name][original_name]:
            self.symbol_map[module_name][original_name].append(resolved_name)


def append_obj(module, d, name, obj, autoload=False):
    in_module = hasattr(obj, "__module__") and obj.__module__ == module.__name__
    if autoload:
        # check needed for module global built-ins
        if not in_module and name in mod_attrs:
            return False
    else:
        if not in_module:
            return False

    key = (module.__name__, name)
    try:
        d.setdefault(key, []).append(weakref.ref(obj))
    except TypeError:
        pass
    return True


def superreload(
    module, reload=reload, old_objects=None, import_from_tracker=None
):
    """Enhanced version of the builtin reload function.

    superreload remembers objects previously in the module, and

    - upgrades the class dictionary of every old class in the module
    - upgrades the code object of every old function and method
    - clears the module's namespace before reloading

    """
    if old_objects is None:
        old_objects = {}

    # collect old objects in the module
    for name, obj in list(module.__dict__.items()):
        if not append_obj(module, old_objects, name, obj):
            continue
        key = (module.__name__, name)
        try:
            old_objects.setdefault(key, []).append(weakref.ref(obj))
        except TypeError:
            pass

    # reload module
    try:
        # clear namespace first from old cruft
        old_dict = module.__dict__.copy()
        old_name = module.__name__
        module.__dict__.clear()
        module.__dict__["__name__"] = old_name
        module.__dict__["__loader__"] = old_dict["__loader__"]
    except (TypeError, AttributeError, KeyError):
        pass

    try:
        module = reload(module)
    except:
        # restore module dictionary on failed reload
        module.__dict__.update(old_dict)
        raise

    for name, new_obj in list(module.__dict__.items()):
        key = (module.__name__, name)
        if key not in old_objects:
            continue

        new_refs = []
        for old_ref in old_objects[key]:
            old_obj = old_ref()
            if old_obj is None:
                continue
            new_refs.append(old_ref)
            update_generic(old_obj, new_obj)

        if new_refs:
            old_objects[key] = new_refs
        else:
            del old_objects[key]

    return module


# ------------------------------------------------------------------------------
# IPython connectivity
# ------------------------------------------------------------------------------


class AutoreloadMagics:
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._reloader = ModuleReloader()
        self._reloader.check_all = False
        self._reloader.autoload_obj = False
        self.loaded_modules = set(sys.modules)

    def autoreload(self, **kwargs):
        kwargs.setdefault("mode", "now")
        kwargs.setdefault("print", False)
        kwargs.setdefault("log", False)
        kwargs.setdefault("hide_errors", False)
        kwargs.setdefault("full", False)

        mode = kwargs["mode"].lower()
        p = print

        logger = logging.getLogger("autoreload")

        l = logger.debug

        def pl(msg):
            p(msg)
            l(msg)

        if kwargs["print"] is False and kwargs["log"] is False:
            self._reloader._report = lambda msg: None
        elif kwargs["print"] is True:
            if kwargs["log"] is True:
                self._reloader._report = pl
            else:
                self._reloader._report = p
        elif kwargs["log"] is True:
            self._reloader._report = l

        self._reloader.hide_errors = kwargs["hide_errors"]

        if mode == "" or mode == "now":
            self._reloader.check(True)
        elif mode == "0" or mode == "off":
            self._reloader.enabled = False
        elif mode == "1" or mode == "explicit":
            self._reloader.enabled = True
            self._reloader.check_all = False
            self._reloader.autoload_obj = False
        elif mode == "2" or mode == "all":
            self._reloader.enabled = True
            self._reloader.check_all = True
            self._reloader.autoload_obj = False
        elif mode == "3" or mode == "complete":
            self._reloader.enabled = True
            self._reloader.check_all = True
            self._reloader.autoload_obj = True
        else:
            raise ValueError(f'Unrecognized autoreload mode "{mode}".')

    def aimport(self, parameter_s="", stream=None):
        """%aimport => Import modules for automatic reloading.

        %aimport
        List modules to automatically import and not to import.

        %aimport foo
        Import module 'foo' and mark it to be autoreloaded for %autoreload explicit

        %aimport foo, bar
        Import modules 'foo', 'bar' and mark them to be autoreloaded for %autoreload explicit

        %aimport -foo, bar
        Mark module 'foo' to not be autoreloaded for %autoreload explicit, all, or complete, and 'bar'
        to be autoreloaded for mode explicit.
        """
        modname = parameter_s
        if not modname:
            to_reload = sorted(self._reloader.modules.keys())
            to_skip = sorted(self._reloader.skip_modules.keys())
            if stream is None:
                stream = sys.stdout
            if self._reloader.check_all:
                stream.write("Modules to reload:\nall-except-skipped\n")
            else:
                stream.write("Modules to reload:\n%s\n" % " ".join(to_reload))
            stream.write("\nModules to skip:\n%s\n" % " ".join(to_skip))
        else:
            for _module in [_.strip() for _ in modname.split(",")]:
                if _module.startswith("-"):
                    _module = _module[1:].strip()
                    self._reloader.mark_module_skipped(_module)
                else:
                    top_module, top_name = self._reloader.aimport_module(_module)

    def pre_execute_hook(self):
        if self._reloader.enabled:
            self._reloader._report("Check")
            try:
                self._reloader.check()
            except:
                pass

    def post_execute_hook(self):
        """Cache the modification times of any modules imported in this execution and track imports"""

        newly_loaded_modules = set(sys.modules) - self.loaded_modules
        for modname in newly_loaded_modules:
            _, pymtime = self._reloader.filename_and_mtime(sys.modules[modname])
            if pymtime is not None:
                self._reloader.modules_mtimes[modname] = pymtime

        self.loaded_modules.update(newly_loaded_modules)
