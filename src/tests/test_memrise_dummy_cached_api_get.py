from . import test_memrise_dummy_get

from cache import memcache_client


class MemriseCachedApiUserGetTest(test_memrise_dummy_get.MemriseDummyGetTest):
    session = {}
    memrise = test_memrise_dummy_get.load_memrise("memrise.backends.DummyCachedApiMemrise")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.check_memcache()

    @classmethod
    def check_memcache(cls):
        if memcache_client.key_prefix != "test_":
            raise Exception("Running memcache without key prefix: not going further")

        # May raise pylibmc.SomeErrors (ie AUTHENTICATION FAILURE)
        memcache_client.get_stats()

    def setUp(self):
        super().setUp()
        memcache_client.flush_all()

    def test_memrise_courses_caching_logic(self):
        cache_key = "french_courses_1_german"

        with self.assertLogs("memrise.backends.cached_api", level="DEBUG") as cm:
            # Retrieve the list of courses on page "NA" => page 1
            result = self.memrise.courses(lang="french", cat="german", page="NA")
            self.assertIs(type(result), dict)
            self.assertEqual(result["page"], 1)

            # The result is now cached
            logs = list(cm.output)
            self.assertEqual(len(logs), 3)
            self.assertTrue(logs[0].endswith(f"Get {cache_key}"))
            self.assertTrue(logs[1].endswith(f"Miss {cache_key}"))
            self.assertTrue(logs[2].endswith(f"Save {cache_key}"))

        with self.assertLogs("memrise.backends.cached_api", level="DEBUG") as cm:
            # Retrieve the list of courses on page "1" => page 1
            result = self.memrise.courses(lang="french", cat="german", page="1")
            self.assertIs(type(result), dict)
            self.assertEqual(result["page"], 1)

            # The result is from the cache
            logs = list(cm.output)
            self.assertEqual(len(logs), 1)
            self.assertTrue(logs[-1].endswith(f"Get {cache_key}"))

        with self.assertLogs("memrise.backends.cached_api", level="DEBUG") as cm:
            # Retrieve the list of courses on page "1" => page 1
            result = self.memrise.courses(lang="french", cat="german", page=1)
            self.assertIs(type(result), dict)
            self.assertEqual(result["page"], 1)

            # The result is from the cache
            logs = list(cm.output)
            self.assertEqual(len(logs), 1)
            self.assertTrue(logs[-1].endswith(f"Get {cache_key}"))

        cache_key = "french_courses_2_german"

        with self.assertLogs("memrise.backends.cached_api", level="DEBUG") as cm:
            # Retrieve the list of courses on page "NA" => page 1
            result = self.memrise.courses(lang="french", cat="german", page=2)
            self.assertIs(type(result), dict)
            self.assertEqual(result["page"], 2)

            # The result is now cached
            logs = list(cm.output)
            self.assertEqual(len(logs), 3)
            self.assertTrue(logs[0].endswith(f"Get {cache_key}"))
            self.assertTrue(logs[1].endswith(f"Miss {cache_key}"))
            self.assertTrue(logs[2].endswith(f"Save {cache_key}"))
