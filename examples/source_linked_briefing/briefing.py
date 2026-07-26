#!/usr/bin/env python3
"""Generate a source-linked news briefing from Currents Search API data."""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, help="Read a saved Search API response.")
    parser.add_argument("--keywords", default="artificial intelligence")
    parser.add_argument("--language", default="en")
    parser.add_argument("--output-dir", type=Path, default=Path("briefing-output"))
    parser.add_argument(
        "--generated-at",
        help="Set the output timestamp for a custom fixture.",
    )
    return parser.parse_args()


def normalize_article(article):
    return {
        "title": article.get("title") or "Untitled",
        "description": article.get("description") or "",
        "url": article.get("url") or "",
        "published": article.get("published") or "",
        "language": article.get("language") or "",
        "category": article.get("category") or [],
    }


def load_fixture(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_live_response(keywords, language):
    api_key = os.environ.get("CURRENTS_API_KEY")
    if not api_key:
        raise ValueError("CURRENTS_API_KEY is required for live mode")

    from currentsapi import CurrentsAPI

    return CurrentsAPI(api_key=api_key).search(
        keywords=keywords,
        language=language,
    )


def validate_response(response):
    if not isinstance(response, dict):
        raise ValueError("Search API response must be an object")
    if response.get("status") != "ok":
        raise ValueError("Search API response status must be 'ok'")
    if not isinstance(response.get("news"), list):
        raise ValueError("Search API response news must be a list")
    if any(not isinstance(article, dict) for article in response["news"]):
        raise ValueError("Every news item must be an object")
    for article in response["news"]:
        for field in ("title", "description", "url", "published", "language"):
            value = article.get(field)
            if value is not None and not isinstance(value, str):
                raise ValueError("news item {} must be a string".format(field))
        category = article.get("category")
        if category is not None and (
            not isinstance(category, list)
            or any(not isinstance(item, str) for item in category)
        ):
            raise ValueError("news item category must be a list of strings")


def resolve_generated_at(args, response):
    if args.generated_at:
        return args.generated_at
    if args.fixture:
        fixture_time = response.get("_fixture_generated_at")
        if not isinstance(fixture_time, str) or not fixture_time:
            raise ValueError(
                "Fixture must include _fixture_generated_at or use --generated-at"
            )
        return fixture_time
    return datetime.now(timezone.utc).isoformat()


def build_output(response, generated_at):
    validate_response(response)
    articles = [normalize_article(article) for article in response["news"]]
    articles.sort(key=lambda article: article["title"].casefold())
    articles.sort(key=lambda article: article["published"], reverse=True)
    lines = ["# Source-Linked News Briefing", "", "Generated at: {}".format(generated_at), ""]
    for article in articles:
        title = article["title"]
        url = article["url"]
        lines.append("- {} - <{}>".format(title, url) if url else "- {}".format(title))
        if article["published"]:
            lines.append("  - Published: {}".format(article["published"]))
        if article["description"]:
            lines.append("  - {}".format(article["description"]))
    return "\n".join(lines) + "\n", {
        "generated_at": generated_at,
        "articles": articles,
    }


def main():
    args = parse_args()

    try:
        response = (
            load_fixture(args.fixture)
            if args.fixture
            else load_live_response(args.keywords, args.language)
        )
        validate_response(response)
        generated_at = resolve_generated_at(args, response)
        markdown, structured = build_output(response, generated_at)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit("error: {}".format(exc))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "briefing.md").write_text(markdown, encoding="utf-8")
    (args.output_dir / "briefing.json").write_text(
        json.dumps(structured, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Wrote {}".format(args.output_dir))


if __name__ == "__main__":
    main()
