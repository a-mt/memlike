import pylibmc
import json, time

class Lock:
    """
    Lock to make computations set to memcached unique
    To use it:
        with Lock(mc, cache_key) as retries:
            do something
    """

    def __init__(self, mc, cache_key):
        self.mc        = mc
        self.cache_key = cache_key

    def __enter__(self):
        if not self.cache_key:
            return 0

        lock      = False
        tries     = 0
        max_tries = 1000

        while lock == False and tries < max_tries:
          lock = self.mc.add('lock:' + self.cache_key, 1, 60)  # lock lasts 1 min max
          if lock:
            break
          tries += 1
          time.sleep(1)

        return tries

    def __exit__(self, type, value, traceback):
        if not self.cache_key:
            return

        self.mc.delete('lock:' + self.cache_key)

class Client(pylibmc.Client):
    """
    Proxy for pylibmc.Client
    Save and retrieve data as JSON
    Catches memcached errors
    """

    def lock(self, cache_key):
        return Lock(self, cache_key)

    #+-----------------------------------------------------
    #| JSON SERIALIZATION/DESERIALIZATION
    #+-----------------------------------------------------
    def serialize(self, value):
        return json.dumps(value).encode('utf-8'), 0

    def deserialize(self, bytes_, flags):
        assert flags == 0
        return json.loads(bytes_.decode('utf-8'))

    #+-----------------------------------------------------
    #| CATCH FAILURES
    #+-----------------------------------------------------
    def get(self, key):
        try:
            res = super(Client, self).get(key)
            return res
        except Exception as e:
            print e
            return None

    def set(self, key, data, **kwargs):
        try:
            res = super(Client, self).set(key, data, **kwargs)
            return res
        except Exception as e:
            print e
            return None

mc = Client(['127.0.0.1'])