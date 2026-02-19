import web


class SessionExpired(web.Unauthorized):
    pass