import inspect
import re
import web


def beautify_pattern(pattern, fn):
    # Retrieve the function's signature
    # example: "(self, course_id, course_slug, level_index)"
    args = str(inspect.signature(fn))[1:-1].split(", ")

    i = 0

    # From the pattern, replace the regex groups with argname
    # example: /(\d+)/ -> /{course_id}/
    def replace_args(match):
        nonlocal i
        i += 1

        argname = args[i] if i <= len(args) else match[0][1:-1]
        return "{" + argname + "}"

    return re.sub(r"\([^)]+\)", replace_args, pattern)


def autodetect_urls(app, prefix="", res={}):
    # For each route in the app mapping
    for i, (pattern, handler) in enumerate(app.mapping):
        f = None

        if isinstance(handler, web.application):
            autodetect_urls(handler, prefix + pattern, res)

        # The associated handler is a string:
        # retrieve the class from the app's local context (fvars)
        elif isinstance(handler, str):
            if handler not in app.fvars:
                continue

            f = app.fvars[handler]
            if not inspect.isclass(f):
                continue

        # The associated handler is a class:
        # display its name in the entries
        elif inspect.isclass(handler):
            f = handler
            handler = handler.__name__

        else:
            print("Unhandled handler", handler, "for route", pattern)

        if f:
            if handler in res:
                continue

            if "GET" in f.__dict__:
                res[handler] = "GET " + beautify_pattern(prefix + pattern, f.__dict__["GET"])

            elif "POST" in f.__dict__:
                res[handler] = "POST " + beautify_pattern(prefix + pattern, f.__dict__["POST"])

    return res
