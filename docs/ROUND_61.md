# Round 61 (2026-10-04) — stale-tip double post: sync-to-tip + semantic cache merge

## The incident (live, 2026-10-03, prod Reddit repo)

`Genshin_Impact_Leaks_1wwyure` was posted to Discord **twice**. Forensics
from the prod repo:

| UTC time | Event |
|---|---|
| ~21:56:3x | Run X posts `1wwyure` (first post) |
| 21:56:35 | Run X pushes cache commit `2de1491` — `1wwyure` now in `posted_reddit.json` |
| 21:56:41 | Run #4014 starts — checks out `dd756a5`, the **stale** tip (no `1wwyure` key) |
| 21:57:02 | Run #4014 sees `1wwyure` as "new", gates pass, **posts it again** |
| 21:57:06 | Run #4014's cache push rejected → `git pull --rebase` → **CONFLICT** in `pending_reddit.json` → recovery aborts → exit 1, dedup state lost |

## Two root causes

### 1. `workflow_dispatch` pins `GITHUB_SHA` at DISPATCH time

The 2026-09-19 P0 concurrency fix assumed a queued run "checks out the
NEWEST main". **That assumption is false.** A queued `workflow_dispatch`
run starts later but checks out the tip *as it was when the trigger
arrived* — without the previous run's fresh dedup cache. At the 5-minute
cadence runs never queued, so the flaw stayed invisible; at 2–3 minutes
(plus stacked manual triggers) overlaps became routine and the latent bug
fired. The run's own log proves it: `actions/checkout` fetched
`+dd756a5...:refs/remotes/origin/main` six seconds after `2de1491` was
already the real tip.

### 2. The cache-push recovery treated a line conflict as fatal

Both runs edited the same `last_checked` line of
`pending_reddit.json` and both appended `1wwyure` to `posted_reddit.json`.
Git merges **lines**; these files carry **meaning**. The old
`git pull --rebase` recovery hit the conflict, aborted at attempt 1/3, and
exited with the dedup cache unpersisted ("the next run may re-post").

Also observed, **benign**: runs #3810/#3811 "Canceling since a higher
priority waiting request exists" — GitHub keeps only the newest *pending*
run per concurrency group. A superseded queued run is a skipped tick, not
a failure; the next tick reads the same feed.

## The fixes (both monitor workflows)

### Fix 1 — "Sync to the live branch tip" step (kills the root cause)

Right after checkout, before anything reads the caches:

```bash
git fetch origin "${CACHE_BRANCH:-main}"
git reset --hard FETCH_HEAD
```

A queued run now operates on the *current* dedup cache — `1wwyure` would
have been present and skipped. An unqueued run is already at the tip and
this is a no-op (~1 s). Correctness becomes **cadence-independent**:
5, 3, 2, even 1-minute cron is safe.

### Fix 2 — semantic cache merge (kills the accomplice)

The persist step saves OUR freshly-written caches aside before pushing.
On a rejected push it no longer rebases lines; it resets to the live tip
and re-merges **semantically** via `.github/scripts/merge_monitor_caches.py`:

* **list files** (`posted_reddit.json`, `posted_tweets.json`): strict
  union — a lost dedup key is a double post; an extra key is merely
  re-evicted by the round-34 caps on the next run. Never drops, never
  duplicates.
* **dict files** (`pending_reddit.json`, `posted_messages.json`): key
  union; newest embedded timestamp (`last_checked`/`first_seen`/
  `delivered_at`/`posted_ts`) wins a collision, ours wins ties.
* telemetry shape mismatches (`proxy_health.json`): ours wins wholesale.
* hygiene: pending keys already covered by the merged posted list drop
  out (not load-bearing — the posting loop re-checks `unique_key in
  posted` immediately before the pipeline).
* invalid JSON anywhere → **loud non-zero exit**; the workflow reports
  `CACHE PUSH RECOVERY FAILED` rather than pushing a half-merge.
* deterministic output (sorted dict keys, stable indent) — re-merging an
  identical state is byte-stable.

The 3-attempt loop, detached-HEAD-safe `git push origin
"HEAD:${cache_branch}"`, bounded backoff, and every loud
`::error::CACHE PUSH FAILED` string are unchanged (r39 guard updated to
pin the new recovery, with an r61 annotation).

## Tests (all offline)

* 15 new `r61` smoke checks: exact-incident replay through
  `merge_lists`/`merge_dicts`, the CLI invoked with the workflow's exact
  argument shape, the hygiene rule, loud failure on invalid JSON, and
  per-workflow guards (sync step present, semantic recovery present,
  `git pull --rebase` gone, dispatch-time pinning documented).
* r39 cache-persistence guard updated (annotated) to pin the new recovery.
* Full suites green: smoke **783 PASS / 0 FAIL**, signals **216 PASS**.
* Every `run:` block in both monitor workflows passes `bash -n`; both
  ymls parse as YAML; the merge script compiles clean.
* **End-to-end race simulation** (real bare origin + two clones replaying
  run X vs run #4014, executing the workflow's verbatim recovery
  sequence): stale push rejected → semantic merge → push accepted →
  origin tip = strict union, newest pending wins, no conflict, exit 0.

## Deploy

Copy to BOTH prod repos (same paths):
`.github/workflows/reddit_monitor.yml`,
`.github/workflows/twitter_monitor.yml`,
`.github/scripts/merge_monitor_caches.py`, `tests/test_smoke.py`,
`README.md`, `docs/ROUND_61.md`. No new Variables, no Secrets, no
behavior change for posting logic — workflow-layer only. Round 61 is
all-or-nothing per repo (the new guards require the merge script **and**
both updated ymls), so never cherry-pick. Step-by-step paste blocks:
[`ROUND_61_DEPLOY.md`](ROUND_61_DEPLOY.md).

### Is the Twitter monitor affected?

Not by the incident — by the **bug**, yes. The flaw lives in the workflow
skeleton both monitors share (cron → `workflow_dispatch` → dispatch-time
SHA → queued run on a stale tip → cache commit-back). Twitter escaped
only because it persists a cache solely when a tweet actually posts, so
its collision window is tiny — not zero. The r61 additions cost it one
`git fetch` + reset (~1–2 s) **before** the feed is read; no gate, no
posting-path, no concurrency change — delivery speed is unchanged.

## Feed-source research note (wide sweep, 2026-10-04 — no credits added)

Assessed: RSSHub, Folo, upvote-rss, trashhalo/reddit-rss,
sametcn99/reddit-rss-api, MonitoRSS, FeedHub, and the RSS-Bridge
RedditBridge network (21 public instances listed as of 2026-09-30).
**None passed instance-level verification**, so per the "proven fully
compatible" bar no credits were added and nothing was wired — fleet
values unchanged. Probe results:

* RSSHub public instance: no Reddit route deployed (`NotFoundError`);
  Reddit routes require self-hosting + Reddit API credentials.
* RSS-Bridge RedditBridge: the bridge is real and maintained, but
  `rss-bridge.org/bridge01` and `rss.bloat.cat` both died in
  `RedditBridge->collectData()` with a `RateLimitException`
  (Reddit rate-limits the shared datacenter IP), `rb.vern.cc` answers
  403, and `bridge.suumitsu.eu` does not whitelist the bridge.
* trashhalo's hosted instance unreachable; sametcn99's deployment dead
  (Deno Deploy Classic sunset 2026-07-20).
* Redlib: `ENABLE_RSS` remains off by default; the instance-list issue
  asking for an RSS-enabled list is open since 2024 and live instances
  report "RSS enabled: Unset" — consistent with the round-59/60 finding
  that no public Redlib serves plain RSS.

**The sweep's actual takeaway:** every third-party Reddit feed middleman
runs from a datacenter IP and hits the same Reddit 403/429 wall our own
probes hit — a middleman adds a hop, not an exemption. The sources that
DO work are exactly the ones already in the fleet: `www`/`old` reddit
native `.rss` (still free, public, and maintained in 2026), the private
feed token, and Arctic Shift. The current architecture is not missing a
better source; it already uses the only reliable class of sources.
Before any future candidate is ever wired, verify it with a 5× body-read
probe **from a GitHub runner** (status codes lie — round 59): fetch the
route five times and require real `/comments/<id>/` post IDs in every
response body.

## Non-changes

* Posting logic, gates, fleets, Variables: untouched.
* `cancel-in-progress: false` and both concurrency groups: untouched
  (still required so two runs never *execute* at once).
* The superseded-queued-run cancellations (#3810-style) are expected and
  harmless at fast cadences; no code should "fix" them.
