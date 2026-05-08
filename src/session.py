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

    def getdata(self):
        try:
            pickled_data = web.cookies().get(self.cookie_name, "")
            if not pickled_data:
                return None

            data = self.decode(pickled_data)
            if type(data) is not dict:
                return None

            return data
        except Exception as e:
            print(e)
            return None

    def __contains__(self, sessionid):
        data = self.getdata()
        return data is not None and data.get("k", "") == sessionid

    def __getitem__(self, sessionid):
        logger.debug(f"Session get {sessionid}")
        try:
            data = self.getdata()

            # Check if the cookie data is valid
            if data is None:
                raise IndexError

            if data.get("k", "") != sessionid:
                raise IndexError

            if self.last_allowed_time is not None and data["atime"] < self.last_allowed_time:
                raise IndexError

            data["atime"] = datetime.datetime.now()
        except IndexError:
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

    def __setitem__(self, sessionid, data):
        assert type(data) is dict

        def callback(self, sessionid, data):
            logger.debug(f"Session set.callback {sessionid}")
            if data:
                data["atime"] = datetime.datetime.now()
                data["k"] = sessionid
                encoded_value = self.encode(data)
            else:
                encoded_value = ""

            cookie_value = self.setcookie(encoded_value)
            return cookie_value

        logger.debug(f"Session set {sessionid}")

        # Will be used when the server calls for response.headers
        if web.ctx.get("session_cookie_data", None) is None:
            session_cookie_data = CookieDataValue("")

            if not web.ctx.get("headers", None):
                web.ctx.headers = []

            web.ctx.headers.append(("Set-Cookie", session_cookie_data))
            web.ctx.session_cookie_data = session_cookie_data
        else:
            session_cookie_data = web.ctx.session_cookie_data

        fct = partial(callback, self, sessionid, data)
        session_cookie_data.set_callback(fct)

    def __delitem__(self, sessionid):
        self[sessionid] = None
        logger.debug("Session deleted")

    def cleanup(self, timeout):
        timeout = datetime.timedelta(
            timeout / (24.0 * 60 * 60)
        )  # timedelta takes numdays as arg
        self.last_allowed_time = datetime.datetime.now() - timeout


class CookieDataValue(str):
    def set_callback(self, fct):
        self.callback = fct

    def encode(self, encoding, **kwargs):
        fct = self.callback
        value = fct()

        if isinstance(value, bytes):
            return value

        return value.encode(encoding, **kwargs)


class Session(Session):
    def _reset(self):
        self._data = web.utils.storage({})
        self.ip = web.ctx.ip

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

                elif hasattr(self._initializer, "__call__"):
                    self._initializer()

        # Update the associated IP
        self.ip = web.ctx.ip

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
