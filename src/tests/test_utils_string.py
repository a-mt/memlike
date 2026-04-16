import unittest

from utils.string import slugify


class UtilsStringTest(unittest.TestCase):
    def test_slugify(self):
        slug = slugify("Iñtërnâtiônàlizætiøn 1!Iñtërnâtiônàlizætiøn 2?")

        self.assertEqual(slug, "internationalizaetion-1-internationalizaetion-2")
