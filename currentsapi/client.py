import datetime
import requests
from dateutil import parser

from currentsapi import constants
from currentsapi.authentication import ApiAuth


class CurrentsAPIError(Exception):
    """Raised when the Currents API returns an error response."""

    def __init__(self, response, http_status=None):
        if not isinstance(response, dict):
            response = {}
        self.response = response
        self._http_status = http_status
        self._code = response.get("code")
        self._message = response.get("message") or response.get("msg")
        super().__init__(self._message or (str(response) if response else "Unknown API error"))

    @property
    def status(self):
        """HTTP status code as int; payload status used only as last resort."""
        if self._http_status is not None:
            return self._http_status
        payload_status = self.response.get("status")
        try:
            return int(payload_status)
        except (TypeError, ValueError):
            return payload_status

    @property
    def code(self):
        return self._code

    @property
    def message(self):
        return self._message


class CurrentsAPI:
    def __init__(
        self,
        api_key,
        domain=constants.DOMAIN,
        version=constants.VERSION,
        timeout=30,
        allow_custom_domain=False,
    ):
        if not isinstance(api_key, str):
            raise ValueError("api_key must be a string")
        if domain != constants.DOMAIN and not allow_custom_domain:
            raise ValueError(
                "Passing a custom domain forwards your API key to that host. "
                "If this is intentional (e.g. testing), pass "
                "allow_custom_domain=True."
            )
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
            raise self._error_from_response(r)
        try:
            payload = r.json()
        except ValueError:
            raise CurrentsAPIError(
                {"message": "Response body is not valid JSON"},
                http_status=r.status_code,
            )
        return payload

    @staticmethod
    def _error_from_response(r):
        try:
            payload = r.json()
        except ValueError:
            payload = {}
        if not isinstance(payload, dict):
            payload = {
                "message": "API returned a non-object error payload",
                "details": payload,
            }
        return CurrentsAPIError(payload, http_status=r.status_code)

    def latest_news(self, language=None):
        params = {}
        if language is not None:
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

        if keywords is not None:
            if not isinstance(keywords, str):
                raise ValueError("keywords must be a string")
            if not keywords.strip():
                raise ValueError("keywords must not be empty")
            params["keywords"] = keywords

        if country is not None:
            if not isinstance(country, str):
                raise ValueError("country must be a string")
            params["country"] = country

        if language is not None:
            if not isinstance(language, str):
                raise ValueError("language must be a string")
            params["language"] = language

        if category is not None:
            if not isinstance(category, str):
                raise ValueError("category must be a string")
            params["category"] = category

        if start_date is not None:
            date = self._normalize_date(
                self._parse_date(start_date, "start_date"), "start_date"
            )
            params["start_date"] = date.strftime("%Y-%m-%dT%H:%M:%SZ")

        if end_date is not None:
            date = self._normalize_date(
                self._parse_date(end_date, "end_date"), "end_date"
            )
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
            try:
                return datetime.date.fromisoformat(date_value)
            except ValueError:
                pass
            try:
                return parser.parse(date_value)
            except (OverflowError, ValueError) as exc:
                raise ValueError(
                    "{} is not a parsable date: {}".format(param_name, exc)
                ) from exc
        elif isinstance(date_value, datetime.date):
            return date_value
        else:
            raise ValueError(
                "{} must be a string parsable by dateutil or a datetime/date object".format(
                    param_name
                )
            )

    @staticmethod
    def _normalize_date(date_value, param_name):
        if isinstance(date_value, datetime.datetime):
            if date_value.tzinfo is None:
                raise ValueError(
                    "{} datetime must be timezone-aware; attach a tzinfo "
                    "(naive datetimes are ambiguous and are NOT assumed to be "
                    "UTC)".format(param_name)
                )
            return date_value.astimezone(datetime.timezone.utc)
        if isinstance(date_value, datetime.date):
            return datetime.datetime(
                date_value.year, date_value.month, date_value.day,
                tzinfo=datetime.timezone.utc,
            )
        return date_value
