"""Shared helpers for the shipped Currents API examples."""

import re


_MARKDOWN_ESCAPES = re.compile(r"([\\`*_\[\]()<>#!|{}])")


def escape_markdown_text(value):
    """Escape Markdown-significant characters in publisher-controlled text."""
    return _MARKDOWN_ESCAPES.sub(r"\\\1", str(value))


def safe_markdown_url(url, allowed_schemes=("http", "https")):
    """Return a URL safe to embed in Markdown, or ``None`` if unsafe.

    Rejects empty values, non-string values, unknown/unsafe schemes
    (e.g. ``javascript:``), and whitespace/control characters that could
    break out of a Markdown link target.
    """
    if not isinstance(url, str):
        return None
    candidate = url.strip()
    if not candidate:
        return None
    if any(ch.isspace() or ord(ch) < 0x20 for ch in candidate):
        return None
    match = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*):", candidate)
    if not match or match.group(1).lower() not in allowed_schemes:
        return None
    # Escape parentheses so the URL cannot break out of [..](..) syntax.
    return candidate.replace("(", "%28").replace(")", "%29")
