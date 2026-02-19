from . import test_memrise_dummy_get


class MemriseDummyApiGetTest(test_memrise_dummy_get.MemriseDummyGetTest):
    session = {}
    memrise = test_memrise_dummy_get.load_memrise('memrise.backends.DummyApiMemrise')
