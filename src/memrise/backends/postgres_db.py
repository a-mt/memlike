import requests
import logging
import settings
import web

from memrise.scrapers import Scraper
from memrise.requestors import ApiRequestor, DummyApiRequestor
from pydantic_core import ValidationError
from utils.crypto import gen_csrftoken
from .dummy import DummyLoginMixin, DummyEditMixin
from .base import Memrise


logger = logging.getLogger(__name__)


class PostgresDB(Memrise):

    # +-----------------------------------------------------
    # | AUTH
    # +-----------------------------------------------------
    def login(self, username, password):
        """
        Authenticate with the given username and password

        @param string username
        @param string password
        @return dict - {username, sessionid, csrftoken}
        """

        # Check if the user exists
        store = web.database()

        # with x as (select username, salt, password from users where username = 'bob') select username from x where crypt('pass', salt) = password;
        qout = web.db.SQLQuery([
            "WITH x AS (SELECT id, username, salt, password FROM users WHERE username = ", web.db.SQLParam(username), ")",
            "SELECT id, username FROM x WHERE crypt(", web.db.SQLParam(password), ", salt) = password"
        ])

        res  = store.query(qout, processed=True).first()
        if res is None:
            return None

        # Create a new CSRF token
        csrftoken = gen_csrftoken(web.ctx.get("ip", "0.0.0.0"), web.config.session_parameters.secret_key)
        res["csrftoken"] = csrftoken
        res["sessionid"] = res["id"]

        return dict(res)

    # +-----------------------------------------------------
    # | CURRENT USER
    # +-----------------------------------------------------
    def whoami(self, **kwargs):
        self.set_default_kwargs(kwargs)

        store = web.database()
        res = store.select(what="id AS sessionid, username, photo", tables="users", where={
            "id": kwargs["sessionid"],
        }).first()

        if not res.get("photo", ""):
            res["photo"] = "/static/img/empty-avatar-1.png"

        return dict(res) if res else None
