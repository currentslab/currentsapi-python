import requests
import datetime
from dateutil import parser
from currentsapi.authentication import ApiAuth
from currentsapi import constants

class APIException(Exception):

    def __init__(self, exception):
        self.exception = exception

    def get_exception(self):
        return self.exception

    def get_status(self):
        if self.exception["status"]:
            return self.exception["status"]

    def get_code(self):
        if self.exception["code"]:
            return self.exception["code"]

    def get_message(self):
        if self.exception["message"]:
            return self.exception["message"]


class CurrentsAPI():

    def __init__(self, api_key, 
        domain=constants.DOMAIN, version=constants.VERSION, timeout=30):
        if not isinstance(api_key, str):
            raise ValueError('api_key must be string')
        self.api_key = ApiAuth(api_key)
        self.latest_endpoint = constants.LATEST_NEWS_URL % (domain, version)
        self.search_endpoint = constants.SEARCH_URL % (domain, version)
        self.timeout = timeout

    def latest_news(self):
        r = requests.get(self.latest_endpoint, auth=self.api_key, timeout=self.timeout)
        if r.status_code != requests.codes.ok:
            raise APIException(r.json())
        return r.json()
    

    def search(self, country=None, language=None, keywords=None, category=None, 
        page_number=None, limit=None, start_date=None, end_date=None, has_image=None, has_description=None):
        payload = {}

        if keywords:
            if not isinstance(keywords, str):
                raise ValueError('keywords should be string')
            payload['keywords'] = keywords
        

        if country:
            if not isinstance(country, str):
                raise ValueError('country should be string')
            payload['country'] = country

        if language:
            if not isinstance(language, str):
                raise ValueError('language should be string')
            payload['language'] = language

        if category:
            if not isinstance(category, str) and not isinstance(category, list):
                raise ValueError('category should be string')
            if isinstance(category, list):
                payload['category'] = ','.join(category)
            else:
                payload['category'] = category

        if page_number:
            if not int(page_number) == page_number:
                raise ValueError('page_number should be integer')
            payload['page_number'] = page_number

        if limit:
            if not int(limit) == limit:
                raise ValueError('limit should be integer')
            payload['limit'] = limit


        if start_date:
            if isinstance(start_date, str):
                date = parser(start_date)
            elif isinstance(end_date, datetime.date):
                date = end_date
            else:
                raise ValueError('start_date must be string parsable by dateutil or datetime object')
            payload['start_date'] = date.strftime('%Y-%m-%dT%H:%M:%SZ')

        if end_date:
            if isinstance(end_date, str):
                date = parser(end_date)
            elif isinstance(end_date, datetime.date):
                date = end_date
            else:
                raise ValueError('end_date must be string parsable by dateutil or datetime object')
            payload['end_date'] = date.strftime('%Y-%m-%dT%H:%M:%SZ')

        if has_image:
            payload['has_image'] = 'true' if has_image else 'false'

        if has_description:
            payload['has_description'] = 'true' if has_description else 'false'
        r = requests.get(self.search_endpoint, auth=self.api_key, 
            timeout=self.timeout, 
            params=payload)

        if r.status_code != requests.codes.ok:
            raise APIException(r.json())

        return r.json()