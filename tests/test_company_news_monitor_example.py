import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


EXAMPLE = Path("examples/company_news_monitor/monitor.py")
WATCHLIST = Path("examples/company_news_monitor/watchlist.json")
FIXTURE = Path("examples/company_news_monitor/fixtures/search_responses.json")


def load_example_module():
    spec = importlib.util.spec_from_file_location("company_news_monitor", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_fixture(tmp_path, state_file=None):
    state_file = state_file or tmp_path / "state.json"
    output_dir = tmp_path / "output"
    result = subprocess.run(
        [
            sys.executable,
            str(EXAMPLE),
            "--watchlist",
            str(WATCHLIST),
            "--fixture",
            str(FIXTURE),
            "--state-file",
            str(state_file),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    return result, output_dir, state_file


def test_checked_in_fixture_runs_without_network_or_credentials(tmp_path):
    env_key = os.environ.pop("CURRENTS_API_KEY", None)
    try:
        result, output_dir, state_file = run_fixture(tmp_path)
    finally:
        if env_key is not None:
            os.environ["CURRENTS_API_KEY"] = env_key

    assert result.returncode == 0, result.stderr
    report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
    markdown = (output_dir / "report.md").read_text(encoding="utf-8")
    assert len(report["new_articles"]) == 3
    assert "https://example.com/business/northstar-pilot-line" in markdown
    assert "2026-08-05T07:30:00Z" in markdown
    assert state_file.exists()


def test_watchlist_parser_rejects_duplicate_names(tmp_path):
    module = load_example_module()
    path = tmp_path / "watchlist.json"
    path.write_text(
        json.dumps(
            {
                "watches": [
                    {"name": "Same", "keywords": "one", "language": "en"},
                    {"name": "Same", "keywords": "two", "language": "en"},
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unique"):
        module.load_watchlist(path)


@pytest.mark.parametrize(
    "watch",
    [
        {"name": "Missing search", "language": "en"},
        {
            "name": "Ambiguous search",
            "keywords": "Northstar Battery",
            "query": '"Northstar Battery" OR "Atlas Storage"',
            "language": "en",
        },
    ],
)
def test_watchlist_parser_requires_exactly_one_search_field(tmp_path, watch):
    module = load_example_module()
    path = tmp_path / "watchlist.json"
    path.write_text(json.dumps({"watches": [watch]}), encoding="utf-8")

    with pytest.raises(ValueError, match="exactly one of keywords or query"):
        module.load_watchlist(path)


def test_date_boundaries_are_inclusive_and_outside_articles_are_removed():
    module = load_example_module()
    start = datetime(2026, 8, 4, tzinfo=timezone.utc)
    end = datetime(2026, 8, 5, tzinfo=timezone.utc)
    watches = [
        {"name": "Window", "keywords": "test", "language": "en", "domain": None}
    ]
    responses = {
        "Window": {
            "status": "ok",
            "news": [
                {
                    "id": "start",
                    "title": "At start",
                    "url": "https://example.com/start",
                    "published": "2026-08-04T00:00:00Z",
                },
                {
                    "id": "end",
                    "title": "At end",
                    "url": "https://example.com/end",
                    "published": "2026-08-05T00:00:00Z",
                },
                {
                    "id": "before",
                    "title": "Before",
                    "url": "https://example.com/before",
                    "published": "2026-08-03T23:59:59Z",
                },
                {
                    "id": "after",
                    "title": "After",
                    "url": "https://example.com/after",
                    "published": "2026-08-05T00:00:01Z",
                },
            ],
        }
    }

    articles, counts, keys = module.collect_articles(
        watches, responses, start, end, set()
    )

    assert {article["title"] for article in articles} == {"At start", "At end"}
    assert counts == {"Window": 2}
    assert keys == {
        "id:start",
        "url:https://example.com/start",
        "id:end",
        "url:https://example.com/end",
    }


def test_same_url_with_optional_id_drift_is_reported_once():
    module = load_example_module()
    start = datetime(2026, 8, 4, tzinfo=timezone.utc)
    end = datetime(2026, 8, 5, tzinfo=timezone.utc)
    watches = [
        {"name": "Company", "keywords": "test", "language": "en", "domain": None},
        {"name": "Policy", "keywords": "test", "language": "en", "domain": None},
    ]
    shared_with_id = {
        "id": "shared",
        "title": "Shared result",
        "url": "https://example.com/shared",
        "published": "2026-08-04T12:00:00Z",
    }
    shared_without_id = {
        key: value for key, value in shared_with_id.items() if key != "id"
    }
    responses = {
        "Company": {"status": "ok", "news": [shared_without_id]},
        "Policy": {"status": "ok", "news": [shared_with_id]},
    }

    articles, _, _ = module.collect_articles(watches, responses, start, end, set())

    assert len(articles) == 1
    assert articles[0]["watches"] == ["Company", "Policy"]


def test_same_id_with_url_variants_is_reported_once():
    module = load_example_module()
    start = datetime(2026, 8, 4, tzinfo=timezone.utc)
    end = datetime(2026, 8, 5, tzinfo=timezone.utc)
    watches = [
        {"name": "Company", "keywords": "test", "language": "en", "domain": None},
        {"name": "Policy", "keywords": "test", "language": "en", "domain": None},
    ]
    responses = {
        "Company": {
            "status": "ok",
            "news": [
                {
                    "id": "shared",
                    "title": "Shared result",
                    "url": "https://example.com/shared",
                    "published": "2026-08-04T12:00:00Z",
                }
            ],
        },
        "Policy": {
            "status": "ok",
            "news": [
                {
                    "id": "shared",
                    "title": "Shared result",
                    "url": "https://example.com/shared?ref=feed",
                    "published": "2026-08-04T12:00:00Z",
                }
            ],
        },
    }

    articles, _, keys = module.collect_articles(
        watches, responses, start, end, set()
    )

    assert len(articles) == 1
    assert articles[0]["watches"] == ["Company", "Policy"]
    assert keys == {
        "id:shared",
        "url:https://example.com/shared",
        "url:https://example.com/shared?ref=feed",
    }


def test_transitive_alias_bridge_keeps_first_article_deterministically():
    module = load_example_module()
    start = datetime(2026, 8, 4, tzinfo=timezone.utc)
    end = datetime(2026, 8, 5, tzinfo=timezone.utc)
    watches = [
        {"name": "First", "keywords": "test", "language": "en", "domain": None},
        {"name": "Second", "keywords": "test", "language": "en", "domain": None},
        {"name": "Bridge", "keywords": "test", "language": "en", "domain": None},
    ]
    responses = {
        "First": {
            "status": "ok",
            "news": [
                {
                    "title": "First record",
                    "url": "https://example.com/a",
                    "published": "2026-08-04T12:00:00Z",
                }
            ],
        },
        "Second": {
            "status": "ok",
            "news": [
                {
                    "id": "shared",
                    "title": "Second record",
                    "url": "https://example.com/b",
                    "published": "2026-08-04T12:00:00Z",
                }
            ],
        },
        "Bridge": {
            "status": "ok",
            "news": [
                {
                    "id": "shared",
                    "title": "Bridge record",
                    "url": "https://example.com/a",
                    "published": "2026-08-04T12:00:00Z",
                }
            ],
        },
    }

    articles, _, _ = module.collect_articles(watches, responses, start, end, set())

    assert len(articles) == 1
    assert articles[0]["title"] == "First record"
    assert articles[0]["url"] == "https://example.com/a"
    assert articles[0]["watches"] == ["Bridge", "First", "Second"]


def test_reverse_transitive_alias_bridge_keeps_first_article():
    module = load_example_module()
    start = datetime(2026, 8, 4, tzinfo=timezone.utc)
    end = datetime(2026, 8, 5, tzinfo=timezone.utc)
    watches = [
        {"name": "First", "keywords": "test", "language": "en", "domain": None},
        {"name": "Second", "keywords": "test", "language": "en", "domain": None},
        {"name": "Bridge", "keywords": "test", "language": "en", "domain": None},
    ]
    responses = {
        "First": {
            "status": "ok",
            "news": [
                {
                    "id": "shared",
                    "title": "First record",
                    "url": "https://example.com/a",
                    "published": "2026-08-04T12:00:00Z",
                }
            ],
        },
        "Second": {
            "status": "ok",
            "news": [
                {
                    "title": "Second record",
                    "url": "https://example.com/b",
                    "published": "2026-08-04T12:00:00Z",
                }
            ],
        },
        "Bridge": {
            "status": "ok",
            "news": [
                {
                    "id": "shared",
                    "title": "Bridge record",
                    "url": "https://example.com/b",
                    "published": "2026-08-04T12:00:00Z",
                }
            ],
        },
    }

    articles, _, _ = module.collect_articles(watches, responses, start, end, set())

    assert len(articles) == 1
    assert articles[0]["title"] == "First record"
    assert articles[0]["url"] == "https://example.com/a"
    assert articles[0]["watches"] == ["Bridge", "First", "Second"]


def test_state_suppresses_same_url_when_id_appears_later():
    module = load_example_module()
    start = datetime(2026, 8, 4, tzinfo=timezone.utc)
    end = datetime(2026, 8, 5, tzinfo=timezone.utc)
    watches = [
        {"name": "Company", "keywords": "test", "language": "en", "domain": None}
    ]
    response_without_id = {
        "Company": {
            "status": "ok",
            "news": [
                {
                    "title": "Same result",
                    "url": "https://example.com/same",
                    "published": "2026-08-04T12:00:00Z",
                }
            ],
        }
    }
    first_articles, _, first_keys = module.collect_articles(
        watches, response_without_id, start, end, set()
    )
    assert len(first_articles) == 1

    response_with_id = {
        "Company": {
            "status": "ok",
            "news": [
                {
                    "id": "same",
                    "title": "Same result",
                    "url": "https://example.com/same",
                    "published": "2026-08-04T12:00:00Z",
                }
            ],
        }
    }
    later_articles, _, later_keys = module.collect_articles(
        watches, response_with_id, start, end, first_keys
    )

    assert later_articles == []
    assert later_keys == {
        "id:same",
        "url:https://example.com/same",
    }


def test_second_run_uses_state_and_reports_no_new_articles(tmp_path):
    first, _, state_file = run_fixture(tmp_path / "first", tmp_path / "state.json")
    assert first.returncode == 0, first.stderr

    second_dir = tmp_path / "second"
    second, output_dir, _ = run_fixture(second_dir, state_file)

    assert second.returncode == 0, second.stderr
    report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
    assert report["new_articles"] == []
    assert "No new matching articles." in (
        output_dir / "report.md"
    ).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("search_field", "search_value"),
    [
        ("keywords", '"grid storage" regulation'),
        ("query", '"Northstar Battery" OR "Atlas Storage"'),
    ],
)
def test_live_mode_sends_matching_documented_search_parameter(
    monkeypatch, search_field, search_value
):
    module = load_example_module()
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "ok", "news": []}

    def fake_get(url, headers, params, timeout):
        captured.update(
            {"url": url, "headers": headers, "params": params, "timeout": timeout}
        )
        return FakeResponse()

    monkeypatch.setenv("CURRENTS_API_KEY", "test-key")
    monkeypatch.setattr(module.requests, "get", fake_get)
    watch = {
        "name": "Policy",
        "language": "en",
        "domain": "example.com",
        search_field: search_value,
    }
    start = datetime(2026, 8, 4, 9, tzinfo=timezone.utc)
    end = datetime(2026, 8, 5, 9, tzinfo=timezone.utc)

    payload = module.fetch_live_response(watch, start, end, 20)

    assert payload == {"status": "ok", "news": []}
    assert captured["url"] == module.SEARCH_URL
    assert captured["headers"] == {"Authorization": "Bearer test-key"}
    assert captured["params"] == {
        search_field: search_value,
        "language": "en",
        "start_date": "2026-08-04T09:00:00Z",
        "end_date": "2026-08-05T09:00:00Z",
        "page_number": 1,
        "page_size": 20,
        "domain": "example.com",
    }
    assert captured["timeout"] == 20


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "ftp://example.com/report",
        "https://example.com/report\n- injected",
    ],
)
def test_article_url_requires_safe_http_or_https_url(url):
    module = load_example_module()
    start = datetime(2026, 8, 4, tzinfo=timezone.utc)
    end = datetime(2026, 8, 5, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="HTTP or HTTPS"):
        module.normalize_article(
            {
                "title": "Unsafe URL",
                "url": url,
                "published": "2026-08-04T12:00:00Z",
            },
            start,
            end,
        )


def test_report_escapes_hostile_publisher_metadata():
    module = load_example_module()
    start = datetime(2026, 8, 4, tzinfo=timezone.utc)
    end = datetime(2026, 8, 5, tzinfo=timezone.utc)
    articles = [
        {
            "keys": ["url:https://example.com/report_(final)"],
            "title": "[Trusted](https://attacker.example) <script>",
            "description": "First line\n- [Injected](https://attacker.example)\n<img>",
            "url": "https://example.com/report_(final)",
            "published": "2026-08-04T12:00:00Z",
            "watches": ["Company"],
        }
    ]

    markdown, _ = module.render_report(
        "2026-08-05T09:00:00Z",
        start,
        end,
        articles,
        {"Company": 1},
    )

    assert "[Trusted](https://attacker.example)" not in markdown
    assert "\n- [Injected]" not in markdown
    assert "<script>" not in markdown
    assert "<img>" not in markdown
    assert (
        r"\[Trusted\]\(https://attacker\.example\) \<script\>"
        in markdown
    )
    assert (
        r"First line \- \[Injected\]\(https://attacker\.example\) \<img\>"
        in markdown
    )
    assert "(<https://example.com/report_(final)>)" in markdown


def test_report_output_retains_every_url_and_published_timestamp(tmp_path):
    result, output_dir, _ = run_fixture(tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))

    assert all(article["url"] for article in report["new_articles"])
    assert all(article["published"] for article in report["new_articles"])
    markdown = (output_dir / "report.md").read_text(encoding="utf-8")
    for article in report["new_articles"]:
        assert article["url"] in markdown
        assert article["published"] in markdown
