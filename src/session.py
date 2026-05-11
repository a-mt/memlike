import base64
import datetime
import logging
import web
from copy import deepcopy
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from functools import partial
from http.cookies import Morsel
from urllib.parse import quote
try:
    import cPickle as pickle
except ImportError:
    import pickle

# Just re-exporting web.session(__all__), with some overwrites
# ruff: noqa F401
from web.session import (
    Session,
    SessionExpired,
    Store,
    DiskStore,
    DBStore,
    MemoryStore,
)
from exceptions import SessionExpired


logger = logging.getLogger(__name__)


class DiskStore(DiskStore):
    def __contains__(self, key):
        logger.debug("DiskStore:Has %s", key)
        return super().__contains__(key)

    def __getitem__(self, key):
        logger.debug("DiskStore:Get %s", key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        logger.debug("DiskStore:Set %s=%s", key, value)
        return super().__setitem__(key, value)


class DBStore(DBStore):
    def __contains__(self, key):
        logger.debug("DBStore:Has %s", key)
        return super().__contains__(key)

    def __getitem__(self, key):
        logger.debug("DBStore:Get %s", key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        logger.debug("DBStore:Set %s=%s", key, value)
        # Remove the leading `b` of bytes object (`b"..."`), otherwise encoded
        # value is invalid base64 format.
        pickled = self.encode(value).decode()

        now = datetime.datetime.now()
        try:
            self.db.update(
                self.table,
                where="session_id=$key",
                data=pickled,
                atime=now,
                vars=locals(),
            )
        except IndexError:
            self.db.insert(self.table, False, session_id=key, atime=now, data=pickled)


# AES CBC mode is used for encryption
def encrypt(plain_data, key):
    if not isinstance(plain_data, bytes):
        plain_data = plain_data.encode("UTF-8", "ignore")

    encryption_suite = AES.new(key, AES.MODE_CBC)
    padded_data = pad(plain_data, AES.block_size)
    cipher_data = encryption_suite.encrypt(padded_data)

    cipher_b64data = base64.urlsafe_b64encode(encryption_suite.iv + cipher_data)
    return cipher_b64data

def decrypt(cipher_b64data, key):
    cipher_data = base64.urlsafe_b64decode(cipher_b64data)
    iv, cipher_data = cipher_data[:AES.block_size], cipher_data[AES.block_size:]

    encryption_suite = AES.new(key, AES.MODE_CBC, iv=iv)
    padded_data = encryption_suite.decrypt(cipher_data)
    plain_data = unpad(padded_data, AES.block_size)

    return plain_data  # as bytes


class CookieDataStore(Store):
    def __init__(self, cookie_name="session_data"):
        self.cookie_name = cookie_name
        self.last_allowed_time = None
        self._cached_data = {}

        self._config = web.storage(web.config.session_parameters)

        key = self._config.get("secret_key", "PASS")
        if len(key) < 32:
            k = len(key) % 32
            key = (key * k)[:32]

        self._encoding_key = key.encode()

    def encode(self, session_dict):
        """encodes session dict as a string"""
        session_data = pickle.dumps(session_dict)
        session_encoded = encrypt(session_data, self._encoding_key)
        session_stored = base64.urlsafe_b64encode(session_encoded)
        return session_stored

    def decode(self, session_stored):
        """decodes the data to get back the session dict"""
        if isinstance(session_stored, str):
            session_stored = session_stored.encode()

        session_encoded = base64.urlsafe_b64decode(session_stored)
        session_data = decrypt(session_encoded, self._encoding_key)
        session_dict = pickle.loads(session_data)
        return session_dict

    def getdata(self, sessionid):
        if sessionid not in self._cached_data:
            self._cached_data[sessionid] = self.readdata()

        return self._cached_data[sessionid]

    def readdata(self):
        try:
            pickled_data = web.cookies().get(self.cookie_name, "")
            if not pickled_data:
                return None

            data = self.decode(pickled_data)
            if type(data) is not dict:
                return None

            return data
        except Exception as e:
            logger.error(e)
            return None

    def __contains__(self, sessionid):
        data = self.getdata(sessionid)

        return data is not None and data.get("session_id", "") == sessionid

    @property
    def atime(self):
        return int(datetime.datetime.now().timestamp())

    def __getitem__(self, sessionid):
        logger.debug(f"Session get {sessionid}")
        try:
            now = self.atime
            data = self.getdata(sessionid)

            # Check if the cookie data is valid
            if data is None:
                raise IndexError

            if data.get("session_id", "") != sessionid:
                raise IndexError

            # check if timeout is reached: session hasn't been used for more than x seconds
            atime = data["atime"]
            if isinstance(atime, datetime.datetime):
                atime = int(atime.timestamp())

            if self.last_allowed_time is not None and atime < self.last_allowed_time:
                raise IndexError

            # refresh our session_data cookie every 10m if nothing otherwise changed
            if now - atime > 600:
                data["atime"] = now

        except IndexError:
            self._cached_data.pop(sessionid, None)
            raise KeyError(sessionid)
        else:
            return data

    def setcookie(self, value):
        morsel = Morsel()
        morsel.set(str(self.cookie_name), str(value), quote(value))

        morsel["expires"] = ""
        morsel["path"] = self._config.cookie_path or web.ctx.homepath + "/"

        if domain := self._config.cookie_domain:
            morsel["domain"] = domain

        if secure := self._config.secure:
            morsel["secure"] = secure

        if httponly := self._config.httponly:
            morsel["httponly"] = True

        cookie_value = morsel.OutputString()

        if (samesite :=  self._config.get("samesite", None)) and samesite.lower() in ("strict", "lax", "none"):
            cookie_value += "; SameSite=%s" % samesite

        return cookie_value

    def dict_are_equal(self, dict_a, dict_b):
        if type(dict_a) is not dict:
            return False

        if type(dict_b) is not dict:
            return False

        new_ref = {**dict_a}
        new_ref.update(dict_b)

        if len(new_ref.keys()) != len(dict_a.keys()):
            return False

        for k, v in new_ref.items():
            if new_ref[k] != dict_a[k]:
                return False

        return True

    def __setitem__(self, sessionid, data):
        are_equal = self.dict_are_equal(self._cached_data.get(sessionid, None), data)

        logger.debug(f"Session set {sessionid} ({are_equal})")

        # Nothing changed
        if are_equal or not data.get("loggedin", False):
            return

        def callback(self, sessionid, data):
            logger.debug(f"Session set.callback {sessionid}")

            if data and type(data) is dict:
                data["atime"] = self.atime
                data["session_id"] = sessionid
                encoded_value = self.encode(data)

                self._cached_data[sessionid] = data
            else:
                encoded_value = ""

                self._cached_data[sessionid] = None

            cookie_value = self.setcookie(encoded_value)
            return cookie_value

        # Will be used when the server calls for response.headers
        if web.ctx.get("session_cookie_data", None) is None:
            session_cookie_data = CookieDataValue("")

            """
            if not web.ctx.get("headers", None):
                web.ctx.headers = []

            if not isinstance(web.ctx.headers, HeadersList):
                web.ctx.headers = HeadersList(web.ctx.headers)

            web.ctx.headers.append(("Set-Cookie", session_cookie_data))
            """
            web.ctx.session_cookie_data = session_cookie_data
        else:
            session_cookie_data = web.ctx.session_cookie_data

        fct = partial(callback, self, sessionid, data)
        session_cookie_data.set_callback(fct)

    def __delitem__(self, sessionid):
        self._cached_data[sessionid] = None
        logger.debug("Session deleted")

    def cleanup(self, timeout):
        self.last_allowed_time = int(datetime.datetime.now().timestamp()) - timeout



class HeadersList(list):
    """
    When we loop through the headers (ie WSGI, unicorn, etc):
    cast each header values to strings
    """
    def __iter__(self):
        for k, v in super().__iter__():
            yield k, str(v)


class CookieDataValue(str):
    def set_callback(self, fct):
        self.callback = fct
        self.value = None

    def __str__(self):
        if self.value is None:
            fct = self.callback
            value = fct()

            self.value = str(value)

        return self.value


class Session(Session):
    __slots__ = Session.__slots__ + [
        "_killed",
    ]

    def _reset(self):
        self._data = web.utils.storage({})
        self._killed = False
        self.ip = web.ctx.ip

    def _generate_session_id(self):
        logger.debug("Generate session ID")

        return super()._generate_session_id()

    def _load(self):
        # Reset _data
        self._reset()

        # Retrieve session_id from cookie
        cookie_name = self._config.cookie_name
        self.session_id = web.cookies().get(cookie_name)

        # Retrieve session data from store
        if self.session_id:
            try:
                data = self.store[self.session_id]
                self._data.update(data)
            except KeyError:
                # session_id doesn't exist in store
                self.expired()

        # Ensure the session is associated to the same IP
        # (if check is enabled in configs)
        if self.session_id:
            self._validate_ip()

        # Recreate a new empty session
        if not self.session_id:
            self._reset()
            self.session_id = self._generate_session_id()

            if self._initializer:
                if isinstance(self._initializer, dict):
                    self._data.update(deepcopy(self._initializer))
                    self._data["session_id"] = self.session_id

                elif hasattr(self._initializer, "__call__"):
                    self._initializer()

        # Update the associated IP
        self.ip = web.ctx.ip

    def _save(self):
        super()._save()

        if self.get("_killed"):
            return

        if web.ctx.get("session_cookie_data", None) is not None:
            web.header("Set-Cookie", str(web.ctx.session_cookie_data))

    def expired(self):
        """
        Delete the old session
        """
        logger.debug("Session expired")
        try:
            super().kill()
        except KeyError:
            pass
        except Exception as e:
            logger.error("Could not kill session", exc_info=e)
        finally:
            if not self._config.ignore_expiry:
                raise SessionExpired(self._config.expired_message)

            if self.get("_killed"):
                del self._killed

            self.session_id = None
