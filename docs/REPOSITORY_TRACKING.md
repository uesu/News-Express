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

Reddit's workflow-only summary is derived from a stable local
`reddit_run_result.json` record (plus `monitor.log` for per-candidate details)
and reports runtime, completion (`completed` true only after required work
including persistence; `normal`/`no-candidate`/`dry-run` completed vs
`failed`/`interrupted` incomplete; not by JSON write/`finally`), local
persistence (`unchanged`/`saved`/`failed`/`not-reached`/`skipped_dry_run`,
entered defaults to `failed`, confirmed no-change `unchanged`, confirmed
successful `saved`, never-ran `not-reached`) and repository persistence
(same set, observed commit/push, dry-run explicit; local save not conflated
with repository push; preparation/copying/recovery-reset/staging/commit/push
failures all `failed` and are covered in tests of the actual workflow shell
`bash -n` + mock `unchanged`/`saved`/`recovered`/`failed`), feed and
delivery counters, proxy warmup health/services, video quality mode
(`balanced` default, `highest`/`compatibility`), media resolved via provider,
final media endpoint/hosting category, final card media kind and tile count,
optional quality candidate result, whether validated base was retained,
terminal media fallback (proxy→native, distinct from feed and quality
fallback), heal queued/edit-performed/skipped-after-revalidation; it
sanitizes error messages (webhook/token/Auth redaction, bounded 500 chars,
preserves operation/type/category) and makes no extra network requests;
neither warmup, HTTP validation, player controls nor “chain complete” proves
audio inclusion and Embeddit remains video-only; production baselines #8982
(`1xbbdbs` video retained after EmbedEZ, 1 tile, 3 buttons, `8ace078`),
#8988 (`1xbby22` vxReddit image retained after Redlib enrichment failure)
and #8989 (`1xbc1mn` vxReddit 720p retained after EmbedEZ, heal skipped after
revalidation, `3b7d836`/`8ace078`-class pushes) are recorded as successful,
not defects. It does not alter provider selection, posting, scheduling,
cache policy, or media requests, and missing data is reported as
`unavailable`/`not-reached` (zero deliveries is not a failure; dry-run is
explicitly labelled).

The operational `pending_reddit.json` cache remains active. It records selected
liveness/removal/approval and media-readiness holds. Retryable holds use the
`PENDING_RECHECK_SECONDS` throttle (default 1800 seconds); confirmed
removed/deleted archive entries follow a no-recheck path unless they reappear
via RSS (provenance-aware reconsideration, still subject to removal checks;
archive/media presence is not proof of current visibility). The round-64
fresh-age hold remains stateless and does not create pending entries; the
companion pristine-listing gate was removed in the 2026-10-21 cleanup. The old
settle-window, dedicated moderator-queue, and duplicate-media/repost gates
remain removed, as does the round-67 content-advisory gate.

The removed content-advisory settings are not current configuration:
`NSFW_ALLOWLIST`, `NSFW_FAIL_OPEN`, `NSFW_REQUIRE_SUBREDDIT`, and
`NSFW_PAGE_FALLBACK` must not be added back to active code or workflows.
