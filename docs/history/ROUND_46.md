# Round 46 (2026-10-01) — two queued posts reached Discord

## What happened

| | 1wuqy6z | 1wurg8f |
|---|---|---|
| created | 05:16:43Z (13:16 PH) | 05:46:59Z (13:46 PH) |
| mirrored to Discord | 05:25Z (13:25 PH) | 05:55Z (13:55 PH) |
| age when mirrored | ~8 min 20 s | ~8 min 30 s |
| state on Reddit | *Post is awaiting moderator approval* | same, **plus** a stickied AutoModerator source-rule comment |
| comments | 0 | 1 (AutoModerator) |
| still pending at 14:05 PH | yes | yes |

Verified from the prod cache history (`uesu/7jkxmy9nvbc`): both IDs appear in
exactly **one** commit each — the commit that added them to
`posted_reddit.json` (05:25:40Z and 05:55:55Z). Neither ever appeared in
`pending_reddit.json`, so **no detector fired at all**.

## Root cause — it was not the settle window

Both posts were ~8.5 min old, well past `POST_SETTLE_SECONDS` (300 s), so the
settle window had legitimately expired. The failure was in what counts as
proof that a post is public.

`_fetch_new_listing()` asks the subreddit's `/new` listing which post IDs are
publicly visible. **Round 38e made Reddit's own token-authenticated
`/r/<sub>/new.rss` the primary source for that listing** — and that feed also
contains posts sitting in the moderator queue. This repository had already
documented the fact in round 20:

> *"the RSS feed ALSO delivers queued posts with their REAL content"*

It is literally the feed the monitor discovers posts from. So every post was
"confirmed present in /new" the moment it existed, and that single wrong fact
disabled three different protections at once:

1. **Settle** — `_listing_confirms_post()` returned True, so the window
   collapsed from 300 s to `POST_SETTLE_VERIFIED_SECONDS` (60 s).
2. **The mod-queue gate was skipped entirely** — `main()` skips
   `mod_queue_reason()` for a post "already confirmed in /new".
3. **The decision itself short-circuited** — `mod_queue_decision()` checked
   *"is the id in the listing?"* **before** it looked at the page text:

   ```python
   if listing_ids is not None and post_id.lower() in listing_ids:
       return None                    # "Present in the public listing"
   if MOD_QUEUE_REQUEST_RE.search(page_html) or ...:
       return "pending approval"      # never reached
   ```

That third point is why **1wurg8f** slipped through even though its
AutoModerator comment (`"Please respond to this comment with a mirror link
and source link"`) matches the round-37 pattern exactly. The evidence was
there; the gate returned before reading it.

## The fix

**Only an API-backed listing can prove a post is public.** A redlib `/new`
page is rendered from Reddit's public listing API, which never includes
queued posts. Reddit's `*.rss` can prove a post *exists*, never that it was
released.

| Change | File |
|---|---|
| `LISTING_HTML` / `LISTING_RSS` provenance tags, `listing_proves_release()`, and the whole decision as a pure function `queue_verdict()` | `testing area/reddit_signals.py` |
| `_fetch_new_listing()` now tries the **API-backed HTML listing first**, querying all instances **concurrently** (one round-trip, not seven sequential timeouts), and tags every result with its source | `testing area/reddit_main_v3.py` |
| `_listing_confirms_post()` returns True only for an API-backed hit → the settle fast path and the "skip the queue gate" shortcut can no longer be triggered by RSS | `testing area/reddit_main_v3.py` |
| `mod_queue_decision()` delegates to `queue_verdict()` and is provenance-aware | `testing area/reddit_main_v3.py` |
| `mod_queue_reason()` now also decides when **no mirror renders the page at all** (previously: post it) | `testing area/reddit_main_v3.py` |
| `MOD_QUEUE_WEAK_GRACE_SECONDS` (default 900) documented + wired | `.env.example`, `reddit_monitor.yml` |

### Two tiers of page evidence

* **STRONG** — `MOD_QUEUE_STRONG_RE`: *awaiting (moderator) approval*,
  *pending (moderator) approval*, *sent to the moderators for review*. Only a
  listing that proves release outranks it. Not time-limited.
* **WEAK** — the existing `MOD_QUEUE_REQUEST_RE` AutoModerator source-rule
  boilerplate. A leak sub posts that comment under **every** submission,
  approved or not, so on its own it may hold a post only for
  `MOD_QUEUE_WEAK_GRACE_SECONDS` (15 min) — long enough to obtain a readable
  listing, not long enough to stall the channel.

### Decision table (what the gate does now)

| Page evidence | Listing | Verdict |
|---|---|---|
| anything | API-backed, **shows** the post | **post** (released) |
| "awaiting moderator approval" | RSS only / none | **hold** |
| AutoMod source-rule only | RSS only / none, post < 15 min | **hold** |
| AutoMod source-rule only | RSS only / none, post ≥ 15 min | post |
| none | API-backed, post **absent** but inside the listing span | **hold** (round 38d) |
| none | RSS only | post (unchanged — no evidence either way) |
| **no page renders at all** | API-backed, post absent | **hold** (new) |
| **no page renders at all** | RSS only, post < 15 min | **hold** (new) |
| **no page renders at all** | RSS only, post ≥ 15 min | post |
| none | listing unreadable | post (round 37 fail-open, unchanged) |

## Effect on speed — measured, not asserted

The listing step now starts **every** source at once (all redlib `/new` pages
*and* Reddit's `/new.rss`) and resolves as soon as the question is settled:
the first API-backed answer wins immediately; an RSS answer is held as a
fallback and only grants the redlib hosts `LISTING_HTML_GRACE_SECONDS` (2 s)
more to beat it; everything is capped at `LISTING_TIMEOUT_SECONDS` (8 s).

Measured against a stubbed network (once per subreddit per run, cached):

| Scenario | Source used | Listing step |
|---|---|---|
| healthy redlib fleet | `html` | **0.00 s** |
| redlib 500 ms slower than RSS | `html` | 0.50 s |
| **every** redlib host hanging | `rss` | **2.00 s** (the grace, not the 8 s cap) |

So the worst case round 46 can add to a run is **2 s per subreddit**, and only
when the entire redlib fleet is unreachable. The old code walked sources
sequentially with a 10 s timeout each, so this path is *faster* than before
whenever a host is slow.

Everything else is unchanged:

* a healthy post confirmed on an API-backed listing keeps the **60 s** fast
  settle and still skips the per-post page fetches;
* no extra requests per post;
* Twitter is untouched.

The only thing that got slower is the case that should be slow: a post that
nothing can prove is public waits one more 5-minute tick instead of being
mirrored. End-to-end that is unchanged for normal posts — discovery is still
bounded by the cron tick (avg ~2.5 min, max 5 min).

## Tests actually run (nothing claimed that was not executed)

```
python -m compileall -q "testing area" tests      OK
python tests/test_smoke.py                        SMOKE TEST: ALL PASS
python tests/test_reddit_signals.py               ALL PASS (191 pass, was 168)
```

26 new checks, including three that MEASURE the listing latency,, including both incidents reproduced by ID:

* `r46: 1wuqy6z — a queued post present in the RSS listing is STILL held`
* `r46: 1wurg8f — the AutoMod source-rule comment holds inside the grace window`
* `r46 wiring: 1wuqy6z is HELD when only the RSS listing shows it`
* `r46 wiring: 1wurg8f is HELD on the AutoMod comment alone`
* `r46 wiring: an API-backed listing releases the same post`
* `r46 wiring: an ordinary post is not held (posting speed unchanged)`
* `r46 wiring: no renderable page + RSS-only listing HOLDS a young post`
* `r46 wiring: absent from a readable API-backed listing HOLDS (no page needed)`
* `r46: an unreadable listing still fails OPEN (round 37 kept)`
* plus the round-38d/38e negative-space suite, re-verified unchanged.

## Applying it

The patch is `docs/round_46.patch`, generated against `main`
(`76512e5`), 6 files:

```bash
git checkout main && git pull
git apply docs/round_46.patch
python -m compileall -q "testing area" tests
python tests/test_smoke.py && python tests/test_reddit_signals.py
```

No repository Variable has to be set — the fix is the default.
`MOD_QUEUE_WEAK_GRACE_SECONDS` only needs setting to change the 15-minute
weak-signal grace (`0` disables the weak signal entirely).

## Afterwards

The two cards are already live in the channel. They are also already in
`posted_reddit.json`, so they will not be re-posted if the mods approve them.
If the mods **remove** them instead, the round-44 retraction
(`RETRACT_DEAD_POSTS`, currently off) is the only thing that would edit the
existing messages — it stays off unless you want it.
