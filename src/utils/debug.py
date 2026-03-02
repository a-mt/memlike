import inspect
import re
import web


def beautify_pattern(pattern, fn):
    # Retrieve the list of arguments (ie "(self, idCourse, slug, lvl)")
    args = str(inspect.signature(fn))[1:-1].split(", ")

    i = 0

    def replace_args(match):
        nonlocal i
        i += 1

        argname = args[i] if i <= len(args) else match[0][1:-1]
        return "{" + argname + "}"

    return re.sub(r"\([^)]+\)", replace_args, pattern)


def autodetect_urls(app, prefix="", res={}):
    for i, (pattern, handler) in enumerate(app.mapping):
        if isinstance(handler, web.application):
            autodetect_urls(handler, prefix + pattern, res)

        elif isinstance(handler, str):
            if handler in res:
                continue

            if handler not in app.fvars:
                continue

            f = app.fvars[handler]
            if not inspect.isclass(f):
                continue

            if "GET" in f.__dict__:
                res[handler] = "GET " + beautify_pattern(prefix + pattern, f.__dict__["GET"])

            elif "POST" in f.__dict__:
                res[handler] = "POST " + beautify_pattern(prefix + pattern, f.__dict__["POST"])

    return res
