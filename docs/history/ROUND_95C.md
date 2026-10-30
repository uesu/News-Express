# Round 95c — 2026-10-30

Two small changes, both answering "can a held or stale item ever be posted
twice, or posted far too late?" No structural change: no new files, no new
service, no change to the delivery path, and no added request on a normal run.

---

## 1. Twitter: a stale feed cannot become a re-post

### What happened (measured, not assumed)

Run **#12043** (`2026-10-30T00:55:25Z`) — log:
`polishing and refining/Twitter Feed Monitor #12043.txt`.

* nitter mirrors `nitter.cf`, `xitter.cf`, `nitter.gq`, `xitter.gq` all returned
  **HTTP 502**; `nitter.meowing.monster` returned 429 then recovered.
* All five accounts reported `feed OK` — so "the fleet is down" is not the
  failure shape to design for. A **partly** healthy fleet is.
* Three posts went out from `TYPEII_EN` at 00:55:39 / :42 / :45.

Were those re-posts? **No — checked against production history.** All three
`posted_tweets.json` keys (`TYPEII_EN_2115271059188613499`,
`…_2114559707734245394`, `…_2112102702817972715`) are **absent** from every
earlier version of the cache: across the 100 commits that touch the file in
`uesu/wvkhabh2s22` they appear only in `74c4fd42` (`+3/−0`, the run itself).
Their snowflakes date the tweets to **2026-10-28**, **2026-10-26** and
**2026-10-19** — 46 h, 94 h and 257 h old at the moment they were posted.

So the real defect is narrower than "double posting":

> When the fleet is degraded, a surviving instance can answer with an **old
> backlog**. The dedup cache only stops keys it already holds. Any key it does
> not hold — a fresh deployment, a reset, an evicted key — goes out as news
> days after the fact.

The neighbouring project's history (`4cuck/teapawt`) shows the instance-health
problem is routine, not a one-off: its recent commits are all "take a proxy out
after five timeouts", "disable an exit after eight timeouts in a row", "keep
moving a request off a blocked exit".

### The change

`testing area/twitter_v3.py`, one guard in the existing per-entry loop:

* **`TWITTER_MAX_AGE_HOURS`** (default **24**, `0` = off) — an entry older than
  the floor is skipped and logged as `STALE-SKIP`, *before* the tweet-data
  fetch, so a stale backlog costs **zero** requests instead of a full card
  build per entry.
* Age has **two independent witnesses**: the feed's `published_parsed` and the
  tweet-id **snowflake** (`(id >> 22) + 1288834974657` ms).
  * **Own tweet** → the **id** wins when it is parsable: it is immutable and
    encodes the creation instant exactly, so a mirror that re-stamps an old
    backlog entry with "now" — or mangles the date outright (epoch 0) — cannot
    smuggle it through. The feed date is the fallback when the id is unusable.
  * **UTC, not local time.** feedparser yields UTC struct_times and the age is
    read with `calendar.timegm`. `time.mktime` would read them as local time:
    on a UTC+8 machine every entry would look 8 h older, so a 16 h-old tweet
    would hit a 24 h floor.
  * **Repost** (the link points at another author's status) → the **feed date**
    wins, because reposting an older tweet is a legitimate new post and the
    original's id is old by definition.
* Failure modes are chosen so the guard can never lose a live post:
  * unknown age (no date, unparsable id) → **posts**, as before;
  * `TEST_TWEET_ID` → exempt (an operator asked for that specific tweet);
  * `TWITTER_MAX_AGE_HOURS=0` → byte-for-byte pre-95c behaviour.
* Cost on a normal run: one integer shift and one comparison per feed entry —
  no request, no measurable time. Confirmed: nothing else in the loop changed.

Why 24 h: the cron fires every 5 minutes, so a genuine tweet is posted within
minutes of publication. A day-old entry is a backlog, never news.

### Proof

| Check | Result |
|---|---|
| the three #12043 entries, judged at the run's own clock | 46.4 h / 93.4 h / 256.2 h → **all refused** |
| a tweet from 4 minutes ago | age ≈ 240 s → **posts** |
| entry with no date and no parsable id | age unknown → **posts** (fail-open) |
| entry whose feed date says 1 h but whose id says 256 h | id wins → **refused** (re-stamped backlog) |
| fresh tweet whose feed date says 1970 | id wins → **posts** (broken feed date cannot hold a live tweet) |
| guard position in the loop | before `fetch_tweet_details_any` → 0 requests |
| feed says "2 min ago", id says 40 h (re-stamped backlog) | **refused** (id wins) |
| repost of a 60 h-old tweet, feed date now | **posted** (feed date wins) |
| `TWITTER_MAX_AGE_HOURS=0` | guard inert |

---

## 2. Reddit: the re-check wait is now one cron tick, not 30 minutes

`PENDING_RECHECK_SECONDS` default **1800 → 300**.

The throttle exists so a held post is not re-verified on every run. At 30 min
against a 5-minute cron, a post held for a transient reason (archive snapshot
stale, media still filling in, a moderator approval landing) could wait **25
extra minutes** after the condition cleared. 300 s is exactly one tick: the
hold is re-probed on the **next** run, so the post lands within ~5 minutes —
and the operator sees the same timing they see on `main` for an ordinary post.

Scope of the extra work is bounded:

* removed / deleted posts are still **never** re-checked (`_NO_RECHECK_REASONS`);
* each due post costs one Arctic lookup (≈0.8 s typical, 8 s timeout,
  fail-open) inside the existing round-95 probe budget;
* nothing new is added to a run that has no held posts.

Restore the old behaviour with the Variable `PENDING_RECHECK_SECONDS=1800`.

---

## 3. Workflow summary: state a future agent can read

Workflow logs are not readable by later agents, so the state now lands in
`$GITHUB_STEP_SUMMARY`:

* the engine emits **one** machine-readable line —
  `V3 SUMMARY: posted=N dedup_skipped=N stale_skipped=N cache_missing=N
  cache_keys=N max_age_hours=N` — and the Twitter summary renders it under
  **### Dedup / backlog state**;
* `entries refused as stale backlog` counts `STALE-SKIP:` lines;
* if the line is absent the summary says **`engine: unavailable`** rather than
  implying "zero re-posts";
* `cache: failed` now also prints an explicit re-post warning ("keys posted
  this run may be re-posted next run"), because an unpersisted cache is the
  one remaining way this monitor can duplicate a post.

---

## Verification

** `tests/test_smoke.py`: **1238 PASS** (20 round-95c guards added; the round-30
  throttle guards were retargeted to the new 300 s default, including a
  +310 s "due" boundary).
* Mutations: removing the guard, moving it after the fetch, flipping it to
  fail-closed, trusting the feed date over the id, judging a repost by the id,
  and reverting the throttle each fail the suite (8/8 caught).
* `compileall` clean; `twitter_monitor.yml` and `reddit_monitor.yml` parse as
  YAML; summary renderer exercised with a real log line and with a missing one.
* Delivery path unchanged: no new requests in `twitter_v3.py`, and the Reddit
  change only alters *when* a hold is re-checked, never *whether* a live post
  is delivered.
