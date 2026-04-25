import datetime
import unittest
from unittest.mock import Mock, patch

from currentsapi import CurrentsAPI
from currentsapi.client import CurrentsAPIError


class TestClient(unittest.TestCase):
    def test_invalid_api_key(self):
        with self.assertRaises(TypeError):
            CurrentsAPI()

        with self.assertRaises(ValueError):
            CurrentsAPI(1)

        with self.assertRaises(ValueError):
            CurrentsAPI(None)

    def test_urls_setup(self):
        api = CurrentsAPI("dummy_key")
        self.assertEqual(api.latest_endpoint, "https://api.currentsapi.services/v1/latest-news")
        self.assertEqual(api.search_endpoint, "https://api.currentsapi.services/v1/search")
        self.assertEqual(
            api.available_languages_endpoint,
            "https://api.currentsapi.services/v1/available/languages",
        )
        self.assertEqual(
            api.available_regions_endpoint,
            "https://api.currentsapi.services/v1/available/regions",
        )
        self.assertEqual(
            api.available_category_endpoint,
            "https://api.currentsapi.services/v1/available/categories",
        )

        api = CurrentsAPI("dummy_key", "localhost", "v0")
        self.assertEqual(api.latest_endpoint, "https://localhost/v0/latest-news")
        self.assertEqual(api.search_endpoint, "https://localhost/v0/search")

    def test_key_setup(self):
        api = CurrentsAPI("dummy_key")
        self.assertEqual(api.api_key.api_key, "dummy_key")

    @patch("currentsapi.client.requests.get")
    def test_latest_news_without_language(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=Mock(return_value={"status": "ok"}))
        api = CurrentsAPI("key")
        result = api.latest_news()
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn("latest-news", args[0])
        self.assertEqual(kwargs["params"], {})
        self.assertEqual(result, {"status": "ok"})

    @patch("currentsapi.client.requests.get")
    def test_latest_news_with_language(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=Mock(return_value={"status": "ok"}))
        api = CurrentsAPI("key")
        result = api.latest_news(language="en")
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"], {"language": "en"})
        self.assertEqual(result, {"status": "ok"})

    @patch("currentsapi.client.requests.get")
    def test_search_all_params(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=Mock(return_value={"status": "ok"}))
        api = CurrentsAPI("key")
        result = api.search(
            keywords="OpenAI",
            language="en",
            country="US",
            category="technology",
            start_date="2024-01-15",
            end_date="2024-06-30",
        )
        args, kwargs = mock_get.call_args
        self.assertEqual(
            kwargs["params"],
            {
                "keywords": "OpenAI",
                "language": "en",
                "country": "US",
                "category": "technology",
                "start_date": "2024-01-15T00:00:00Z",
                "end_date": "2024-06-30T00:00:00Z",
            },
        )
        self.assertEqual(result, {"status": "ok"})

    @patch("currentsapi.client.requests.get")
    def test_search_with_datetime_objects(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=Mock(return_value={"status": "ok"}))
        api = CurrentsAPI("key")
        start = datetime.date(2024, 1, 15)
        end = datetime.date(2024, 6, 30)
        api.search(start_date=start, end_date=end)
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["start_date"], "2024-01-15T00:00:00Z")
        self.assertEqual(kwargs["params"]["end_date"], "2024-06-30T00:00:00Z")

    @patch("currentsapi.client.requests.get")
    def test_available_languages(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=Mock(return_value={"languages": []}))
        api = CurrentsAPI("key")
        result = api.available_languages()
        args, kwargs = mock_get.call_args
        self.assertIn("available/languages", args[0])
        self.assertEqual(result, {"languages": []})

    @patch("currentsapi.client.requests.get")
    def test_available_regions(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=Mock(return_value={"regions": []}))
        api = CurrentsAPI("key")
        result = api.available_regions()
        args, kwargs = mock_get.call_args
        self.assertIn("available/regions", args[0])
        self.assertEqual(result, {"regions": []})

    @patch("currentsapi.client.requests.get")
    def test_available_category(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=Mock(return_value={"categories": []}))
        api = CurrentsAPI("key")
        result = api.available_category()
        args, kwargs = mock_get.call_args
        self.assertIn("available/categories", args[0])
        self.assertEqual(result, {"categories": []})

    @patch("currentsapi.client.requests.get")
    def test_auth_header_applied(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=Mock(return_value={"status": "ok"}))
        api = CurrentsAPI("secret_key")
        api.latest_news()
        args, kwargs = mock_get.call_args
        auth = kwargs["auth"]
        req = Mock(headers={})
        auth(req)
        self.assertEqual(req.headers["Authorization"], "secret_key")

    @patch("currentsapi.client.requests.get")
    def test_api_error_raises_exception(self, mock_get):
        mock_get.return_value = Mock(
            status_code=401,
            json=Mock(return_value={"status": "error", "code": "Unauthorized", "message": "Invalid key"}),
        )
        api = CurrentsAPI("key")
        with self.assertRaises(CurrentsAPIError) as ctx:
            api.latest_news()
        self.assertEqual(ctx.exception.status, "error")
        self.assertEqual(ctx.exception.code, "Unauthorized")
        self.assertEqual(ctx.exception.message, "Invalid key")

    def test_invalid_keywords_type(self):
        api = CurrentsAPI("key")
        with self.assertRaises(ValueError):
            api.search(keywords=123)

    def test_invalid_start_date(self):
        api = CurrentsAPI("key")
        with self.assertRaises(ValueError):
            api.search(start_date=123)


if __name__ == "__main__":
    unittest.main()
