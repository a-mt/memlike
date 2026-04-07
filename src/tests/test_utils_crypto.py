import unittest
import web

from utils.crypto import gen_csrftoken


class UtilsCryptoTest(unittest.TestCase):
    def test_gen_csrftoken(self):
        csrftoken = gen_csrftoken(web.ctx.get("ip", "0.0.0.0"), web.config.session_parameters.secret_key)

        self.assertEqual(len(csrftoken), 44)
