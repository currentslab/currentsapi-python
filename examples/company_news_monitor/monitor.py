#!/usr/bin/env python3
"""Build a source-linked company news change report."""

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit

import requests


SEARCH_URL = "https://api.currentsapi.services/v1/search"


def parse_args():
    example_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--watchlist",
        type=Path,
        default=example_dir / "watchlist.json",
        help="Read company and competitor searches from JSON.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Read saved Search API responses instead of calling the network.",
    )
    parser.add_argument("--start-date", help="Set the inclusive RFC 3339 window start.")
    parser.add_argument("--end-date", help="Set the inclusive RFC 3339 window end.")
    parser.add_argument(
        "--state-file",
        type=Path,
        default=Path("company-news-monitor-state.json"),
        help="Store article keys already included in earlier reports.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("company-news-monitor-output"),
        help="Write report.md and report.json here.",
    )
    parser.add_argument(
        "--generated-at",
        help="Override the report timestamp. Fixtures provide a stable default.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=20,
        help="Request this many results per watch in live mode.",
    )
    return parser.parse_args()


def parse_timestamp(value, label):
    if not isinstance(value, str) or not value:
        raise ValueError("{} must be a non-empty RFC 3339 timestamp".format(label))
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("{} must be an RFC 3339 timestamp".format(label)) from exc
    if parsed.tzinfo is None:
        raise ValueError("{} must include a timezone".format(label))
    return parsed.astimezone(timezone.utc)


def format_timestamp(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_watchlist(path):
    payload = load_json(path)
    if not isinstance(payload, dict) or not isinstance(payload.get("watches"), list):
        raise ValueError("watchlist must contain a watches list")

    watches = []
    names = set()
    for item in payload["watches"]:
        if not isinstance(item, dict):
            raise ValueError("every watch must be an object")
        name = item.get("name")
        keywords = item.get("keywords")
        query = item.get("query")
        language = item.get("language", "en")
        domain = item.get("domain")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("every watch requires a non-empty name")
        if name in names:
            raise ValueError("watch names must be unique")
        search_fields = {
            key: value
            for key, value in (("keywords", keywords), ("query", query))
            if value is not None
        }
        if len(search_fields) != 1:
            raise ValueError("every watch requires exactly one of keywords or query")
        search_field, search_value = next(iter(search_fields.items()))
        if not isinstance(search_value, str) or not search_value.strip():
            raise ValueError(
                "watch {} must be a non-empty string".format(search_field)
            )
        if not isinstance(language, str) or not language.strip():
            raise ValueError("watch language must be a non-empty string")
        if domain is not None and (
            not isinstance(domain, str) or not domain.strip()
        ):
            raise ValueError("watch domain must be a non-empty string")
        names.add(name)
        watch = {
            "name": name,
            "language": language,
            "domain": domain,
            search_field: search_value,
        }
        watches.append(watch)
    if not watches:
        raise ValueError("watchlist must contain at least one watch")
    return watches


def resolve_window(args, fixture):
    start_value = args.start_date
    end_value = args.end_date
    if fixture:
        start_value = start_value or fixture.get("_fixture_start_date")
        end_value = end_value or fixture.get("_fixture_end_date")
    start = parse_timestamp(start_value, "start_date")
    end = parse_timestamp(end_value, "end_date")
    if start > end:
        raise ValueError("start_date must not be after end_date")
    return start, end


def resolve_generated_at(args, fixture):
    if args.generated_at:
        return format_timestamp(parse_timestamp(args.generated_at, "generated_at"))
    if fixture:
        return format_timestamp(
            parse_timestamp(
                fixture.get("_fixture_generated_at"),
                "_fixture_generated_at",
            )
        )
    return format_timestamp(datetime.now(timezone.utc))


def validate_search_response(response):
    if not isinstance(response, dict):
        raise ValueError("Search API response must be an object")
    if response.get("status") != "ok":
        raise ValueError("Search API response status must be 'ok'")
    if not isinstance(response.get("news"), list):
        raise ValueError("Search API response news must be a list")
    if any(not isinstance(article, dict) for article in response["news"]):
        raise ValueError("every news item must be an object")


def fixture_response(fixture, watch):
    responses = fixture.get("responses")
    if not isinstance(responses, dict):
        raise ValueError("fixture must contain a responses object")
    if watch["name"] not in responses:
        raise ValueError(
            "fixture is missing a response for watch '{}'".format(watch["name"])
        )
    response = responses[watch["name"]]
    validate_search_response(response)
    return response


def fetch_live_response(watch, start, end, page_size):
    api_key = os.environ.get("CURRENTS_API_KEY")
    if not api_key:
        raise ValueError("CURRENTS_API_KEY is required for live mode")
    if page_size < 1:
        raise ValueError("page_size must be positive")

    search_fields = [
        key for key in ("keywords", "query") if watch.get(key) is not None
    ]
    if len(search_fields) != 1:
        raise ValueError("watch requires exactly one of keywords or query")
    search_field = search_fields[0]
    search_value = watch[search_field]
    if not isinstance(search_value, str) or not search_value.strip():
        raise ValueError("watch {} must be a non-empty string".format(search_field))

    params = {
        search_field: search_value,
        "language": watch["language"],
        "start_date": format_timestamp(start),
        "end_date": format_timestamp(end),
        "page_number": 1,
        "page_size": page_size,
    }
    if watch["domain"]:
        params["domain"] = watch["domain"]

    response = requests.get(
        SEARCH_URL,
        headers={"Authorization": "Bearer {}".format(api_key)},
        params=params,
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    validate_search_response(payload)
    return payload


def normalize_article(article, start, end):
    title = article.get("title")
    url = article.get("url")
    published = article.get("published")
    article_id = article.get("id")
    description = article.get("description")

    for label, value in (
        ("title", title),
        ("url", url),
        ("published", published),
        ("id", article_id),
        ("description", description),
    ):
        if value is not None and not isinstance(value, str):
            raise ValueError("news item {} must be a string".format(label))
    if not url:
        raise ValueError("news item url must be present")
    parsed_url = urlsplit(url)
    if (
        parsed_url.scheme.lower() not in {"http", "https"}
        or not parsed_url.netloc
        or any(character.isspace() or ord(character) < 32 for character in url)
    ):
        raise ValueError("news item url must be an HTTP or HTTPS URL")
    published_at = parse_timestamp(published, "news item published")
    if published_at < start or published_at > end:
        return None

    keys = ["url:{}".format(url)]
    if article_id:
        keys.append("id:{}".format(article_id))
    return {
        "keys": keys,
        "title": title or "Untitled",
        "description": description or "",
        "url": url,
        "published": format_timestamp(published_at),
    }


def load_state(path):
    if not path.exists():
        return set()
    payload = load_json(path)
    keys = payload.get("seen_article_keys") if isinstance(payload, dict) else None
    if not isinstance(keys, list) or any(not isinstance(key, str) for key in keys):
        raise ValueError("state file must contain a seen_article_keys list")
    return set(keys)


def collect_articles(watches, responses, start, end, seen_keys):
    by_alias = {}
    collected = []
    watch_counts = {}
    discovered_keys = set()

    for watch in watches:
        response = responses[watch["name"]]
        validate_search_response(response)
        matched = 0
        for raw_article in response["news"]:
            article = normalize_article(raw_article, start, end)
            if article is None:
                continue
            matched += 1
            keys = tuple(article["keys"])
            key_set = set(keys)
            discovered_keys.update(keys)
            existing_articles = []
            for key in keys:
                existing = by_alias.get(key)
                if existing is not None and all(
                    existing is not candidate for candidate in existing_articles
                ):
                    existing_articles.append(existing)
            if existing_articles:
                existing_articles.sort(key=lambda item: item["_order"])
                target = existing_articles[0]
                for duplicate in existing_articles[1:]:
                    target["keys"] = sorted(
                        set(target["keys"]) | set(duplicate["keys"])
                    )
                    target["watches"] = sorted(
                        set(target["watches"]) | set(duplicate["watches"]),
                        key=str.casefold,
                    )
                    target["_suppressed"] = (
                        target.get("_suppressed", False)
                        or duplicate.get("_suppressed", False)
                    )
                    duplicate["_suppressed"] = True
                    for alias in duplicate["keys"]:
                        by_alias[alias] = target
                target["keys"] = sorted(set(target["keys"]) | key_set)
                if watch["name"] not in target["watches"]:
                    target["watches"].append(watch["name"])
                if key_set & seen_keys:
                    target["_suppressed"] = True
                for key in target["keys"]:
                    by_alias[key] = target
                continue
            if key_set & seen_keys:
                continue
            article["watches"] = [watch["name"]]
            article["_suppressed"] = False
            article["_order"] = len(collected)
            collected.append(article)
            for key in keys:
                by_alias[key] = article
        watch_counts[watch["name"]] = matched

    articles = [
        article for article in collected if not article.get("_suppressed", False)
    ]
    for article in articles:
        article["watches"].sort(key=str.casefold)
    articles.sort(key=lambda item: item["title"].casefold())
    articles.sort(key=lambda item: item["published"], reverse=True)
    return articles, watch_counts, discovered_keys


def escape_markdown_text(value):
    normalized = " ".join(value.split())
    return re.sub(r"([\\`*_\[\]{}()#+\-.!|<>~])", r"\\\1", normalized)


def markdown_url(value):
    encoded = quote(
        value,
        safe=":/?#[]@!$&'()*+,;=%-._~",
    )
    return "<{}>".format(encoded)


def render_report(generated_at, start, end, articles, watch_counts):
    lines = [
        "# Company News Change Report",
        "",
        "Generated at: {}".format(generated_at),
        "Window: {} to {}".format(format_timestamp(start), format_timestamp(end)),
        "",
    ]
    if not articles:
        lines.append("No new matching articles.")
    for article in articles:
        lines.append(
            "- [{}]({})".format(
                escape_markdown_text(article["title"]),
                markdown_url(article["url"]),
            )
        )
        lines.append("  - Published: {}".format(article["published"]))
        lines.append(
            "  - Watches: {}".format(
                ", ".join(escape_markdown_text(name) for name in article["watches"])
            )
        )
        if article["description"]:
            lines.append("  - {}".format(escape_markdown_text(article["description"])))

    structured = {
        "generated_at": generated_at,
        "window": {
            "start_date": format_timestamp(start),
            "end_date": format_timestamp(end),
        },
        "watch_match_counts": watch_counts,
        "new_articles": [
            {
                key: value
                for key, value in article.items()
                if key not in {"keys", "_suppressed", "_order"}
            }
            for article in articles
        ],
    }
    return "\n".join(lines) + "\n", structured


def main():
    args = parse_args()
    try:
        watches = load_watchlist(args.watchlist)
        fixture = load_json(args.fixture) if args.fixture else None
        start, end = resolve_window(args, fixture)
        generated_at = resolve_generated_at(args, fixture)
        responses = {}
        for watch in watches:
            responses[watch["name"]] = (
                fixture_response(fixture, watch)
                if fixture
                else fetch_live_response(watch, start, end, args.page_size)
            )
        seen_keys = load_state(args.state_file)
        articles, watch_counts, discovered_keys = collect_articles(
            watches,
            responses,
            start,
            end,
            seen_keys,
        )
        markdown, structured = render_report(
            generated_at,
            start,
            end,
            articles,
            watch_counts,
        )
    except (OSError, ValueError, json.JSONDecodeError, requests.RequestException) as exc:
        raise SystemExit("error: {}".format(exc))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "report.md").write_text(markdown, encoding="utf-8")
    (args.output_dir / "report.json").write_text(
        json.dumps(structured, indent=2) + "\n",
        encoding="utf-8",
    )
    args.state_file.parent.mkdir(parents=True, exist_ok=True)
    args.state_file.write_text(
        json.dumps(
            {"seen_article_keys": sorted(seen_keys | discovered_keys)},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Wrote {}".format(args.output_dir))


if __name__ == "__main__":
    main()
