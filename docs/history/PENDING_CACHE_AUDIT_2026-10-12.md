# Reddit pending-cache and current-documentation audit — 2026-10-12

**Decision:** retain `pending_reddit.json` and all active pending-state code,
workflow persistence, and semantic cache-merge handling. This record documents a
scoped documentation/configuration correction; it does not authorize a runtime
change or a pending-cache deletion.

## Canonical and production findings

Canonical News-Express `main` was `777e0789b01ce9536ef91fb329503853f9acabba`.
The active `.github/workflows/reddit_monitor.yml` target is
`testing area/reddit_main_v3.py`. That engine loads and saves
`pending_reddit.json`, throttles retryable operational rechecks using
`PENDING_RECHECK_SECONDS` (default 1800 seconds), and records selected
liveness/removal/approval and media-readiness holds. Confirmed removed/deleted
archive entries follow a no-recheck path unless they reappear through RSS.
The Reddit workflow persists the cache, and
`.github/scripts/merge_monitor_caches.py` includes pending-dictionary merge
handling. Tests also exercise the pending cache and its operational holds.

The cache was an empty JSON object at audit time. That is current state, not
evidence that the file or code path is unused. The round-64 fresh-age and
pristine-listing checks remain stateless and do not write pending entries.

The live production repositories were `uesu/7jkxmy9nvbc` at
`6b2f1d38b39cb028c9582023abfe18cae4967ca1` and `uesu/wvkhabh2s22` at
`b9fe39ac92b55ea52d8cacffe929b29d4689649b`. Their active engine/workflow files
matched News-Express at audit time; their smaller tracked file sets omit the
development documentation/history by design. No production repository or cache
was modified by this News-Express PR. Both production `.env.example` copies
also omit `MEDIA_HEAL_SCOPE`; they need a separate documentation-only sync.
Neither production repository was edited on this branch.

## Current documentation/configuration corrections

- Mark Round 72 shipped, referencing merged PR #59.
- Add the missing Twitter `MEDIA_HEAL_SCOPE=video` example and document
  `video`, `on`/`all`, and `off` modes.
- Clarify that Twitter V3 inspects Discord's returned message and uses an
  in-memory, post-delivery repair queue for unresolved eligible media; it is
  distinct from Reddit's persistent operational pending cache.
- Clarify that Reddit's old settle-window, dedicated moderator-queue,
  duplicate-media/repost, and content-advisory gate families remain removed,
  while the active engine still uses pending state for selected operational
  rechecks. The stateless fresh-age and pristine-listing skips remain separate.
- Preserve historical round records; only Round 72's status line was corrected
  after canonical GitHub confirmed PR #59 merged.

## Preserved behavior and validation

No Reddit or Twitter runtime code, workflow persistence, cache-merge semantics,
secrets, schedules, cache contents, provider behavior, Discord payloads, or
retraction behavior changed. `pending_reddit.json`, `posted_reddit.json`,
`posted_tweets.json`, and `proxy_health.json` were not reset or edited.

Validation on a disposable snapshot of the updated tree:

```text
python -m compileall -q "testing area" tests        PASS
python tests/test_smoke.py                           PASS
python tests/test_reddit_signals.py                  PASS (96 checks)
git diff --check                                     PASS
```
