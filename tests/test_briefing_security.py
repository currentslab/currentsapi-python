"""Security regression tests for the source-linked briefing example."""

import importlib.util
import sys
from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
sys.path.insert(0, str(EXAMPLES_DIR))

from _example_utils import escape_markdown_text, safe_markdown_url  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "briefing", EXAMPLES_DIR / "source_linked_briefing" / "briefing.py"
)
briefing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(briefing)


class TestSafeMarkdownUrl:
    def test_javascript_scheme_rejected(self):
        assert safe_markdown_url("javascript:alert(1)") is None

    def test_data_scheme_rejected(self):
        assert safe_markdown_url("data:text/html,<script>alert(1)</script>") is None

    def test_scheme_relative_rejected(self):
        assert safe_markdown_url("//attacker.example/x") is None

    def test_missing_netloc_rejected(self):
        assert safe_markdown_url("https://") is None

    def test_angle_brackets_percent_encoded(self):
        out = safe_markdown_url("https://example.com><script>x</script>")
        assert "<" not in out and ">" not in out
        assert out == "https://example.com%3E%3Cscript%3Ex%3C/script%3E"

    def test_parens_percent_encoded(self):
        assert safe_markdown_url("https://example.com/x(1)") == "https://example.com/x%281%29"

    def test_normal_url_unchanged(self):
        assert safe_markdown_url("https://example.com/a?b=1&c=2") == "https://example.com/a?b=1&c=2"

    def test_non_string_rejected(self):
        assert safe_markdown_url(None) is None
        assert safe_markdown_url(123) is None


class TestBriefingOutputSanitization:
    def test_hostile_title_cannot_form_link(self):
        art = {
            "title": "[click here](javascript:alert(1))",
            "description": "",
            "url": "",
            "published": "2026-01-01",
        }
        md, _ = briefing.build_output(
            {"status": "ok", "news": [art]}, generated_at="2026-01-01T00:00:00Z"
        )
        assert "](javascript:" not in md

    def test_hostile_url_cannot_break_out(self):
        art = {
            "title": "t",
            "description": "",
            "url": "https://example.com><script>location.href='//attacker.example'</script>",
            "published": "2026-01-01",
        }
        md, _ = briefing.build_output(
            {"status": "ok", "news": [art]}, generated_at="2026-01-01T00:00:00Z"
        )
        assert "<script>" not in md

    def test_clean_url_rendered(self):
        art = {
            "title": "t",
            "description": "",
            "url": "https://example.com/story",
            "published": "2026-01-01",
        }
        md, _ = briefing.build_output(
            {"status": "ok", "news": [art]}, generated_at="2026-01-01T00:00:00Z"
        )
        assert "<https://example.com/story>" in md

    def test_escape_markdown_text_neutralizes_link_syntax(self):
        escaped = escape_markdown_text("[x](javascript:alert(1))")
        assert "\\[x\\]" in escaped
        assert "\\(javascript:" in escaped
