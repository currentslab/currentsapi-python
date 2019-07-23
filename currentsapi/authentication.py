from requests.auth import AuthBase

def set_header_payload(auth_key):
    
    return {
        'Authorization': auth_key,
        'Content-Type': 'Application/JSON',
    }


class ApiAuth(AuthBase):
    def __init__(self, api_key):
        if not isinstance(api_key, str):
            raise ValueError('api_key must be string')
        self.api_key = api_key

    def __call__(self, request):
        request.headers.update(set_header_payload(self.api_key))
        return request


