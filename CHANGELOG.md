# Changelog

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
