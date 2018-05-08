import pylibmc
import json, time
from os import environ

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
          try:
              lock = self.mc.add('lock:' + self.cache_key, 1, 60)  # lock lasts 1 min max
          except Exception as e:
              print e
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
            self.mc.delete('lock:' + self.cache_key)
        except Exception as e:
            print e

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

# https://devcenter.heroku.com/articles/memcachier#python
if environ.get('MEMCACHIER_SERVERS', ''):
    servers = environ.get('MEMCACHIER_SERVERS', '').split(',')
    user    = environ.get('MEMCACHIER_USERNAME', '')
    passw   = environ.get('MEMCACHIER_PASSWORD', '')

    mc = Client(servers, binary=True, username=user, password=passw, behaviors={
      # Faster IO
      "tcp_nodelay": True,

      # Keep connection alive
      'tcp_keepalive': True,

      # Timeout for set/get requests
      'connect_timeout': 2000, # ms
      'send_timeout': 750 * 1000, # us
      'receive_timeout': 750 * 1000, # us
      '_poll_timeout': 2000, # ms

      # Better failover
      'ketama': True,
      'remove_failed': 1,
      'retry_timeout': 2,
      'dead_timeout': 30,
    })

else:
    mc = Client(['127.0.0.1'])