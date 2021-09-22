'''

Basic test 

'''
import unittest
from currentsapi import CurrentsAPI
from currentsapi import constants



class TestBasics(unittest.TestCase):

    def test_invalid_api(self):
        with self.assertRaises(TypeError):
            CurrentsAPI()

        with self.assertRaises(ValueError):
            CurrentsAPI(1)

        with self.assertRaises(ValueError):
            CurrentsAPI(None)

    def test_urls_setup(self):

        api = CurrentsAPI('dummy_key')
        assert api.latest_endpoint == 'https://api.currentsapi.services/v1/latest-news'
        assert api.search_endpoint == 'https://api.currentsapi.services/v1/search'

        api = CurrentsAPI('dummy_key', 'localhost', 'v0')
        assert api.latest_endpoint == 'https://localhost/v0/latest-news'
        assert api.search_endpoint == 'https://localhost/v0/search'

        api = CurrentsAPI('dummy_key', 'localhost', 'v1.1')
        assert api.latest_endpoint == 'https://localhost/v1.1/latest-news'        
        assert api.search_endpoint == 'https://localhost/v1.1/search'


    def test_key_setup(self):
        api = CurrentsAPI('dummy_key')
        assert api.api_key.api_key == 'dummy_key'
