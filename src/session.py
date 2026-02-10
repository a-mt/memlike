import datetime
import logging

# Just re-exporting web.session(__all__), with some overwrites
from web.session import *


logger = logging.getLogger(__name__)


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
    def _check_expiry(self):
        pass

    def _load(self):
        self.ip = None
        try:
            super()._load()
        except KeyError:
            # session_id doesn't exist in store
            return self.expired()
