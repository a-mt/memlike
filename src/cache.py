import pylibmc
import json
import time
import settings


class Lock:
    """
    Lock to make computations set to memcached unique
    To use it:
        with Lock(memcache_client, cache_key) as retries:
            do something
    """

    def __init__(self, memcache_client, cache_key):
        """
        @param MemcacheClient memcache_client
        @param string cache_key
        """
        self.memcache_client = memcache_client
        self.cache_key = cache_key

    def __enter__(self):
        if not self.cache_key:
            return 0

        lock = False
        tries = 0
        max_tries = 1000

        while lock is False and tries < max_tries:
            try:
                lock = self.memcache_client.add("lock:" + self.cache_key, 1, 60)  # lock lasts 1 min max
            except Exception as e:
                print(e)
                break

            if lock:
                break
            tries += 1
            time.sleep(1)

        return tries

    def __exit__(self, type, value, traceback):
        if not self.cache_key:
            return

        try:
            self.memcache_client.delete("lock:" + self.cache_key)
        except Exception as e:
            print(e)


class MemcacheClient(pylibmc.Client):
    """
    Proxy for pylibmc.Client
    Save and retrieve data as JSON
    Catches memcached errors

    see
    https://deepwiki.com/lericson/pylibmc/3-user-guide
    https://sendapatch.se/projects/pylibmc/reference.html
    https://github.com/memcached/memcached/blob/master/doc/protocol.txt
    """

    key_prefix = ""

    def lock(self, key):
        return Lock(self, self.key_prefix + key)

    # +-----------------------------------------------------
    # | JSON SERIALIZATION/DESERIALIZATION
    # +-----------------------------------------------------
    def serialize(self, value):
        return json.dumps(value).encode("utf-8"), 0

    def deserialize(self, bytes_, flags):
        assert flags == 0
        return json.loads(bytes_.decode("utf-8"))

    # +-----------------------------------------------------
    # | CATCH FAILURES
    # +-----------------------------------------------------
    def delete(self, key):
        try:
            res = super(MemcacheClient, self).delete(self.key_prefix + key)
            return res
        except Exception as e:
            print(e)
            return None

    def get(self, key):
        try:
            res = super(MemcacheClient, self).get(self.key_prefix + key)
            return res
        except Exception as e:
            print(e)
            return None

    def set(self, key, data, **kwargs):
        try:
            res = super(MemcacheClient, self).set(self.key_prefix + key, data, **kwargs)
            return res
        except Exception as e:
            print(e)
            return None


def load_memcache_client():
    """
    Note that the client is created without attempting to connect
    """

    # https://devcenter.heroku.com/articles/memcachier#python
    # fmt: off
    client = MemcacheClient(
        settings.MEMCACHE_SERVERS,
        binary=True,
        username=settings.MEMCACHE_USERNAME,
        password=settings.MEMCACHE_PASSWORD,
        behaviors={
            # Faster IO
            "tcp_nodelay": True,

            # Keep connection alive
            "tcp_keepalive": True,

            # Timeout for set/get requests
            "connect_timeout": 2000, # ms
            "send_timeout": 750 * 1000, # us
            "receive_timeout": 750 * 1000, # us
            "_poll_timeout": 2000, # ms

            # Better failover
            "ketama": True,
            "remove_failed": 1,
            "retry_timeout": 2,
            "dead_timeout": 30,
        },
    )
    # fmt: on

    client.key_prefix = settings.MEMCACHE_KEY_PREFIX
    return client


# Load a client with the default settings
memcache_client = load_memcache_client()
