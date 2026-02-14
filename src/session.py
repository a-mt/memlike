import datetime
import logging
import web
from copy import deepcopy

# Just re-exporting web.session(__all__), with some overwrites
from web.session import *


logger = logging.getLogger(__name__)


class SessionExpired(web.Unauthorized):
    pass


class DiskStore(DiskStore):
    def __contains__(self, key):
        logger.debug('DiskStore.has %s', key)
        return super().__contains__(key)

    def __getitem__(self, key):
        logger.debug('DiskStore.get %s', key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        logger.debug('DiskStore.set %s=%s', key, value)
        return super().__setitem__(key, value)


class DBStore(DBStore):
    def __contains__(self, key):
        logger.debug('DBStore.has %s', key)
        return super().__contains__(key)

    def __getitem__(self, key):
        logger.debug('DBStore.get %s', key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        logger.debug('DBStore.set %s=%s', key, value)
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
        logger.debug('Session.expired')
        try:
            super().kill()
        except Exception as e:
            logger.error(e)
        finally:
            if not self._config.ignore_expiry:
                raise SessionExpired(message=self._config.expired_message)

            if self.get('_killed'):
                del self._killed

            self.session_id = None
