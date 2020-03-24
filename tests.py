import re
import os
import hourlyplanet as hp
import unittest



class TestUtils(unittest.TestCase):

    def test_base_58(self):
        self.assertEqual(hp.Util.encode_base58(1234567), "7jZD")
        self.assertEqual(hp.Util.encode_base58(1234567l), "7jZD")
        self.assertEqual(hp.Util.encode_base58(0), "")
        self.assertEqual(hp.Util.encode_base58(-1234567), "")
        with self.assertRaises(TypeError):
            hp.Util.encode_base58(1234567.123)
        with self.assertRaises(TypeError):
            hp.Util.encode_base58("1234567")

    def test_fetch_image(self):
        if os.path.exists("test-image.jpg"):
            os.unlink("test-image.jpg")

        with self.assertRaises(Exception):
            hp.Util.fetch_image_to_path("http://placekitten.com/-1/-1", "test-image.jpg")

        hp.Util.fetch_image_to_path("http://placekitten.com/200/300", "test-image.jpg")

        self.assertTrue(os.path.exists("test-image.jpg"))
        self.assertEqual(os.path.getsize("test-image.jpg"), 7191)

        os.unlink("test-image.jpg")

    def test_load_image(self):
        if os.path.exists("test-image.jpg"):
            os.unlink("test-image.jpg")

        with self.assertRaises(IOError):
            data = hp.Util.load_image_data("test-image.jpg")

        hp.Util.fetch_image_to_path("http://placekitten.com/200/300", "test-image.jpg")

        self.assertTrue(os.path.exists("test-image.jpg"))
        data = hp.Util.load_image_data("test-image.jpg")

        self.assertEqual(len(data), 7191)
        self.assertEqual(type(data), str)

        os.unlink("test-image.jpg")


class TestSearchTermMatching(unittest.TestCase):

    def setUp(self):
        self.translations = hp.load_translations("translations.yaml")

    def test_search_term_matching(self):
        self.assertIsNone(hp.find_search_term("Can I have an image please", self.translations))
        self.assertEqual(hp.find_search_term("Can I have an image of Saturn please", self.translations), "saturn")
        self.assertEqual(hp.find_search_term("Can I have an image of The Great Red Spot please", self.translations), "great red spot")
        self.assertEqual(hp.find_search_term("Can I have an image of a moon, please", self.translations), "moon")
        self.assertEqual(hp.find_search_term("Can I have an image of Messier 123, please", self.translations), "messier 123")
        self.assertEqual(hp.find_search_term("Can I please have an image of the Meathook Galaxy", self.translations), "meathook galaxy")
        self.assertEqual(hp.find_search_term("Can I have an image of an elliptical galaxy, please", self.translations), "elliptical galaxy")

    def test_search_term_matching_i18n(self):
        # German
        self.assertIsNone(hp.find_search_term("Kann ich bitte ein Bild von Jupiter haben?", self.translations))

        # Spanish
        self.assertIsNone(hp.find_search_term("Puedo tener una foto de Jupiter, por favor", self.translations))


if __name__ == '__main__':
    unittest.main()





