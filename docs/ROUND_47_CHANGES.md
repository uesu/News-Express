# Rounds 47 / 48 / 48b — complete change list for review

> **Where everything lives.** All of it is on the branch
> `arena/01a0f4c3-news-express`, NOT on `main` (this session can no longer
> push — start a new coding session to publish it).
>
> | Round | What | Files |
> |---|---|---|
> | 47 | X media self-heal re-edit; Reddit profile-post crossposts | `twitter_v3.py`, `reddit_main_v3.py`, `.env.example`, `twitter_monitor.yml` |
> | 47 (reverted) | the 300 MiB video cap — rolled back to 256 MiB at your request | `twitter_v3.py` |
> | 48 | the mod-queue banner now outranks the /new listing (incident 1wuwjiw) | `reddit_signals.py` |
> | 48b | delivery latency telemetry (`LATENCY … held … as …`) | `reddit_main_v3.py` |
>
> One cumulative patch for all of it: **`docs/round_47_48.patch`**.
> Companion docs: `docs/ROUND_47.md` (narrative), `docs/LATENCY_MODEL.md`
> (timing model + estimates), this file (hunk-by-hunk review).


Commit `af7adf0` on `arena/01a0f4c3-news-express`, on top of `main` @ `b933006`.
Patch: `docs/round_47.patch` (608 lines). Nothing else in the repo was touched.

```
 .env.example                          |  15 +
 .github/workflows/twitter_monitor.yml |  14 +
 testing area/reddit_main_v3.py        | 103 +++++-   (7 hunks)
 testing area/twitter_v3.py            | 145 +++++++-  (5 hunks)
 tests/test_smoke.py                   | 203 ++++++++++ (1 appended block, 23 checks)
 docs/ROUND_47.md                      | 228 ++++++++++ (write-up)
 docs/round_47.patch                   | 608 ++++++++++ (the patch itself)
```

No file was deleted or renamed. `reddit_signals.py`, `tests/test_reddit_signals.py`,
`reddit_monitor.yml`, `ci.yml`, `README.md`, every Twitter v1/v2 script and every
other monitor file are **unchanged**.

---

## A. `testing area/twitter_v3.py` — 5 hunks

### A1. Line ~185 — `VIDEO_SIZE_LIMIT` **REVERTED** to the original 256 MiB

The 300 MiB / `VIDEO_SIZE_LIMIT_MB` change was rolled back at your request.
The line is byte-identical to `main` again:

```python
VIDEO_SIZE_LIMIT = 256 * 1024 * 1024          # 256 MiB
```

Only a comment was added above it, recording that (a) a ~295 MB 4K rendition
was seen to embed by hand, (b) Discord's Nitro upload limit went 500 MB -> 1 GB
on 2026-09-29 but governs UPLOADED ATTACHMENTS, not the media proxy that renders
external URLs, and (c) one manual success is not a proven ceiling, so the cap
stays at the measured value. `VIDEO_SIZE_LIMIT_MB` was removed from the script,
`.env.example` and the workflow.

### A2. Line ~215 — three new module constants

```python
MEDIA_HEAL = os.getenv("MEDIA_HEAL", "on")... not in ("0","off","no","false")  # default ON
MEDIA_HEAL_DELAY_SECONDS = int(os.getenv("MEDIA_HEAL_DELAY_SECONDS", "45"))
MEDIA_HEAL_ATTEMPTS = int(os.getenv("MEDIA_HEAL_ATTEMPTS", "2"))
```

preceded by a 25-line comment that records the live incident, the exact
`width: 0 / height: 0 / content_type: ""` payload Discord returned, and the
reasoning (cold media proxy → an edit forces re-resolution).

### A3. New function `unresolved_media_items(message)` (~30 lines)

* Pure, synchronous, no network.
* Input: a Discord message object (what `wait=true` returns), or `None`.
* Recursively walks `message["components"]`, descending into every nested
  `components` list (so it works inside the type-17 container), and for every
  media-gallery `items[]` entry looks at `item["media"]`.
* An item is reported as **unresolved** when it has a `url` but is missing
  `content_type`, or has `width == 0`, or `height == 0`.
* Returns the list of offending URLs (empty list = everything is fine).
* Defensive: non-dict input, missing keys, `None` items — all return `[]`
  rather than raising.

### A4. New coroutine `heal_unresolved_media(session, pending)` (~45 lines)

* `pending` is a list of `(webhook_url, message_id, payload, key)` tuples.
* Immediately returns when `MEDIA_HEAL` is off **or** the list is empty →
  a healthy run does literally nothing.
* For each entry, concurrently (`asyncio.gather`, `return_exceptions=True`):
  1. `await asyncio.sleep(MEDIA_HEAL_DELAY_SECONDS)` (default 45 s);
  2. `session.patch(f"{webhook_url}/messages/{message_id}?with_components=true", json=payload)`
     — the **identical payload**, nothing added, nothing removed;
  3. non-200 → log `MEDIA-HEAL … edit HTTP <status>` and **stop** for that
     message (no retry storm on a 404/401/429);
  4. 200 → re-run `unresolved_media_items()` on the edited message Discord
     returned. Clean → log success and stop. Still unresolved → loop, up to
     `MEDIA_HEAL_ATTEMPTS` (default 2) total edits, then log a warning that
     Discord is refusing the asset rather than merely being cold.
* Any exception is caught and logged; it can never take the run down.
* Log prefixes are all `MEDIA-HEAL` so they're greppable in the Actions log.

### A5. `main()` — three small wiring changes

1. Before the `aiohttp.ClientSession` block: `heal_queue: list = []`.
2. The webhook POST URL gained `&wait=true`:
   `f"{webhook_url}?with_components=true&wait=true"`.
   On success Discord now answers **200 with the created message** instead of
   `204` — same single request. The code still accepts `204` (so nothing
   breaks if Discord ignores the flag), in which case `created` stays `None`
   and no heal is queued.
   Side effect to be aware of: the response body is now read on every post.
3. Inside the `status in (200, 204)` branch, after the existing
   `posted_urls.add(...)` + `V3 Posted:` log (dedup behaviour unchanged):
   parse the JSON, run `unresolved_media_items()`, and if anything is
   unresolved **and** the message has an `id`, append to `heal_queue` and log
   `MEDIA-HEAL queued for <key>`. The existing `await asyncio.sleep(1.5)`
   rate-limit pause is kept exactly where it was.
4. After the per-account/per-entry loops, still inside the session:
   `await heal_unresolved_media(session, heal_queue)` — i.e. strictly after
   every tweet has been posted. The dedup-cache save that follows is unchanged.

**What did NOT change on the X side:** feed fetching, the nitter instance
chain, FxTwitter resolution, translation, article handling, quote handling,
GIF converters, card/OG fallback, payload building, button rows, the dedup
cache and its guard, `TEST_TWEET_ID`, and the 1.5 s inter-post pause.

---

## B. `testing area/reddit_main_v3.py` — 7 hunks

### B1. `fetch_proxy_post_memo()` (~line 782) — alias retry

After the normal `reddit_proxy.fetch_proxy_post(...)` call: **if the result is
not a dict or carries no `media`**, iterate `_path_aliases(path)[1:]` and try
each alias once. First alias answer that has media replaces the result and
logs `profile post resolved via its subreddit alias …`.

* For an ordinary `/r/<sub>/…` post `_path_aliases()` returns a single entry,
  so `[1:]` is empty → **zero extra calls, zero extra latency**.
* The per-run memo cache is unchanged (still keyed on the original path, still
  only caches successes).

### B2. New constants + rewritten `normalize_reddit_path()` (~line 1132)

```python
PROFILE_POST_RE      = re.compile(r"^/u(?:ser)?/([^/\s?]+)/comments/([a-zA-Z0-9]+)", re.I)
SUBREDDIT_PROFILE_RE = re.compile(r"^/r/u_([^/\s?]+)/comments/([a-zA-Z0-9]+)", re.I)
```

`normalize_reddit_path(link)`:
* `/r/…` still wins first and behaves **exactly** as before
  (`match.group(1).rstrip("/") + "/"`);
* otherwise it now recognises `/user/<name>/comments/<id>[/slug]` **and** the
  short `/u/<name>/…` form and returns the canonical
  `/user/<name>/comments/<id>[/slug]/`;
* `link or ""` makes it `None`-safe (it previously raised on `None`);
* no match → `None`, as before.

### B3. New `is_profile_post_path(path)` — one-line predicate, used by tests and
future callers; no behaviour of its own.

### B4. New `_path_aliases(path)` — the equivalence table

* `/user/<n>/comments/<id>/` → `["/user/<n>/comments/<id>/", "/r/u_<n>/comments/<id>/"]`
* `/r/u_<n>/comments/<id>/` → the reverse pair
* anything else → `[path]` (single entry)
* `None`/empty → `[]`

This encodes the fact that Reddit files a profile post under the
pseudo-subreddit `u_<name>`, which is the route Arctic Shift and several
proxy services index.

### B5. `CROSSPOST_PERMALINK_RE` (~line 1207)

```diff
-re.compile(r"/r/[^/\s?<>]+/comments/[a-zA-Z0-9]+/")
+re.compile(r"/(?:r/[^/\s?<>]+|u(?:ser)?/[^/\s?<>]+)/comments/[a-zA-Z0-9]+/")
```

Profile permalinks now count as crosspost originals. Subreddit matching is
character-for-character the same alternative, so round-14 behaviour is intact.

### B6. `find_crosspost_original_path()` — return the canonical form

```diff
-        return p + "/"
+        return normalize_reddit_path(p + "/") or (p + "/")
```

So a mirror that emits `/u/aphotide/comments/…` and one that emits
`/user/aphotide/comments/…` produce the **same** path, which keeps the proxy
memo cache and the alias logic consistent. The "skip the post's own
permalink" rule above it is unchanged, and the function still requires the
word `crosspost` to appear in the text (round-14 gate).

### B7. `enrich_gallery_redlib()` (~line 2975) — alias retry for mirrors

If the parallel redlib page harvest returned **nothing at all** (`not any(pages)`),
retry the whole fan-out once per alias; on success it logs
`profile post pages via alias …` and rebinds `path` so the rest of the
function (gallery extraction, video id detection) uses the working route.
Again: only profile posts have an alias, so ordinary posts never retry.

### B8. `resolve_post_media()` (~line 3297) — accept an Arctic profile permalink

```diff
-re.fullmatch(r"/r/[^/]+/comments/[a-z0-9]+/[^?#]*", original_path)
+re.fullmatch(r"/(?:r|user)/[^/]+/comments/[a-z0-9]+/[^?#]*", original_path)
```

When Arctic Shift reports `crosspost_parent_list[0].permalink` pointing at a
profile post, it is now accepted as the original to fetch media from.

**What did NOT change on the Reddit side:** the mod-queue gate and all of
round 46/46b, the NSFW gate, the settle timings, the dedup/repost gates, the
retraction code (still default-off), `extract_subreddit`, `extract_post_id`,
the DASH video ladder, gallery handling, spoiler conversion, the RSS/listing
code, and the workflow for Reddit (`reddit_monitor.yml` is untouched in this
round).

---

## C. `.env.example` — 15 added lines (documentation only)

A new block above the round-46b block documenting `MEDIA_HEAL`,
`MEDIA_HEAL_DELAY_SECONDS` and `MEDIA_HEAL_ATTEMPTS`. All stay commented out =
defaults apply.

## D. `.github/workflows/twitter_monitor.yml` — 14 added lines

Four new `env:` entries on the monitor step, all reading **repository
Variables** (not secrets), all optional — an unset Variable passes an empty
string, which the script treats as "use the default":

```yaml
MEDIA_HEAL: ${{ vars.MEDIA_HEAL }}
MEDIA_HEAL_DELAY_SECONDS: ${{ vars.MEDIA_HEAL_DELAY_SECONDS }}
MEDIA_HEAL_ATTEMPTS: ${{ vars.MEDIA_HEAL_ATTEMPTS }}
```

**You do not need to create any of these Variables.** Unset = the defaults
(heal on, 45 s, 2 attempts), which is the recommended configuration.

plus a comment block explaining them. Triggers, schedule, Python version,
caching, the run line and the cache-persist step are untouched.

> ⚠️ Empty-string caveat: `MEDIA_HEAL_DELAY_SECONDS=""` would make `int("")`
> raise. That only happens if you *create* the Variable and leave it blank;
> GitHub omits unset Variables entirely, which is the normal case. Set a
> number or do not create the Variable.

## E. `tests/test_smoke.py` — +203 lines, 23 new checks

Appended as one block before the final `if failures:` summary; no existing
check was modified or removed. The X checks load `twitter_v3.py` as a fresh
module (`smoke_x_v3_r47`) and use a fake session, so nothing touches the
network.

X (12):
1. the exact broken payload from your message is detected as unresolved
2. a resolved tile is not flagged (no pointless edits)
3. a message with no media / `None` is never flagged
4. an unresolved message is re-edited exactly once when that fixes it
5. the edit URL is `…/messages/{id}?with_components=true`
6. the edit body is byte-identical to the original payload
7. a permanently unresolvable asset stops after `MEDIA_HEAL_ATTEMPTS`
8. **measured**: a healthy run performs zero edits and zero waiting
9. the POST uses `wait=true`
10. healing is proven (by source order) to run after the posting loop
11. the heal pass defaults ON with a 30–60 s delay and ≥ 1 attempt
12. 295 MB is inside the new limit and 405 MB is still outside

Reddit (11):
13–15. profile permalink, short `/u/` form, and ordinary `/r/` normalisation
16. profile-post detection
17. alias pair generation for a profile post
18. an ordinary post has exactly one route
19. `1wuv547` → `1wuv4j8` crosspost resolution
20. round-14 subreddit crosspost resolution still works
21. the Arctic check accepts `/user/…`
22. the proxy alias retry recovers the `v.redd.it` video (fake proxy module
    that only knows `/r/u_aphotide/…`)
23. an ordinary post still makes exactly one proxy call

## F. Verification actually run

On a **clean worktree of `main` @ `b933006`** with `docs/round_47.patch`
applied:

* `git apply --check` — clean
* `python3 -m compileall -q "testing area" tests` — clean
* `python3 tests/test_smoke.py` — **ALL PASS**
* `python3 tests/test_reddit_signals.py` — **ALL PASS (190 pass)**

## G. Risk notes / things to decide

1. **`wait=true` response size.** Every post now downloads the created
   message JSON (a few KB). Negligible, but it is a real behaviour change.
2. **300 MiB cap** rests on one hand-verified data point (your 295 MB test)
   plus the older 405 MB / 521 MB failures. If a video between 256 and
   300 MiB ever fails to render, the heal pass will try to fix it, and
   `VIDEO_SIZE_LIMIT_MB=256` reverts instantly without a code change.
3. **The alias retry is only reached when the primary route returned no
   media**, so it cannot slow the normal path — but on a profile post with a
   genuinely dead mirror fleet it adds one extra fan-out before giving up.
4. **Reddit retraction is still off.** The AnantaLeaks removal happened after
   a correct publication; catching it needs the opt-in post-run sweep, which
   is not part of this round.


---

## H. ROUND 48 (added 2026-10-01) — the mod-queue banner now outranks the listing

### The escape

`r/HonkaiStarRail_leaks` **1wuwjiw** — created 19:06:00 (+08), delivered to
Discord **19:16**, and at 19:17 the post page still showed
*"Post is awaiting moderator approval"* with AutoModerator's stickied
source-rule comment and the OP's source/mirror reply under it.

Round 46 asked questions in this order:

```python
if listing_proves_release(in_listing, listing_source):   # 1st
    return None
if strong_hold_text:                                     # never reached
    return PENDING_APPROVAL
```

i.e. a post present in an **API-backed** `/new` listing was released without
the page's own banner ever being read. The round-46 assumption — "Reddit's
listing API excludes queued posts" — is therefore **not safe**: a queued post
can be visible in the listing.

### The change (`testing area/reddit_signals.py`, `queue_verdict`)

The two checks are swapped, and the precedence is documented in the
docstring:

1. **STRONG page text** ("awaiting moderator approval", "pending moderator
   approval", "sent to the moderators for review", "awaiting mod") → **HOLD**
2. an API-backed listing containing the post → release
3. WEAK text (AutoModerator source-rule comment) inside
   `MOD_QUEUE_WEAK_GRACE_SECONDS` → HOLD
4. round-38d negative space (API-backed listings only) → HOLD
5. otherwise → release

Nothing else changed: the regexes, the grace window, the fail-open rules for
unreadable pages/listings, and the whole fast-settle path are untouched. A
post with **no** banner is released by the listing exactly as before, so
posting speed for healthy posts is unchanged.

### Tests added (6 new, both suites, all run)

* `r48: 1wuwjiw — the banner holds the post whatever the listing says`
  (API-backed listing, RSS listing, absent from listing, unreadable listing)
* `r48: with NO banner an API-backed listing still releases instantly`
* `r48: the weak AutoMod signal still yields to an API-backed listing`
* `r48: the banner is checked before anything else in queue_verdict`
* `r48 wiring: 1wuwjiw is HELD even when the API-backed listing contains it`
* `r48 wiring: once the banner is gone the same post posts immediately`

Suite totals after round 48: smoke **ALL PASS**, signals **ALL PASS
(196 pass)**.

---

## I. ROUND 48c / 48d (2026-10-01) — proxy audit for profile posts, and one speed win

### 48c — what was audited (offline; this sandbox has no network egress)

`curl` to redditez.com, vxreddit.com, embeddit.deltandy.me and reddit.com all
fail from here (connection blocked), so the chain was audited against the
real module with fake sessions plus the committed `proxy_health.json`
warm-up record (all three services `ok: true`).

Findings for a PROFILE path (`/user/aphotide/comments/1wuv4j8/…`):

| Service | URL it builds | Profile path OK? |
|---|---|---|
| redditez (EmbedEZ) | `embedez.com/api/v1/providers/search?url=https://www.reddit.com/user/aphotide/comments/1wuv4j8/…` then `embedez.com/embed/<key>` | ✅ — the same post your `redditez.com/user/…` test rendered |
| vxreddit | `https://www.vxreddit.com` + the path verbatim | ✅ — the URL in your screenshot |
| embeddit | post id only (`/comments/<id>/`), path-agnostic | ✅ |

So **no proxy was ever the problem** for 1wuv547: the monitor simply never
asked for the original post, because the crosspost original
(`/user/…`) was not recognised. Round 47 fixes exactly that, and the
`/r/u_<name>/` alias is a belt-and-braces fallback that the canonical path
makes unnecessary in practice.

16 new offline checks: redditez asked first with the canonical permalink and
Discord's bot UA; a healthy redditez video wins; `Failed to Get Post` is
treated as a service outage and the chain moves on; vxreddit is asked on the
same path and its stats line parses; a text-only answer never wins a video
post (round 23); embeddit answers from the id alone; all-dead returns `None`
so the native path takes over; a warm-up-dead service is skipped; all-dead
forces a retry of everything; `og:video`/`og:image` classification.

### 48d — the speed win the audit exposed

Round 25 keeps querying the remaining services after a winner, in case one
has a **more complete gallery**. For a VIDEO post that can never happen —
a Reddit video post has one video and the card shows one player — so every
video post was paying **two useless proxy round-trips**.

```python
if need_video and any(m["kind"] == "video" for m in best_media_result["media"]):
    break      # chain complete, no gallery can beat it
```

Measured in the suite: a video post now costs **2 proxy requests instead of
4**. Gallery posts still shop the whole chain exactly as before.
