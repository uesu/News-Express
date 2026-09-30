# Changelog

Release-level changes for News Express. The [README](README.md) keeps the detailed
round-by-round implementation notes and operating guidance.

## 2026-09-30 — Reddit V3 round 38e

### Added

- Token-authenticated public Reddit RSS `/new` listings are now the primary
  negative-space signal for native moderator-queue posts with no AutoModerator
  comment.
- Exact RSS `pubDate` span parsing, including malformed/future-date fail-open
  handling, and URL-encoded reuse of the existing `REDDIT_FEED_TOKEN`.
- Offline smoke coverage for RSS IDs, CDATA dates, deterministic age parsing,
  token URL construction, per-run listing caching, and the HTML fallback.

### Changed

- The round-37/38d HTML listing chain remains the fallback when RSS is empty,
  rate-limited, unavailable, or not parseable.
- The queue gate continues to fail open whenever visibility or age evidence is
  incomplete. No new secret, repository Variable, workflow input, or dependency
  was introduced.
- Privacy policy, Terms of Service, README, CI smoke-test documentation, and
  release-level changelog entries now describe the RSS-backed safety path.

### Verification

- `python -m compileall -q "testing area" tests`
- `python tests/test_smoke.py`
- `git diff --check`
