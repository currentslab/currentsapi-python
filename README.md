# currentsapi-python

The official Python SDK for the [Currents API](https://currentsapi.services/en/docs/).

## Installation

Install the package from PyPI. The distribution name is `currentsapi` (this
repository is `currentsapi-python`, and the Python import name is also
`currentsapi`):

```bash
pip install currentsapi
```

Python 3.8+ is supported.

## Usage

Import the client and initialize it with your API key:

```python
from currentsapi import CurrentsAPI

api = CurrentsAPI(api_key="YOUR_API_KEY")
```

## Endpoints

### Latest News

Retrieve the latest news headlines. Optionally filter by language:

```python
api.latest_news()
api.latest_news(language="en")
```

### Search

Search news articles with optional filters:

```python
api.search(keywords="OpenAI", language="en")
api.search(country="US", category="technology", start_date="2024-01-01", end_date="2024-12-31")
```

Supported parameters:

- `keywords` – search keywords
- `language` – article language code
- `country` – country code
- `category` – news category
- `start_date` – start date (`YYYY-MM-DD` or `datetime` object)
- `end_date` – end date (`YYYY-MM-DD` or `datetime` object)

### Available Resources

```python
api.available_languages()
api.available_regions()
api.available_category()
```

## Examples

- [Generate a source-linked news briefing](examples/source_linked_briefing/README.md) from a live Search API response or a deterministic offline fixture.
- [Build a company news monitor](examples/company_news_monitor/README.md) with
  a JSON watchlist, bounded search window, local state, and deterministic fixture.

## Authentication

All requests are authenticated using an `Authorization` header. Pass your API key when instantiating the client:

```python
api = CurrentsAPI(api_key="YOUR_API_KEY")
```

Get your API key at [https://currentsapi.services/en/register](https://currentsapi.services/en/register).

## License

MIT License

## Error handling

Any non-200 API response raises `CurrentsAPIError`, which exposes the parsed
response body:

```python
from currentsapi.client import CurrentsAPIError

try:
    api.latest_news()
except CurrentsAPIError as exc:
    print(exc.status, exc.code, exc.message)
```
