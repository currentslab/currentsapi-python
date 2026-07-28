# Company news monitor

This example runs a small company, competitor, or industry watchlist against a
bounded Currents Search API window. It writes:

- `report.md`, a source-linked change report for review;
- `report.json`, the same new articles as structured data;
- a local state file containing article keys seen across runs.

Currents provides search results and article metadata. This script owns the
watchlist, date window, local state, deduplication, and report formatting. It is
not a managed monitor or alert service.

## Run the checked-in fixture

Install this repository's dependencies, then run:

```bash
python examples/company_news_monitor/monitor.py \
  --fixture examples/company_news_monitor/fixtures/search_responses.json \
  --state-file company-monitor-state.json \
  --output-dir company-monitor-output
```

The fixture uses fictional companies and `example.com` URLs. It needs no network
request, credentials, or customer data. Its fixed timestamps make the first run
deterministic. Delete the generated state file to reproduce that first run.

Run the same command again with the same state file. The second report contains
no new articles.

## Configure a watchlist

Each watch requires a unique `name` and `keywords`. `language` defaults to `en`.
The optional `domain` narrows that watch to one publisher domain.

```json
{
  "watches": [
    {
      "name": "Competitor names",
      "keywords": "\"Northstar Battery\" OR \"Atlas Storage\"",
      "language": "en"
    },
    {
      "name": "Industry policy",
      "keywords": "\"grid storage\" regulation",
      "language": "en",
      "domain": "example.com"
    }
  ]
}
```

Use the smallest watchlist that represents a real decision. Search does not
perform entity resolution, so ambiguous company names need additional terms.

## Run a live window

Create a [Currents API key](https://currentsapi.services/en/register), then set
it in your environment:

```bash
export CURRENTS_API_KEY="your-api-key"
```

Run an explicit UTC window:

```bash
python examples/company_news_monitor/monitor.py \
  --watchlist examples/company_news_monitor/watchlist.json \
  --start-date 2026-08-04T09:00:00Z \
  --end-date 2026-08-05T09:00:00Z \
  --page-size 20 \
  --state-file company-monitor-state.json \
  --output-dir company-monitor-output
```

Live mode sends `keywords`, `language`, `start_date`, `end_date`, `page_number`,
and `page_size` for every watch. It also sends `domain` when the watch defines
one.

Use a window and page size allowed by your Currents plan. Search windows,
lookback, page sizes, and retrievable result counts can vary by plan.

## Deduplication and state

The report treats the publisher URL and article ID as aliases. A match on either
alias merges the article and its watch names. The state file stores both aliases
when both are present.

The state file prevents the same article from appearing as new on later runs.
Keep a separate state file for each monitor. Back it up if missing alerts would
matter to your application.

## Limitations

- The script runs once. Your application must schedule it.
- The first run treats every in-window result as new.
- One page is requested per watch. Increase coverage only within plan limits.
- Names and Boolean terms can miss aliases or match unrelated entities.
- Results reflect the Currents index and are not exhaustive.
- Currents does not verify article claims or score their truth.
- API access does not grant publisher-content republication rights.
- Add retries, locking, state recovery, observability, and human review before
  using this pattern in a production workflow.

## Test

Run the focused offline tests:

```bash
python -m pytest tests/test_company_news_monitor_example.py
```
