# Round 46b — finish the mod-queue fix that PR #21 half-landed

**Base:** `main` @ `692e1b7` (the merge of PR #21).
**Patch:** `docs/round_46b.patch` — 5 files, verified with `git apply --check`
against a clean worktree of `692e1b7`, then applied there and both suites run.

## Why this round exists

PR #21 landed the *rules* of round 46 but not the *plumbing*:

| Piece of round 46 | On `main` after #21 | Effect |
|---|---|---|
| `LISTING_HTML` / `LISTING_RSS`, `listing_proves_release()`, `queue_verdict()` | ✅ | an RSS listing no longer counts as proof of release |
| strong/weak hold tiers + `MOD_QUEUE_WEAK_GRACE_SECONDS` | ✅ | wired in `.env.example` + workflow |
| HTML-first listing resolution | ❌ | **see below** |
| `LISTING_TIMEOUT_SECONDS`, `LISTING_HTML_GRACE_SECONDS` | defined, never used | dead constants |
| no-page branch in `mod_queue_reason` | ❌ | an unrenderable (likely queued) post is still posted |
| round-46 regression + latency tests | ❌ | 168 signal checks instead of 190 |

`_fetch_new_listing` on `main` still asks Reddit's `/new.rss` **first** and only
falls back to redlib HTML when RSS fails — and RSS practically never fails. So
the monitor now almost always holds an `rss` listing, which under the new
provenance rule can prove nothing. Consequences on live `main` today:

* the 60 s fast settle (`POST_SETTLE_VERIFIED_SECONDS`) **never applies again** —
  every post waits the full `POST_SETTLE_SECONDS` (300 s), i.e. an extra cron tick;
* the round-38d negative-space rule can **never** run (it needs an API-backed listing);
* every post inside the mod-queue window still pays the per-post page fetches
  across all 9 instances.

Net: `main` is *safer but slower* than it was before round 42.

## What changes

### 1. `_fetch_new_listing` — one concurrent batch, API-backed answer wins

All redlib `/new` HTML hosts and the Reddit `/new.rss` sources start **at the
same time** (`asyncio.wait(..., FIRST_COMPLETED)`), and the answer is taken as
soon as the question is settled:

* the first API-backed (HTML) answer wins **immediately** — only it can prove
  a post left the moderator queue, because redlib renders Reddit's public
  listing API, which excludes queued posts;
* an RSS answer is kept as a **fallback** and grants the HTML hosts only
  `LISTING_HTML_GRACE_SECONDS` (default **2 s**) more to beat it;
* the whole step is capped by `LISTING_TIMEOUT_SECONDS` (default **8 s**);
* every still-pending task is cancelled in `finally` — no stragglers.

A healthy redlib fleet therefore costs one round-trip; a dead one costs the
grace instead of a serial timeout chain. Behaviour when nothing answers is
unchanged: the gate fails **open** (round 37).

### 2. `mod_queue_reason` — decide even when no mirror renders the page

`if not page: return None` became a real decision. "No mirror can render this
post" is itself evidence while the post is young, and a queued post is exactly
the kind a mirror cannot render:

| No page, and… | Verdict |
|---|---|
| an **API-backed** listing contains the post | post it (it is public) |
| a readable API-backed listing that *should* still show it does not | hold (`pending approval`) |
| no listing that can prove release, post younger than `MOD_QUEUE_WEAK_GRACE_SECONDS` | hold one more tick |
| older than the grace | post it (never hold for ever) |

### 3. Configuration

`.env.example` + `reddit_monitor.yml` now carry `LISTING_HTML_GRACE_SECONDS`
and `LISTING_TIMEOUT_SECONDS` (both optional repository Variables; the
defaults above are what runs if you set nothing).

## Tests actually run (not claimed — executed)

Run against a clean worktree of `692e1b7` with the patch applied:

* `python3 tests/test_smoke.py` → **ALL PASS** (includes 15 new r46/r46b checks)
* `python3 tests/test_reddit_signals.py` → **ALL PASS (190 pass)** (was 168)
* `python3 -m compileall -q "testing area" tests` → clean

New coverage:

* **Incident regressions** — `1wuqy6z` (queued, zero comments) and `1wurg8f`
  (queued, AutoModerator source-rule comment) are both **held** when only the
  RSS listing shows them, and both post normally once an API-backed listing
  confirms them.
* **Provenance** — `listing_proves_release`/`queue_verdict` for every
  source × signal combination, including fail-open on an unreadable listing
  and the 2-tuple back-compat path.
* **No-page branch** — all four rows of the table above.
* **Measured latency** (real `asyncio` timings, offline fake session):
  * healthy fleet → API-backed listing in **< 0.5 s**;
  * HTML and RSS requests are issued **together**, not in sequence;
  * 5 s-slow fleet with a 0.3 s grace → falls back to RSS in **< 1.5 s**;
  * 0.2 s-slow fleet with a 2 s grace → API-backed answer still **wins**.

## Apply

```bash
git checkout main && git pull
git apply docs/round_46b.patch
python3 tests/test_smoke.py && python3 tests/test_reddit_signals.py
```
