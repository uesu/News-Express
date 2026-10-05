# Round 49 — parallel proxy dispatch (2026-10-01)

Carries forward the two pieces that missed PR #23 (**48c** proxy audit, **48d**
video early exit) and replaces the serial proxy chain with a concurrent one.

## A. The evidence

Prod Actions log, repo `7jkxmy9nvbc`, run of 2026-10-01 11:55 UTC,
post `AnantaLeaks_1wuxc27`:

```
11:55:50.681  redditez had no usable data — trying the next proxy
11:55:51.098  proxy media via vxreddit — 1 item(s) (best so far)   (+0.417 s)
11:55:51.408  embeddit returned text only                          (+0.310 s)
11:55:51.408  proxy media winner — 1 item(s)
```

Each service only started after the previous one finished: **~1.5 s of wall
time per post**, and the chain kept querying after a usable winner existed.
The same shape repeated for `1wuxcjw` (`00.739 → 01.271 → 01.474`).

Two more facts from the same run:

* `redditez` was logged **OK at warm-up** and then returned *no usable data*
  for **both** live posts seconds later — it is genuinely intermittent.
* every embeddit attempt printed **two** outcome lines ("returned text only …
  continuing the chain" *and* "had no usable data — trying the next proxy"),
  because the text-only branch fell through to the end of the loop body.

Field comparison (user screenshots, same posts):

| service | canonical `/comments/` | `/s/` share link | video | notes |
|---|---|---|---|---|
| vxreddit | yes | **yes** | yes (with audio) | most complete + most stable |
| redditez | yes | **no** — "Malformed url?" | intermittent | 2 HTTP hops per attempt |
| embeddit | yes (id only) | n/a | no audio | GIFs broken — last resort |

## B. What changed

### 1. Priority order is now evidence-based
`PROXY_SERVICES = ("vxreddit", "redditez", "embeddit")`. This is now purely
the **tie-break** order (equal media counts keep the earlier service); it is
no longer the order services are asked in.

### 2. Concurrent dispatch with waves
* **Wave 1** — vxreddit + redditez, dispatched together at t=0.
* **Wave 2** — embeddit, held back `PROXY_WAVE_DELAY` (0.5 s), and started
  early if wave 1 settles without a winner.
* **Decisive answer** (video on a video post — round 48d — or
  `MEDIA_CAP_ITEMS` items) cancels everything still in flight.
* Otherwise, once *some* media exists, stragglers get at most
  `PROXY_GALLERY_GRACE` (1.5 s) to produce a **more complete** gallery, then
  they are cancelled.
* `PROXY_MAX_CONCURRENCY` (8) caps in-flight proxy requests per run.

0.5 s for the wave delay is tuned on the measured prod latencies (vxreddit
0.42 s, redditez 0.76 s, embeddit 0.31 s): a healthy vxreddit answers *before*
the delay elapses, so a video post never dispatches the third service at all.

### 3. Round 25 is deliberately NOT short-circuited
An early draft cancelled wave 2 as soon as the top-ranked service returned any
media. The test suite caught it: incident `1wj0p83` is precisely the case where
the **lowest**-priority service (embeddit) held the complete 13-item gallery
while the others had 1 item. Only a *decisive* answer ends the wait.

### 4. Tie-breaks are deterministic
Results now arrive in network order, so the round-25 rule was made explicit:
`_better_media()` — more items wins; an equal count keeps the better
`PROXY_SERVICES` rank. A `wait()` batch is processed in rank order, so the
winner never depends on set iteration order.

### 5. Share links skip redditez
`SHARE_LINK_RE` / `proxy_services_for()`: a `/r/<sub>/s/<token>` or
`/u/<name>/s/<token>` path drops redditez (which always answers "Could not
find provider for this url. Malformed url?"). The share token is **not** a
post id, so it cannot be rewritten without a round trip. Canonical
`/comments/` paths still ask all three.

### 6. One log line per attempt
The duplicate embeddit line is gone.

### 7. X: section-accessory thumbnails are healed too
Round 47's `unresolved_media_items()` only walked `items[]`. A type-11 section
accessory keeps its media outside `items[]`, so a thumbnail Discord failed to
resolve was invisible to the heal pass. Same failure shape, same cure.

### 8. Redlib reachability telemetry
The prod run only said *"all instances" / "all sources"* failed, which cannot
distinguish a dead mirror from a flaky one. `_redlib_reach` counts ok/total per
instance and `log_redlib_reachability()` emits one line per run:

```
REDLIB-REACH: 2/3 instance(s) answered this run — redlib.catsarch.com 0/3, redlib.nadeko.net 1/4, www.reddit.com 2/2
```

Zero extra requests, zero latency. This is the data needed before pruning or
refreshing the instance list.

## C. Rejected: proxy-based mod-queue evidence

Considered and dropped. Incident `1wuwjiw` was *in the moderator queue* and the
proxies **served it with media anyway** — proxy reachability does not correlate
with queue state, so the signal has no discriminative power. What it *would*
correlate with is redditez flaking, i.e. it would manufacture false holds and
delay good posts. Explicitly out of scope.

## D. Measured

Offline harness (`/tmp/bench.py` shape; fake services with the measured prod
latencies redditez 0.76 s / vxreddit 0.42 s / embeddit 0.31 s):

| case | serial (before) | round 49 | services dispatched |
|---|---|---|---|
| video post (48d decisive) | 1.49 s | **0.42 s** | 2 |
| prod 11:55 shape (rez dead, vx 1 item, emb text) | 1.49 s | **0.81 s** | 3 |
| single-image, all three answer (0.4 s each) | 1.20 s | **0.80 s** | 3 |

On an 18-post run that is roughly **12–19 s** off the Reddit job.

## E. Tests

`tests/test_smoke.py` — **ALL PASS**, `tests/test_reddit_signals.py` —
**ALL PASS (196)**. New/updated round-49 checks:

* measured parallel vs serial timing; wave 2 starting early when wave 1 settles
* a video answer cancels wave 2 before it opens a socket
* `1wj0p83` — a late embeddit with 13 items still beats a fast 1-item answer
* a hung service cannot stall a post (bounded grace, then cancel)
* the global semaphore caps in-flight requests
* share-link handling, tie-break order, single log line per attempt
* rank-ordered (deterministic) tie-breaks
* section-accessory thumbnail detection, and resolved accessories not flagged
* reachability line format, empty-run silence, and real wiring into
  `_fetch_redlib_post_page` + `main()`

Updated in place (behaviour genuinely changed): the round-23/25 fallback checks
now assert the **highest-priority** text-only answer rather than the first to
arrive, and the round-48c/48d checks assert *services dispatched* rather than a
fixed serial call order.
