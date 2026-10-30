# Round 98 (2026-10-30) — stale archive snapshots no longer strand live posts

## Provenance

The operator asked, per subreddit, which posts were missing from Discord and why. The
answer was 23 pending keys, and the reasons split the problem in two:

| Reason class | Keys | Re-checked? |
|---|---|---|
| `removal_notice` (live page / queue text) | 13 | **No** — by design; returns only via RSS |
| `liveness_removed` (round-95 archive probe) | 9 | Only while a source still lists the post |
| `not_live` (live-source gate) | 1 | Only while a source still lists the post |

Two of those behaviours were wrong in production the same day:

1. **A snapshot was treated as the present tense.** Six `r/HonkaiStarRail_leaks`
   "Official" posts (Fun with Aha, Affinitive Eidolon, Star Lotto, Brief on 4.7 Program,
   4.7 Bonuses, 4.7 Trailer) and `Genshin_Impact_Leaks_1xjh1mq` were held as
   `liveness_removed` for 2–4 h while reddit.com's own listing carried them, with the
   user's screenshots showing votes and comments. They entered through the combined feed,
   i.e. Reddit was listing them; the archive row still carried `removed_by_category` from
   the moment it was captured (queued post, approved later).
2. **A hold that no source lists is never re-read.** `HonkaiStarRail_leaks_1xjdkwf`
   (archive-sourced) sat with `last_checked` frozen at 12:10Z: it had dropped out of both
   the feed and the archive sweep, so nothing in the pipeline looked at it again.

`FRESH_HOLD_SECONDS` is a third, separate matter: the engine default is 30 s, the
operator Variable is 60 s. It only defers a candidate to the next tick and never writes
the cache, so it cannot explain any of the above; the operator is changing it to 30 s in
repo settings (this round does not touch it).

## What Round 98 changes

### 1. Stale-snapshot override (engine)

A snapshot `removed` verdict is overridden only when **all** of these hold:

- the state came from a **snapshot** source (`arctic-entry`, `arctic-lookup`) — a
  `post-json` verdict is a live read (FULL MODE) and stays authoritative;
- the post is in **Reddit's own listing this run** — the combined feed, or a reddit.com
  per-subreddit feed. `collect()` now takes `provenance=`; redlib/eddrit proxies and the
  archive are never `reddit-native`;
- it has been listed there for `STALE_SNAPSHOT_TICKS` (3) `runs in a row` — ~15 min at
  the 5-minute cron. `_bump_native_streak()` increments on every run the key is listed
  and resets to 0 on the first run it is not.

Why it is safe: a post removed by a moderator leaves reddit.com's own `/new` listing
within minutes, so it cannot build a 3-run streak; a proxy-served ghost never counts at
all; and one missed tick resets the count. The override is reported as
`Stale-snapshot overrides: N` with the key, the archive reason and the streak length.

### 2. Held-post reclaim (engine)

`_reclaim_due()` picks held keys that are **not** in this run's candidate set, oldest
`first_seen` first, at most `RECLAIM_MAX_PER_RUN` (5), and only when:

- the reason is retryable: `liveness_removed`, `liveness_unverified`, `not_live`,
  `pending approval`, `sources_down`. **`removal_notice` is excluded** — it is evidence
  read from a live page and must return via RSS, as before;
- `last_checked` is at least `PENDING_RECHECK_SECONDS` (300 s) old;
- `published_ts` is inside the 48 h window.

Those IDs are read in **one** batched `GET /api/posts/ids?ids=a,b,c` request
(`fetch_arctic_posts_by_ids`). A clean record is appended to `new_posts` as an
`_ArcticEntry`, so it runs the **unchanged** pipeline: double dedup, round-18 removal
text filter, round-20 live-source gate, round-95 probe, fresh hold, flood cap. A record
that still reports removal refreshes `last_checked` and keeps its original reason (a
`removal_notice` is never downgraded into a retry loop). The archive erroring is a no-op.

## Expected effect on the 23 keys in pending at 15:41Z

| Sub | Pending | Reclaimable by round 98 |
|---|---|---|
| Genshin_Impact_Leaks | 5 | `1xjh1mq` already reaches the probe every tick (feed-visible → override path); 4 `removal_notice` stay held |
| HonkaiStarRail_leaks | 10 | 6 rss keys ride the override path; `1xjdkwf` rides the reclaim path; 3 `removal_notice` stay held |
| WutheringWavesLeaks | 5 | `1xjdfwl` rides the override path; 4 `removal_notice` stay held |
| Zenlesszonezeroleaks_ | 2 | none — both `removal_notice` |
| AnantaLeaks | 1 | `1xjdnaq` rides the reclaim path |
| HonkaiNexusAnimaLeaks | 0 | — |

Full per-key table (15:41:35Z):

| Key | Reason | Source | Age | Last re-checked |
|---|---|---|---|---|
| `AnantaLeaks_1xjdnaq` | not_live | arctic | 3.5 h | 2 min |
| `Genshin_Impact_Leaks_1xi4zoq` | removal_notice | arctic | 39.6 h | 2372 min |
| `Genshin_Impact_Leaks_1xjcbmd` | removal_notice | arctic | 4.6 h | 277 min |
| `Genshin_Impact_Leaks_1xjdo12` | removal_notice | arctic | 3.5 h | 72 min |
| `Genshin_Impact_Leaks_1xjgpew` | removal_notice | arctic | 1.3 h | 77 min |
| `Genshin_Impact_Leaks_1xjh1mq` | liveness_removed | rss | 1.1 h | 2 min |
| `HonkaiStarRail_leaks_1xjdd2p` | removal_notice | arctic | 3.7 h | 222 min |
| `HonkaiStarRail_leaks_1xjde36` | removal_notice | arctic | 3.7 h | 222 min |
| `HonkaiStarRail_leaks_1xjdkwf` | liveness_removed | arctic | 3.6 h | 212 min |
| `HonkaiStarRail_leaks_1xjdmog` | removal_notice | arctic | 3.5 h | 207 min |
| `HonkaiStarRail_leaks_1xjdr5v` | liveness_removed | rss | 3.4 h | 2 min |
| `HonkaiStarRail_leaks_1xjdv7f` | liveness_removed | rss | 3.4 h | 2 min |
| `HonkaiStarRail_leaks_1xjdzv2` | liveness_removed | rss | 3.3 h | 2 min |
| `HonkaiStarRail_leaks_1xjegxk` | liveness_removed | rss | 2.9 h | 2 min |
| `HonkaiStarRail_leaks_1xjenx8` | liveness_removed | rss | 2.7 h | 2 min |
| `HonkaiStarRail_leaks_1xjerk7` | liveness_removed | rss | 2.7 h | 2 min |
| `WutheringWavesLeaks_1xivgx5` | removal_notice | arctic | 19.1 h | 1137 min |
| `WutheringWavesLeaks_1xivhbn` | removal_notice | arctic | 19.1 h | 1137 min |
| `WutheringWavesLeaks_1xj9k8k` | removal_notice | arctic | 7.5 h | 437 min |
| `WutheringWavesLeaks_1xj9l31` | removal_notice | arctic | 7.4 h | 437 min |
| `WutheringWavesLeaks_1xjdfwl` | liveness_removed | rss | 3.7 h | 2 min |
| `Zenlesszonezeroleaks__1xj62lz` | removal_notice | arctic | 11.1 h | 657 min |
| `Zenlesszonezeroleaks__1xj93ln` | removal_notice | arctic | 8.0 h | 472 min |

**Honest limits.** A post only posts if its *fresh* record is clean **and** the post is
still live **and** inside the 48 h window. The 13 `removal_notice` keys are not touched
by this round: if they were genuinely removed, they are gone and no code change can
bring them back; if they were removed by mistake, they return when RSS sees them again.
`1xi4zoq` is at 39.6 h of a 48 h window — no round-98 change reaches a `removal_notice`
hold, so it expires on its own schedule.

## Cost and blast radius

- One extra archive request per run, and only when a reclaim candidate exists.
- No change to the posting path, the dedup cache, the flood cap, the fresh hold, or the
  Discord card builder.
- `run_stats` gains six fields; the summary gains ~10 lines (largest step script
  14,509 chars, guard 16,000, GitHub cap 21,000).
- Engine-formatted settings line adds `reclaim 5/run, snapshot override after 3 feeds`.

## Edge cases (each one has a test)

| Case | Behaviour |
|---|---|
| Archive record has no usable `created_utc` **and** the pending entry has no `published_ts` | `no_timestamp` — hold stands, nothing written, never posted on a guess |
| Archive record carries a timestamp in the future | clamped to `now` (otherwise the fresh-age floor would hold it forever) |
| Record's own `subreddit` disagrees with the pending key | `sub_mismatch` — never re-admitted (no wrong-channel post) |
| Held key belongs to a subreddit no longer tracked | filtered before the archive call (no request, no "No webhook configured" ERROR line) |
| Archive unreachable / circuit open / no record | `no_record` — hold stands, re-probed next tick, fail-open |
| Batch request returns a subset | only the returned ids are acted on; the rest stay held |
| Malformed entry in `stale_snapshot_keys` / `reclaim_keys` | summary skips it and truncates long text; the step still exits 0 |
| `TEST POST` mode (feed bypassed) | reclaim disabled; `native_keys` initialised outside the feed branch |
| `DRY_RUN` | no Discord post; liveness verdict is `skipped` |
| First run (empty dedup cache) | reclaim disabled (anti-flood, same rule as the archive sweep) |

## Verification

- `python3 tests/test_smoke.py` → **ALL PASS**. Nine of the new checks run the **real
  `v3.main()`** with the network mocked and read the run-result record back:
  reclaim → delivered + leaves pending; feed-listed + streak 3 + archive says removed →
  delivered with `stale_snapshot_overrides: 1`; the same with streak 1 → still held; a
  reclaim that still reads as removed → kept, reason preserved, `last_checked` refreshed;
  a `removal_notice` hold → never reclaimed, zero archive requests; plus the four edge
  cases in the table above. This is what caught the placement bugs below — a grep could
  not have.
- Ten further checks execute the pure helpers (streak reset, native-only listing, no
  `post-json` override, reason/window/seen/limit filters, single-request batching,
  workflow presence of both summary lines).
- Two real bugs were found and fixed before this PR: (1) `num()` was called without its
  `tail` argument in the new summary lines — the summary step would have exited 1 on the
  first production run; (2) `native_keys` was initialised only inside the feed branch, so
  TEST POST mode raised `UnboundLocalError`, and the reclaim pass was placed *after* the
  "no candidates" early return, which would have skipped it on any quiet tick (exactly the
  tick where a frozen hold needs it).

  execute `_bump_native_streak`, `_stale_snapshot_override` and `_reclaim_due` (streak
  reset, native-only listing, no `post-json` override, reason/window/seen/limit filters,
  single-request batching, workflow presence of both summary lines).
- The `Write monitor run summary` script was rendered against a synthetic run-result
  record: exit 0, and the two new blocks print as intended.
