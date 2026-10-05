# Round 50 — a video win no longer cancels a pending higher-priority service (2026-10-01)

## A. The incident

Prod Actions log, repo `7jkxmy9nvbc`, run `36923059079`
(`job/110573575565`), post `AnantaLeaks_1wv12qb`:

```
20:39:19.152  [AnantaLeaks_1wv12qb] vxreddit returned text only (no media) - still waiting for media.
20:39:19.535  [AnantaLeaks_1wv12qb] redditez had no usable data.
20:39:19.582  [AnantaLeaks_1wv12qb] embeddit returned text only (no media) - still waiting for media.
20:39:20.520  [AnantaLeaks_1wv12qb] crosspost detected via Arctic Shift: /r/AnantaStation/comments/1wv0oiq/...
20:39:21.300  [AnantaLeaks_1wv12qb] redlib gallery enrichment failed (all instances) — proxy/native media used instead.
20:39:21.310  [AnantaLeaks_1wv12qb] proxy media via embeddit - 1 item(s) (best so far).
20:39:21.310  [AnantaLeaks_1wv12qb] video resolved via embeddit - chain complete (no gallery can beat it).
20:39:21.871  [AnantaLeaks_1wv12qb] proxy video OK via embeddit (15278062 bytes).
20:39:21.871  [AnantaLeaks_1wv12qb] card media via embeddit — 1 video tile.
```

`AnantaLeaks_1wv12qb` is a crosspost of `AnantaStation_1wv0oiq`. The first three
lines are the liveness probe against the crosspost's OWN url (expected: a
crosspost page carries no inline media on any of the three services). Once
Arctic Shift resolves the crosspost's original path, `resolve_post_media`
re-asks the proxy chain — this time against `/r/AnantaStation/.../1wv0oiq`,
the post the user independently confirmed renders correctly on **vxreddit**
with a working, audible video (Discord embed JSON captured directly from the
live channel, included in the report). vxreddit is rank 0 in `PROXY_SERVICES`
specifically because round 49's field table marked it the only service with
audio:

| service  | video | notes |
|---|---|---|
| vxreddit | yes, **with audio** | most complete + most stable |
| redditez | intermittent | 2 HTTP hops per attempt |
| embeddit | **no audio** | GIFs broken — last resort |

Only `embeddit`'s outcome is logged for the second lookup — vxreddit and
redditez never got to report in, because round 48d's decisive-video exit
fires on **any** video answer, with no check for whether a higher-priority
service is still in flight. embeddit (rank 2, wave 2, delayed
`PROXY_WAVE_DELAY`) answered inside its own ~0.05 s, while vxreddit/redditez
(wave 1, rank 0/1) were still awaiting a response against the *original*
post's longer page — and were cancelled mid-flight the instant embeddit's
video landed. The card posted on time, with the right content, but silent —
exactly the symptom the user filed ("no audio but the video plays").

## B. The fix

`testing area/reddit_proxy.py`, `fetch_proxy_post()`: the round-48d
decisive-video check now also asks "is a better-ranked service still
pending?" before declaring the chain complete:

```python
if need_video and any(m["kind"] == "video" for m in best_media_result["media"]):
    if any(rank[tasks[t]] < r for t in pending):
        # a higher-priority service might still answer — fall through to
        # the existing bounded grace window instead of cancelling it
        ...
    else:
        decisive = True
        break
```

When nothing outranks the winner (the common case — `vxreddit`/`redditez`
already answered, or the post simply has no higher-priority service left to
ask) behaviour is byte-identical to round 48d: instant exit, same as before.

When a higher-priority service IS still in flight, the video answer falls
into the **same bounded grace window** round 25 already uses for incomplete
galleries (`PROXY_GALLERY_GRACE`, 1.5 s default):

* if the pending service answers first with its own video, `_better_media()`
  replaces the winner (equal item count, better rank) and the chain exits
  decisively on the next pass — the audible video wins, exactly as the user
  observed on vxreddit directly;
* if the pending service answers with no video (fallback-only) or nothing
  at all, or the grace window expires, the original embeddit/other answer is
  kept — no regression versus round 48d's safety net, no post is ever lost
  or delayed beyond the existing grace bound.

Nothing about the warm-up, share-link handling, gallery tie-breaks, or the
media cap check changed.

## C. Why this was invisible to the round 49 suite

The round 49 "a video answer cancels wave 2" test fakes `vxreddit` and
`redditez` at the SAME low latency (0.01 s) — both land in the first
`asyncio.wait()` batch, `vxreddit` (rank 0) always wins the tie-break, and
`decisive` was already correct in that shape (rank 0 can never be outranked).
It never modeled the reverse: wave 1 running **slower** than wave 2's
`PROXY_WAVE_DELAY` + its own latency, which is exactly what a second,
slower proxy lookup (post-crosspost-detection) produced in prod.

## D. Tests

`tests/test_smoke.py` — new ROUND 50 block, 3 checks:

1. `vxreddit` (rank 0) answers at 0.9 s, `embeddit` (rank 2) answers
   decisively at ~0.55 s — the final winner is **vxreddit**, confirming the
   race from 1wv12qb is fixed.
2. `vxreddit` hangs (10 s) with `PROXY_GALLERY_GRACE` lowered to 0.3 s for
   the test — the chain still returns **embeddit**'s video inside the bound;
   no hang, no regression of the round-49 safety net.
3. The original round-49 shape (both wave-1 services answer with video in
   ~0.01 s) is unchanged: instant exit, embeddit never dispatched.

Confirmed the fix reproduces and resolves the exact prod timing: reverting
`reddit_proxy.py` alone (keeping the new tests) fails check 1 with
`winner=embeddit in 0.552s` — the measured prod shape — before the fix, and
passes afterwards.

`tests/test_smoke.py` — **ALL PASS** (691 checks), `tests/test_reddit_signals.py`
— **ALL PASS (196)**.

## E. Out of scope (reviewed, not bugs)

* **`embedded.gallery`** (the third-party Components-v2 Discord bot the user
  referenced) is a separate, independently-operated Discord application —
  it is not part of this repo's pipeline and nothing here calls or depends
  on it. No code change applies.
* **Combined feed covering 5 of 6 subreddits** (`Fetching combined feed for
  6 subreddits... Combined feed OK: 100 entries covering 5 subreddit(s)`):
  `HonkaiNexusAnimaLeaks` simply had no post inside Reddit's own most-recent
  100-entry window across all 6 subs at that moment (it's the lowest-volume
  tracked sub); the per-sub Arctic Shift archive fallback (round 17) still
  runs for it and silently finds nothing when the archive is equally empty.
  Not a regression — same behavior pre-dates round 49/49b.
* **`dedup cache near cap: 621 key(s)` warning**: informational telemetry
  (round 42/46) — the per-sub quota (250) and global backstop (10000) evict
  automatically on every save; `Genshin=250` just means that sub is at
  quota, which is expected for the highest-volume tracked subreddit. No
  action needed.
* **PR #26** (merged) already fixed the unset-repository-Variable
  `ValueError` crash risk; both monitor logs attached by the user (Twitter
  run `36923446826`, Reddit runs `36923059079` / `36923426630`) confirm
  clean imports and zero exceptions on the first production runs after the
  merge.
