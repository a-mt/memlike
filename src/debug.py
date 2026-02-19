from inspect import isclass
from functools import wraps
import web
import logging


logger = logging.getLogger(__name__)
logger_proxy = logger.getChild(suffix="route")


def debug_route(origin, pattern, fn):
    if getattr(fn, "proxied", False):
        return fn

    origin += "." + fn.__name__

    @wraps(fn)
    def wrapper(*args, **kwargs):
        logger_proxy.debug(f"{origin} [pattern={pattern},path={web.ctx.path}]")

        return fn(*args, **kwargs)

    setattr(wrapper, "proxied", True)
    return wrapper


def init_debug_route(app):
    """
    Print the method that was called
    for each classes served by our app
    """
    for i, (pattern, handler) in enumerate(app.mapping):
        if isinstance(handler, web.application):
            if handler.fvars.get("print_info", False):
                continue

            handler.fvars["print_info"] = True
            init_debug_route(handler)

        elif isinstance(handler, str) and handler in app.fvars:
            f = app.fvars[handler]

            if isclass(f) and "GET" in f.__dict__:
                fn = f.__dict__["GET"]
                new_fn = debug_route(f"{f.__module__}.{f.__name__}", pattern, fn)

                setattr(f, "GET", new_fn)
