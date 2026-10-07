# Repository tracking

This document tracks current monitor observability and selected workflow variables. Historical round documents remain under `docs/` and should not be used as current configuration instructions.

## Twitter V3

| Category | Variables |
| --- | --- |
| Inputs | `ACCOUNTS`, `DISCORD_WEBHOOK_URL`, per-account `WEBHOOK_*`, optional `NITTER_RSS_TOKEN` |
| Cache | `MAX_CACHE_SIZE_PER_ACCOUNT`, `MAX_CACHE_SIZE_TOTAL` |
| Media healing | `MEDIA_HEAL`, `MEDIA_HEAL_SCOPE`, `MEDIA_HEAL_DELAY_SECONDS`, `MEDIA_HEAL_ATTEMPTS` |

`MEDIA_HEAL_SCOPE=video` is the default. `off` disables the pass; `on` or
`all` includes additional media types. The workflow-only run summary reports
actual runtime, aggregate feed entries, terminal feed failures, empty accounts,
post counters, media-heal diagnostics, and cache status.

## Reddit V3

Reddit's workflow-only summary reports runtime, feed and delivery counters,
proxy warmup health, quality-upgrade diagnostics, fallback labels, listing/retry
counters, and the cache commit/push result. It does not alter provider
selection, posting, scheduling, cache policy, or media requests.

The removed content-advisory settings are not current configuration:
`NSFW_ALLOWLIST`, `NSFW_FAIL_OPEN`, `NSFW_REQUIRE_SUBREDDIT`, and
`NSFW_PAGE_FALLBACK` must not be added back to active code or workflows.
