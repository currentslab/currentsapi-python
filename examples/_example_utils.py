"""Shared helpers for the shipped Currents API examples."""

import re
from urllib.parse import urlsplit


_MARKDOWN_ESCAPES = re.compile(r"([\\`*_\[\]()<>#!|{}])")


def escape_markdown_text(value):
    """Escape Markdown-significant characters in publisher-controlled text."""
    return _MARKDOWN_ESCAPES.sub(r"\\\1", str(value))


def safe_markdown_url(url, allowed_schemes=("http", "https")):
    """Return a URL safe to embed in Markdown, or ``None`` if unsafe.

    Requires an explicit allowed scheme (default http/https) and a hostname;
    percent-encodes characters that could break out of ``[..](..)`` or
    ``<..>`` Markdown targets (parentheses, angle brackets, spaces,
    control characters).
    """
    if not isinstance(url, str):
        return None
    candidate = url.strip()
    if not candidate or any(ord(ch) < 0x20 for ch in candidate):
        return None
    parts = urlsplit(candidate)
    if parts.scheme.lower() not in allowed_schemes or not parts.netloc:
        return None
    if any(ch.isspace() for ch in candidate):
        return None
    return (
        candidate.replace("<", "%3C")
        .replace(">", "%3E")
        .replace("(", "%28")
        .replace(")", "%29")
        .replace(" ", "%20")
    )
