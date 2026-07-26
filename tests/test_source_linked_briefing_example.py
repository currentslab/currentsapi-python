import json
import os
import subprocess
import sys
from pathlib import Path


EXAMPLE = Path("examples/source_linked_briefing/briefing.py")
CHECKED_IN_FIXTURE = Path(
    "examples/source_linked_briefing/fixtures/search_response.json"
)


def test_fixture_mode_writes_source_linked_markdown_and_json(tmp_path):
    fixture = tmp_path / "search-response.json"
    fixture.write_text(
        json.dumps(
            {
                "status": "ok",
                "news": [
                    {
                        "title": "Grid storage project reaches commissioning",
                        "description": "The operator started final commissioning.",
                        "url": "https://news.example/grid-storage",
                        "published": "2026-07-24T09:30:00Z",
                        "language": "en",
                        "category": ["business"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"

    result = subprocess.run(
        [
            sys.executable,
            str(EXAMPLE),
            "--fixture",
            str(fixture),
            "--output-dir",
            str(output_dir),
            "--generated-at",
            "2026-07-25T00:00:00Z",
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    markdown = (output_dir / "briefing.md").read_text(encoding="utf-8")
    structured = json.loads((output_dir / "briefing.json").read_text(encoding="utf-8"))
    assert "https://news.example/grid-storage" in markdown
    assert "2026-07-24T09:30:00Z" in markdown
    assert structured["articles"][0]["url"] == "https://news.example/grid-storage"
    assert structured["articles"][0]["published"] == "2026-07-24T09:30:00Z"


def test_fixture_mode_orders_newest_articles_first(tmp_path):
    fixture = tmp_path / "search-response.json"
    fixture.write_text(
        json.dumps(
            {
                "status": "ok",
                "news": [
                    {
                        "title": "Earlier report",
                        "url": "https://news.example/earlier",
                        "published": "2026-07-23T09:30:00Z",
                    },
                    {
                        "title": "Latest report",
                        "url": "https://news.example/latest",
                        "published": "2026-07-25T09:30:00Z",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"

    result = subprocess.run(
        [
            sys.executable,
            str(EXAMPLE),
            "--fixture",
            str(fixture),
            "--output-dir",
            str(output_dir),
            "--generated-at",
            "2026-07-25T10:00:00Z",
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    structured = json.loads((output_dir / "briefing.json").read_text(encoding="utf-8"))
    assert [article["title"] for article in structured["articles"]] == [
        "Latest report",
        "Earlier report",
    ]


def test_fixture_mode_rejects_malformed_search_response(tmp_path):
    fixture = tmp_path / "search-response.json"
    fixture.write_text(
        json.dumps({"status": "ok", "news": {"unexpected": "object"}}),
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"

    result = subprocess.run(
        [
            sys.executable,
            str(EXAMPLE),
            "--fixture",
            str(fixture),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode != 0
    assert "news must be a list" in result.stderr
    assert not output_dir.exists()


def test_live_mode_requires_api_key(tmp_path):
    env = os.environ.copy()
    env.pop("CURRENTS_API_KEY", None)

    result = subprocess.run(
        [
            sys.executable,
            str(EXAMPLE),
            "--output-dir",
            str(tmp_path / "output"),
        ],
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    assert result.returncode != 0
    assert "CURRENTS_API_KEY is required for live mode" in result.stderr


def test_checked_in_fixture_runs_without_network_or_credentials(tmp_path):
    env = os.environ.copy()
    env.pop("CURRENTS_API_KEY", None)

    result = subprocess.run(
        [
            sys.executable,
            str(EXAMPLE),
            "--fixture",
            str(CHECKED_IN_FIXTURE),
            "--output-dir",
            str(tmp_path / "output"),
            "--generated-at",
            "2026-07-25T00:00:00Z",
        ],
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    markdown = (tmp_path / "output" / "briefing.md").read_text(encoding="utf-8")
    assert "Battery storage policy enters public consultation" in markdown
    assert "https://example.com/energy/storage-policy" in markdown


def test_live_mode_uses_the_sdk_search_result(tmp_path):
    fake_package = tmp_path / "fake-sdk" / "currentsapi"
    fake_package.mkdir(parents=True)
    (fake_package / "__init__.py").write_text(
        """
class CurrentsAPI:
    def __init__(self, api_key):
        assert api_key == "test-key"

    def search(self, keywords, language):
        assert keywords == "energy storage"
        assert language == "en"
        return {
            "status": "ok",
            "news": [{
                "title": "Live search result",
                "url": "https://news.example/live-result",
                "published": "2026-07-25T12:00:00Z"
            }]
        }
""".lstrip(),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["CURRENTS_API_KEY"] = "test-key"
    env["PYTHONPATH"] = str(tmp_path / "fake-sdk")
    output_dir = tmp_path / "output"

    result = subprocess.run(
        [
            sys.executable,
            str(EXAMPLE),
            "--keywords",
            "energy storage",
            "--language",
            "en",
            "--output-dir",
            str(output_dir),
            "--generated-at",
            "2026-07-25T13:00:00Z",
        ],
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    markdown = (output_dir / "briefing.md").read_text(encoding="utf-8")
    assert "Live search result" in markdown
    assert "https://news.example/live-result" in markdown
