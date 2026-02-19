from . import test_memrise_dummy_edit


class MemriseDummyApiEditTest(test_memrise_dummy_edit.MemriseDummyEditTest):
    session = {}
    memrise = test_memrise_dummy_edit.load_memrise('memrise.backends.DummyApiMemrise')
