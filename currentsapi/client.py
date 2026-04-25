import datetime
import requests
from dateutil import parser

from currentsapi import constants
from currentsapi.authentication import ApiAuth


class CurrentsAPIError(Exception):
    """Raised when the Currents API returns an error response."""

    def __init__(self, response):
        self.response = response
        super().__init__(str(response))

    @property
    def status(self):
        return self.response.get("status")

    @property
    def code(self):
        return self.response.get("code")

    @property
    def message(self):
        return self.response.get("message")


class CurrentsAPI:
    def __init__(
        self,
        api_key,
        domain=constants.DOMAIN,
        version=constants.VERSION,
        timeout=30,
    ):
        if not isinstance(api_key, str):
            raise ValueError("api_key must be a string")
        self.api_key = ApiAuth(api_key)
        self.latest_endpoint = constants.LATEST_NEWS_URL % (domain, version)
        self.search_endpoint = constants.SEARCH_URL % (domain, version)
        self.available_languages_endpoint = constants.AVAILABLE_LANGUAGES_URL % (domain, version)
        self.available_regions_endpoint = constants.AVAILABLE_REGIONS_URL % (domain, version)
        self.available_category_endpoint = constants.AVAILABLE_CATEGORIES_URL % (domain, version)
        self.timeout = timeout

    def _get(self, endpoint, params=None):
        r = requests.get(
            endpoint,
            auth=self.api_key,
            timeout=self.timeout,
            params=params or {},
        )
        if r.status_code != requests.codes.ok:
            raise CurrentsAPIError(r.json())
        return r.json()

    def latest_news(self, language=None):
        params = {}
        if language:
            if not isinstance(language, str):
                raise ValueError("language must be a string")
            params["language"] = language
        return self._get(self.latest_endpoint, params)

    def search(
        self,
        language=None,
        keywords=None,
        country=None,
        category=None,
        start_date=None,
        end_date=None,
    ):
        params = {}

        if keywords:
            if not isinstance(keywords, str):
                raise ValueError("keywords must be a string")
            params["keywords"] = keywords

        if country:
            if not isinstance(country, str):
                raise ValueError("country must be a string")
            params["country"] = country

        if language:
            if not isinstance(language, str):
                raise ValueError("language must be a string")
            params["language"] = language

        if category:
            if not isinstance(category, str):
                raise ValueError("category must be a string")
            params["category"] = category

        if start_date:
            date = self._parse_date(start_date, "start_date")
            params["start_date"] = date.strftime("%Y-%m-%dT%H:%M:%SZ")

        if end_date:
            date = self._parse_date(end_date, "end_date")
            params["end_date"] = date.strftime("%Y-%m-%dT%H:%M:%SZ")

        return self._get(self.search_endpoint, params)

    def available_languages(self):
        return self._get(self.available_languages_endpoint)

    def available_regions(self):
        return self._get(self.available_regions_endpoint)

    def available_category(self):
        return self._get(self.available_category_endpoint)

    @staticmethod
    def _parse_date(date_value, param_name):
        if isinstance(date_value, str):
            return parser.parse(date_value)
        elif isinstance(date_value, datetime.date):
            return date_value
        else:
            raise ValueError(
                "{} must be a string parsable by dateutil or a datetime/date object".format(
                    param_name
                )
            )
