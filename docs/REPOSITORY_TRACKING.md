# Repository tracking

This document tracks current monitor observability and selected workflow variables. Historical round documents remain under `docs/history/` and should not be used as current configuration instructions.

## Twitter V3

| Category | Variables |
| --- | --- |
| Inputs | `ACCOUNTS`, `DISCORD_WEBHOOK_URL`, per-account `WEBHOOK_*`, optional `NITTER_RSS_TOKEN` |
| Cache | `MAX_CACHE_SIZE_PER_ACCOUNT`, `MAX_CACHE_SIZE_TOTAL` |
| Media healing | `MEDIA_HEAL`, `MEDIA_HEAL_SCOPE`, `MEDIA_HEAL_DELAY_SECONDS`, `MEDIA_HEAL_ATTEMPTS` |

`MEDIA_HEAL_SCOPE=video` is the default. `off` disables the pass; `on` or
`all` includes additional media types. Twitter V3 inspects Discord's returned
message after its `wait=true` post; unresolved eligible media enters an
in-memory message repair queue that runs after the posting loop. Healthy media
is a no-op: it is posted immediately, with no revalidation request and no
delay, and neither the tweet-data provider that answered nor the gallery's
ordering adds a repair. This is distinct from Reddit's persisted candidate recheck state;
Twitter's heal queue is not stored in `pending_reddit.json` or `posted_tweets.json`.
The workflow-only run summary reports actual runtime, aggregate feed entries,
terminal feed failures, empty accounts, post counters, and cache status.

## Reddit V3

Reddit's workflow-only summary reports runtime, feed and delivery counters,
proxy warmup health, quality-upgrade diagnostics, fallback labels, listing/retry
counters, and the cache commit/push result. It does not alter provider
selection, posting, scheduling, cache policy, or media requests.

The operational `pending_reddit.json` cache remains active. It records selected
liveness/removal/approval and media-readiness holds. Retryable holds use the
`PENDING_RECHECK_SECONDS` throttle (default 1800 seconds); confirmed
removed/deleted archive entries follow a no-recheck path unless they reappear
via RSS. The round-64 fresh-age and pristine-listing skips remain stateless and
do not create pending entries. The old settle-window, dedicated moderator-
queue, and duplicate-media/repost gates remain removed, as does the round-67
content-advisory gate.

The removed content-advisory settings are not current configuration:
`NSFW_ALLOWLIST`, `NSFW_FAIL_OPEN`, `NSFW_REQUIRE_SUBREDDIT`, and
`NSFW_PAGE_FALLBACK` must not be added back to active code or workflows.
