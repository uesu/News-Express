# Round 108 — Arctic hardening for the backup chain (2026-11-02)

Scope: the OLD-structure Reddit engine only (`testing area/reddit_main_v3.py`, the chain that
runs when the Devvit relay is paused, stale, empty or unconfigured — `INTAKE-FALLBACK`). The
relay-primary path is untouched: a relay-served post still needs no redlib / reddit.com /
Arctic request (round 104), and relay restores still go through `relay_listed_after_hold`
(round 107).

## Why now

Reddit retires RSS on **2026-11-13**. After that date the fallback chain is redlib (0/26
instances answer from the Actions runner since 2026-10-29) plus **Arctic Shift**. Four
different places talked to the archive, each with its own copy of the request/parse code and
none of them tolerant of the archive's known behaviour:

| quirk (observed) | effect before this round |
|---|---|
| back-to-back requests time out | the per-subreddit sweep fired its requests with no gap; one timeout per subreddit = three strikes = circuit open for the rest of the run |
| one transient 429 / 5xx / timeout | counted as a full outage although the next request usually answers |
| unbounded `/posts/search` (no `after=`) | the slowest query shape; only guaranteed bounded by the one caller that happened to pass `after_epoch` |
| rows accepted without shape checks | a row without a string `id` could flow into the sweep |
| a removal snapshot later reversed by a mod approval | **1xlrj90** (round 107): the old chain held the post as `removal_notice` at 08:20Z; the mods approved it at ~12:35Z; in relay mode the relay restored it, but with the relay paused the hold could only "re-enter via RSS" — a dead end once RSS is gone, so the post would have stayed held until the 48 h window dropped it |
| the reclaim re-admitted a fresh row with `removed_by_category` set | an untouched title/body let the row through to the pipeline, where the round-95 probe held it again one step later — a wasted pipeline pass |

## What changed

### One archive request helper — `_arctic_get_rows(session, url, params, *, timeout, label, what)`

All four call sites (`fetch_arctic_post`, `fetch_arctic_posts_by_ids`,
`fetch_arctic_subreddit_posts`, `_fetch_arctic_post_row`) go through it:

- **spacing** — consecutive archive requests are at least `ARCTIC_MIN_SPACING` (1.0 s, max 5)
  apart, process-wide (the sweep, the reclaim batch and the liveness lookups share the gap);
- **one retry** — a timeout, connection drop, 429 or 5xx is retried once after
  `ARCTIC_RETRY_BACKOFF` (1.5 s; a short `Retry-After` is honoured, capped at 5 s), within a
  per-run `ARCTIC_RETRY_BUDGET` (3). A 404/422/parse error is final. A request that still
  fails after its retry counts exactly **one** strike on the caller's own counter, as before —
  the 3-strike circuits, their separation (`_arctic_fail_count` vs `_liveness_fail_count`) and
  "a miss is not an outage" are unchanged;
- **strict parse** — only `{"data": [...]}` is an answer; rows must be dicts with a non-empty
  string `id` (others are dropped, never matched to a candidate);
- **always bounded search** — `fetch_arctic_subreddit_posts` sends `after=` on every call
  (`now - MAX_AGE_SECONDS` when the caller gives nothing);
- **health in the run result** — `arctic_requests`, `arctic_retries`, `arctic_failures` are
  merged into every `reddit_run_result.json` write; the summary prints
  `- Archive requests: N (retried N, failed N)` when any were made. `_reset_arctic_run_state()`
  starts each run clean. The blank `Arctic Shift unavailable: ` line (a `TimeoutError` with an
  empty message) is gone on every call site, not only the search one (round 69).

### Archive-driven restore — `archive_listed_after_hold(pend, entry, now)`

The old chain's counterpart of round 107. A never-re-check hold (`removal_notice`, title/body
markers, "removed by moderators/filters", …) reopens when **the archive re-read the post after
the hold and the row is clean**:

- `archive_snapshot_time(row)` = newest numeric of `retrieved_on` / `retrieved_utc` /
  `updated_utc` must be **newer** than `max(first_seen, last_checked)`;
- `archived_removal_verdict(row)` must be `live` (no `removed_by_category`, no
  `[removed]` / `[deleted]` / notice markers);
- the hold must be at least `ARCTIC_RESTORE_MIN_SECONDS` (1800) old, so a row that is simply
  re-served by every sweep cannot start a re-check loop;
- at most `ARCTIC_RESTORE_MAX_PER_RUN` (5) per run; overflow is counted as
  `arctic_restores_deferred` and tried next run.

Satisfied → the candidate re-enters the **full pipeline**: the round-20/32 live-source gate
and the round-95 probe decide again. A post that is still removed is held again with its clock
refreshed (so the next restore needs an even newer snapshot); nothing is ever posted on the
archive's word alone. `_pending_throttle_skip` itself still says "skip" for archive resurfaces;
`main()` applies the restore and its cap before consulting it, so the cap lives in one place.
Only `_ArcticEntry` candidates qualify, and the sweep runs only when the relay is not primary,
so relay-primary runs cannot be affected.

Log line: `[<key>] held as '<reason>' since N min, but the archive re-read it clean afterwards
— restore, full pipeline (live sources decide).` Summary:
`- Held posts the archive re-read clean (archive restore): N` with the same
`- restored: <key> — held as '<reason>' for N min` detail lines as the relay restore.

### Reclaim verdict

The round-98 reclaim now judges the fresh row with `archived_removal_verdict` (category **and**
markers) instead of markers only; a mod-removed row keeps its hold without a pipeline pass.

## Knobs (all optional; defaults need no Variables)

| Variable | Default | Meaning |
|---|---|---|
| `ARCTIC_MIN_SPACING` | `1.0` | seconds between consecutive archive requests (`0` = off, max 5) |
| `ARCTIC_RETRY_BUDGET` | `3` | single retries allowed per run (`0` = never retry, max 10) |
| `ARCTIC_RESTORE_MAX_PER_RUN` | `5` | archive-driven restores per run (`0` = off) |
| `ARCTIC_RESTORE_MIN_SECONDS` | `1800` | minimum hold age before the archive may reopen it |

Wired into `reddit_monitor.yml` `env:`; listed in README and `.env.example`; reported in
`effective_settings` and the settings line (`archive retry budget 3, restore 5/run`).

## Cost

Spacing adds ≤ 1 s between archive requests (a six-subreddit sweep: ≤ 5 s). A failed request
now costs at most `timeout + backoff + timeout` instead of `timeout`, three times per run at
most. Nothing changes for relay-primary runs with a complete record (zero archive requests).
Summary step: 15,557 → 15,835 chars (guard 16,000).

## Guards

`tests/test_smoke.py` `r108` (helper behaviour executed against scripted sessions: retry on
timeout / 429 with `Retry-After` / 5xx, final 404, strict rows, per-run budget, liveness
counter isolation, spacing; restore helper cases; main-loop/reclaim/run-result/workflow/docs
pins) and `r108b` (summary wording). `r69` now pins the final failure text with retries off;
the archive-call contract test expects the one retry in its 5xx scenario.

## Game-Express

No engine change needed. GE uses Arctic only as a last-resort single `/posts/ids` lookup
inside `resolve_post` (its fetcher has its own retry/backoff machinery, `retries=0` there) and
has no hold memory — the 1xlrj90 class of issue cannot occur (pinned by GE's
`test_round107_post_approved_from_the_mod_queue_hours_later_is_a_plain_new_item`).

## Addendum (2026-11-03): Devvit Directory readme

`devvit/gaming-express/readme.md` rewritten as a full product readme for the app's Directory
page (`developers.reddit.com/apps/gaming-express`): intro, how it works, delivery semantics,
setup, settings table, inbox contract (`v:1` record and `v:2` update examples with a field
table), moderator menu, fetch domains, permissions, sources, toolchain, current installation.
It names no repository, no consumer and no retired Reddit feature. Ships with the next
`npx devvit upload --copy-paste` + `install` (Reddit assigns the version; the code is 0.0.8
unchanged). `docs/DEVVIT_SETUP.md` §1 / §4 / version table adjusted.
