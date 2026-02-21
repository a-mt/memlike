from inspect import isclass
from functools import wraps
import web
import logging
import os


logger = logging.getLogger(__name__)
logger_proxy = logger.getChild(suffix="route")
logger_tpl = logger.getChild(suffix="template")


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


def debug_template(template_config, key, decorate_fn="_load_template"):
    """
    Print whenever the load_template of the Render instance is called
    """
    instance = template_config[key]
    logger_render = logger_tpl.getChild(suffix=key)

    fn = getattr(instance, decorate_fn)
    if getattr(fn, "proxied", False):
        return

    @wraps(fn)
    def wrapper(name):
        logger_render.debug(f"Load template '{name}'")

        try:
            return fn(name)
        except Exception as e:
            logger_render.error(f"Failed to load template '{name}'", exc_info=e)

            raise web.internalerror()

    setattr(wrapper, "proxied", True)
    setattr(instance, decorate_fn, wrapper)


def init_debug_template(template_config):
    if template_config.get("debug_template", None) is not None:
        return

    template_config["debug_template"] = True
    debug_template(template_config, "render")
    debug_template(template_config, "prender")


def get_template(name, path):
    logger_tpl.debug(f"Get template '{name}'")

    # Retrieve the html
    text = ""
    with open(path, encoding="utf-8") as tmpl_file:
        try:
            text = tmpl_file.read()
        except Exception as e:
            logger_tpl.error(f"Couldnt open template '{name}'", exc_info=e)
            return

    # Try parsing it
    try:
        return web.template.Template(text, filename=path)
    except Exception as e:
        logger_tpl.error(f"Could not create template '{name}'", exc_info=e)


def decorate_parser():
    """
    Add a try/except around the Parser.read_suite method
    to be able to debug
    """
    from web.template import Parser, SuiteNode
    fn = Parser.__dict__['read_suite']

    def new_fn(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger_tpl.error("Couldnt parse template: %(args)s" % {"args": args}, exc_info=e)
            return SuiteNode([])

    setattr(Parser, "read_suite", new_fn)


def override_djangoerror_r():
    from djangoerror import get_djangoerror_template
    import web.debugerror

    try:
        djangoerror_r = get_djangoerror_template()

        # from web.debugerror import djangoerror_r
        web.debugerror.__globals__["djangoerror_r"] = djangoerror_r

    except Exception as e:
        logger_tpl.error(f"Could not create djangoerror", exc_info=e)


def check_load_templates(root):
    decorate_parser()
    override_djangoerror_r()

    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)

            if not filepath.endswith(".html"):
                continue

            get_template(filename, filepath)
