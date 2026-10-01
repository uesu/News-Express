# Round 47 — X media self-heal, the real video size limit, and profile-post crossposts

**Base:** `main` @ `b933006` (after PR #22 merged round 46b).
**Patch:** `docs/round_47.patch` — 5 files, `git apply --check` clean against a
fresh worktree of `b933006`; applied there and both suites run (see Tests).

---

## 1. X — "Image failed to load" on a video that is perfectly fine

### What actually happened

The message Discord stored for `Wuthering_Waves/2105598609827737874` contains:

```json
"media": {
  "url": ".../1920x1080/MKcWr_GC5zM6ZGX4.mp4?tag=29",
  "proxy_url": "https://images-ext-1.discordapp.net/external/F2rq…/…mp4",
  "width": 0, "height": 0, "content_type": ""
}
```

Discord **minted a proxy URL but never finished fetching the asset**: no
dimensions, no content type. A client with no dimensions and no content type
has nothing to render, so it paints the "Image failed to load" placeholder.
This is a known, long-standing media-proxy behaviour (discord-api-docs
issue #878 describes the identical `width: 0 / height: 0` signature).

So the diagnosis in your message is right in substance: it is a **cold
fetch** on Discord's side — the first time its proxy sees a brand-new
`video.twimg.com` rendition (fresh CDN object, served through Cloudflare,
~89 MB to pull) the probe does not complete inside the window Discord allows
while creating the message. It is **not** a bad URL, not fxembed, and not
your webhook: pressing **Edit** in Discohook with zero changes made the same
URL play, because an edit forces Discord to resolve the media again — and by
then its proxy has the object.

### The fix: the monitor now does that edit itself

* The webhook POST is now `?with_components=true&wait=true`, so Discord
  returns the **created message** instead of `204`.
* `unresolved_media_items(message)` walks the components tree and collects
  every media tile with `width`/`height` of 0 or an empty `content_type`.
* Any such message is queued as `(webhook_url, message_id, payload, key)`.
* **After the whole posting loop finishes**, `heal_unresolved_media()`
  `PATCH`es each queued message with the **identical payload** —
  nothing added, nothing removed — at
  `{webhook}/messages/{id}?with_components=true`, waits
  `MEDIA_HEAL_DELAY_SECONDS` (default **45 s**, inside your 30–60 s range),
  re-checks the returned message, and retries up to `MEDIA_HEAL_ATTEMPTS`
  (default 2) before giving up with a warning.
* All queued messages heal **concurrently** (`asyncio.gather`).

### Is there a performance loss? No.

| Step | Cost |
|---|---|
| `wait=true` | none — the same single HTTP request; Discord just returns a body instead of `204`. No extra round trip. |
| unresolved check | pure local JSON walk, microseconds |
| queueing | appends a tuple |
| the edit itself | happens **after every tweet of the run has been posted**, and only for messages that actually came back unresolved — normally **zero** |
| retries | bounded (`MEDIA_HEAL_ATTEMPTS`), never blocks a post |

Posting latency is byte-for-byte unchanged. The GitHub Actions job stays
alive ~45–90 s longer **only** on runs that had a cold-proxy video.

Config (optional repository Variables): `MEDIA_HEAL=off`,
`MEDIA_HEAL_DELAY_SECONDS`, `MEDIA_HEAL_ATTEMPTS`.

---

## 2. X — the 4K video did not need downgrading

You proved it by hand: swapping the 1080p rendition for the
**3840×2160, ~295 MB** original made the gallery play it. The old cap was
`VIDEO_SIZE_LIMIT = 256 MiB`, chosen in 2026-09 from "191 MB plays, 405 MB
fails". 295 MB sits in the untested gap — and it works.

* `VIDEO_SIZE_LIMIT` is now `int(os.getenv("VIDEO_SIZE_LIMIT_MB", "300")) * 1024 * 1024`.
* 405 MB and 521 MB remain confirmed failures, so 300 MiB keeps a margin.
* Effect on this exact tweet: it posts at **4K with no downgrade note**.

### About the Nitro 1 GB change

Discord raised the **Nitro upload limit from 500 MB to 1 GB** (announced
2026-09-29). It does **not** apply here: that limit governs files you
*upload as attachments*. Our videos are **external URLs** rendered through
Discord's media proxy, which has its own (undocumented) ceiling — the one we
measure empirically at ~300 MB works / ~405 MB fails. Nothing to gain by
raising the cap to 1 GB; it would just bring back "Image failed to load".
(If you ever wanted true 1 GB support you would have to download the file in
the runner and upload it as an attachment — slow, bandwidth-heavy, and it
breaks the "post as fast as possible" rule. Not recommended.)

---

## 3. Reddit — the crosspost that showed a still image instead of the video

`https://www.reddit.com/r/AnantaLeaks/comments/1wuv547/` is a crosspost of
**a profile post**: `https://www.reddit.com/user/aphotide/comments/1wuv4j8/`
— a post that lives on a user's own page, not in a subreddit.

Every crosspost helper in `reddit_main_v3.py` only recognised
`/r/<sub>/comments/<id>/`:

| Helper | Before |
|---|---|
| `normalize_reddit_path` | `re.search(r"(/r/[^\s?]+)")` → `None` for `/user/…` |
| `CROSSPOST_PERMALINK_RE` | `/r/…/comments/<id>/` only |
| Arctic original check | `re.fullmatch(r"/r/[^/]+/comments/…")` |

So the original was never resolved, no `v.redd.it` id was ever found, and
the card fell back to the crosspost's own `external-preview.redd.it` **poster
image** — exactly what you saw.

### Fix

* `normalize_reddit_path()` now also accepts `/user/<name>/comments/<id>/…`
  and the short `/u/<name>/…` form, returning the canonical `/user/…` path.
* `CROSSPOST_PERMALINK_RE` matches profile permalinks.
* The Arctic-Shift original permalink check accepts `/user/…`.
* New `is_profile_post_path()` and `_path_aliases()`: Reddit files a profile
  post under the pseudo-subreddit `u_<name>`, so
  `/user/aphotide/comments/1wuv4j8/` ≡ `/r/u_aphotide/comments/1wuv4j8/`.
  `fetch_proxy_post_memo()` and `enrich_gallery_redlib()` try the canonical
  route first and the alias **only if the first returned no media** — an
  ordinary subreddit post has exactly one route and makes exactly one call,
  so nothing gets slower.

Result: the crosspost resolves to the profile post, the profile post yields
its `v.redd.it` id, and the existing DASH ladder (`DASH_720/1080/480/360.mp4`,
self-contained h264+AAC) posts the **playable video with audio** instead of a
poster frame. This covers future crossposts of profile posts generally, not
just this one.

---

## 4. "Sorry, this post has been removed by the moderators of r/AnantaLeaks."

This one is **not** a gate failure, and nothing in rounds 46/46b/47 would
have stopped it:

* 1wuv547 was created 17:43:03 (+08) and posted to Discord at 17:50 — about
  7 minutes later.
* At that moment it was **live**: it rendered, it had the video, it was in
  the public listing. Your own screenshots show the content, with 1 upvote
  and 1 comment.
* The moderators removed it **afterwards** (your profile screenshot shows the
  removal banner on the same post an hour later, 0 comments).

A removal that happens *after* a correct publication can only be handled in
one of two ways:

1. **Wait longer before posting** — i.e. raise `POST_SETTLE_SECONDS` above
   the removal latency of that subreddit (minutes to hours). That directly
   contradicts "post as fast as possible", so: no.
2. **Retract after the fact** — the existing `RETRACT_DEAD_POSTS` path, which
  edits the Discord message once the post is found dead. You ruled retraction
  out while it cost posting time; it no longer has to. Round 47 just built a
  **post-run edit lane** for X that runs strictly after everything is posted.
  The identical shape works for Reddit: a sweep after the posting loop that
  re-checks the last N posted links and edits dead ones. Still **opt-in and
  default off**, still zero latency cost. Say the word and I will wire it.

So: nothing is "wrong" in the gate for this post. The queue gate protects
against posts that were *never released*; this one was released and then
pulled.

---

## 5. Speed status after this round

Nothing in round 47 touches the Reddit posting path's hot loop. The current
latency budget (unchanged, from round 46b) is:

| Stage | Cost |
|---|---|
| cron tick (cron-job.org) | every 5 min — the floor |
| `/new` listing | one concurrent batch, API-backed answer wins, < 0.5 s healthy |
| settle | 60 s when an API-backed listing confirms the post, else 300 s |
| mod-queue gate | one page fetch across mirrors, concurrent |
| Discord send | one request |

The only remaining structural latency is the **cron interval itself**. If you
want faster than ~5 min, the interval has to shrink; nothing in the code is
the bottleneck any more.

---

## 6. Discohook / API check

* Discohook is a **client**, not an API we depend on — the monitor talks to
  Discord's webhook API directly (`POST /webhooks/{id}/{token}` and
  `PATCH /webhooks/{id}/{token}/messages/{message_id}`), which is what round
  47 uses. No change there.
* Discohook's Components-V2 support is still the beta editor you already use;
  there is no new public Discohook API to adopt, and nothing it offers would
  make posting faster or more reliable than the direct webhook calls.
* The only genuinely relevant platform change found is the Nitro upload limit
  (500 MB → 1 GB, 2026-09-29), which, as explained above, does not apply to
  linked/external media.

---

## Tests actually run (executed, not claimed)

On a clean worktree of `main` @ `b933006` with `docs/round_47.patch` applied:

* `python3 tests/test_smoke.py` → **ALL PASS** (21 new r47 checks)
* `python3 tests/test_reddit_signals.py` → **ALL PASS (190 pass)**
* `python3 -m compileall -q "testing area" tests` → clean

New checks include:

* the **exact** broken payload from your message is detected as unresolved;
  a healthy tile is not (so no pointless edits);
* one unresolved message is re-edited exactly once when that fixes it, with
  the identical payload, to `…/messages/{id}?with_components=true`;
* a permanently unresolvable asset is retried `MEDIA_HEAL_ATTEMPTS` times and
  then dropped (no infinite loop);
* **measured**: a healthy run performs zero edits and zero waiting;
* the posting call uses `wait=true`, and healing is proven to run *after* the
  posting loop;
* 295 MB is inside the new limit while 405 MB is still outside;
* profile-post normalisation (`/user/…`, `/u/…`), alias generation,
  `1wuv547` → `1wuv4j8` crosspost resolution, Arctic acceptance, the proxy
  alias retry recovering the `v.redd.it` video, and the proof that an
  ordinary post still makes exactly one proxy call.
