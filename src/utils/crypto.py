import time
import os
from base58 import b58encode
from hashlib import sha256
from web.utils import safestr


def gen_csrftoken(ip, secret_key):
    """
    :param string ip  - web.ctx.ip
    :param string secret_key - web.config.session_parameters.secret_key
    """
    rand = os.urandom(16)
    now = time.time()

    hashable = f"{rand}{now}{safestr(ip)}{secret_key}"
    digest = sha256(hashable.encode("utf-8")).digest()
    return b58encode(digest).decode()
