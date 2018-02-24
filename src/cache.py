import pylibmc
import json

class Client(pylibmc.Client):

    def serialize(self, value):
        return json.dumps(value).encode('utf-8'), 0

    def deserialize(self, bytes_, flags):
        assert flags == 0
        return json.loads(bytes_.decode('utf-8'))

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