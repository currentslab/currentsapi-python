# Source-linked news briefing

This example turns a Currents Search API response into two local files:

- `briefing.md` for a person to read;
- `briefing.json` for a dashboard, queue, or application-owned agent workflow.

Every item keeps its publisher URL and publication time. The script does not call a language model, summarize full publisher articles, or make decisions for the reader.

The example accompanies [Build a Source-Linked News Briefing with Currents Search API](https://currentsapi.services/en/blog/build-source-linked-news-briefing-currents-search-api).

## Run the checked-in fixture

Install the SDK from this checkout:

```bash
python -m pip install -e .
```

Generate deterministic output without a network request or API key:

```bash
python examples/source_linked_briefing/briefing.py \
  --fixture examples/source_linked_briefing/fixtures/search_response.json \
  --output-dir briefing-output
```

The fixture contains fictional `example.com` articles. It contains no customer data, publisher article bodies, or credentials. Its `_fixture_generated_at` value keeps both output files identical across runs.

For another saved Search API response, add `_fixture_generated_at` at the top level or pass `--generated-at` explicitly.

## Run a live search

Create a [free Currents API key](https://currentsapi.services/en/register), then export it:

```bash
export CURRENTS_API_KEY="your-api-key"
```

Run a live search:

```bash
python examples/source_linked_briefing/briefing.py \
  --keywords "energy storage" \
  --language en \
  --output-dir briefing-output
```

Live mode calls `CurrentsAPI.search()`. Fixture mode reads a saved Search API response. Both modes use the same validation, normalization, ordering, and rendering path.

## Output

Articles are ordered by publication time, newest first. Titles provide a stable tie-breaker. Missing optional fields become empty values rather than fabricated content.

The Markdown output remains deliberately plain:

```markdown
# Source-Linked News Briefing

Generated at: 2026-07-25T00:00:00+00:00

- Battery storage policy enters public consultation - <https://example.com/energy/storage-policy>
  - Published: 2026-07-25T08:00:00Z
  - A fictional example describing a public policy consultation.
```

The JSON output contains `generated_at` and a normalized `articles` list. Each article can contain:

- `title`
- `description`
- `url`
- `published`
- `language`
- `category`

## Where an agent fits

Currents retrieves structured news results and preserves source context. Your application owns any later prompt, model call, summary, alert, embedding, storage policy, or human-review step.

If you pass the JSON output to a model, instruct it to use only the supplied items, preserve every source URL, distinguish source facts from inference, and state when the retrieved context is insufficient.

## Limitations

- Search results reflect the index at request time. A saved briefing is not automatically refreshed.
- Network failures, invalid credentials, plan limits, and rate limits can stop live execution.
- Overlapping searches can return duplicate articles. This single-query example does not deduplicate across runs.
- Descriptions can be missing or truncated. Follow the publisher URL for the source context.
- Access through an API does not grant republication rights. Follow your Currents plan terms and publisher requirements.
- Do not treat generated or retrieved text as investment, legal, medical, or other high-stakes advice.
- Add retries, caching, incremental date windows, observability, and human review before scheduling production workloads.

## Test

Run the focused offline tests:

```bash
python -m pytest tests/test_source_linked_briefing_example.py
```

The tests cover source preservation, publication times, deterministic ordering, malformed responses, the checked-in fixture, and the live SDK adapter.
