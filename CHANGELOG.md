# Changelog

## 0.1.2

### Fixed
- Restored compatibility with the declared `python-dateutil>=2.8.0` floor:
  the date-parse error handler no longer references `parser.ParserError`
  (introduced in dateutil 2.8.1).
- Non-JSON error responses (e.g. HTML gateway 502s) and non-object JSON
  error payloads now raise `CurrentsAPIError` instead of leaking
  `JSONDecodeError`/`AttributeError`. The exception now carries the real
  HTTP status code via its `status` property; the payload's `status` value
  is only used when no HTTP status is available.
- `search()` now rejects falsey invalid arguments (`keywords=0`, empty/
  whitespace keywords) instead of silently omitting them.
- Naive `datetime` inputs are rejected with a clear `ValueError` (they were
  silently labeled UTC before); `date` objects are now explicitly formatted
  as UTC midnight.
- `examples/source_linked_briefing` now escapes publisher-controlled
  Markdown text and validates URL schemes, matching the protection the
  company-monitor example already had (blocks `javascript:` link injection).

## 0.1.1

### Fixed
- `CurrentsAPIError.message` now falls back to the API's `msg` key (401
  responses carry `msg`, not `message`), and `str(exception)` returns the
  human-readable message instead of a raw dict repr.
- `CurrentsAPIError.status` now returns an `int` when the payload carries a
  numeric status string, so `e.status == 401` works as expected.
- Timezone-aware `datetime` inputs to `search()` are converted to UTC before
  formatting, instead of silently losing their offset while the string gains a
  misleading `Z` suffix.
- Unparsable date strings (e.g. `"2026-13-45"`) now raise `ValueError` with a
  clear message instead of leaking `dateutil.parser.ParserError`.

## 0.1.0

### Added
- Added `available_languages()`, `available_regions()`, and `available_category()` endpoint wrappers.
- Added `language` parameter support to `latest_news()`.
- Added GitHub Actions CI workflow.
- Added unit tests using `unittest.mock`.

### Changed
- Aligned `search()` parameters with the current documented API surface.
- Modernized packaging metadata: updated repository URL, classifiers, and dependency pins.
- Unified package version to `0.1.0` across `setup.py` and `currentsapi/__init__.py`.
- Single-sourced the version: `setup.py` now reads `__version__` from
  `currentsapi/__init__.py` instead of duplicating it.
- Replaced the deprecated `tests_require` argument with an `extras_require`
  `"dev"` extra (`pip install currentsapi[dev]`).
- Removed obsolete `setup.cfg`: the `description-file` metadata key is
  deprecated and the `universal` wheel flag is incorrect for a Python 3-only
  package.
- README now clarifies that the PyPI distribution name is `currentsapi`
  (matching the 0.0.1/0.0.2 releases), documents `CurrentsAPIError` handling,
  and states the supported Python versions.
- Updated README with current docs link and usage examples.

### Fixed
- Fixed `start_date` handling in `search()` which incorrectly referenced `end_date`.
- Renamed exception class to `CurrentsAPIError` with cleaner attribute access.

### Removed
- Removed unsupported `search()` parameters: `page_number`, `limit`, `has_image`, `has_description`.
- Removed the "subtly broken or buggy" disclaimer from the README.
