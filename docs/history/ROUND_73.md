# Round 73 — Twitter mixed-media order + GIF fallback quality

**Status:** Open — [PR #62](https://github.com/uesu/News-Express/pull/62)
**Scope:** Active X/Twitter V3 delivery (`testing area/twitter_v3.py`) for all
configured accounts, quoted tweets and in-article media
**Date:** 2026-10-13

## Problem

Two media-presentation defects in the X (Twitter) V3 card:

1. **Mixed-media posts lost their source order.** The gallery was assembled
   from the API's per-type subsets — every `media.videos` entry first, then
   every `media.photos` entry — so a tweet whose own order is
   `JPG → GIF 1 → GIF 2 → GIF 3` reached Discord as `GIF, GIF, GIF, JPG`.
   FxEmbed/FxTwitter has always returned the tweet's real order in
   `media.all` (`mediaList.forEach` in its processor pushes each
   `extended_entities` entry into `all` and into the matching type subset —
   verified in the FxEmbed source, not inferred).
2. **GIF fallback selection was optimistic about URLs.** The round-11 chain
   accepted the first converter URL that answered HTTP 200 with *any*
   `image/*` content type, and it never considered the AVIF rendition
   `gifconvert` actually serves. An `.avif` tile can look static in Discord's
   gallery preview while still animating once opened, so a "converted" GIF
   could reach a channel looking like a frozen picture — worse than the mp4
   player it replaced.

## Behavior after this round

### Canonical source order

`canonical_media_entries(media)` returns one ordered list:

* `media.all` when the API returns it — the tweet's own order, with photos
  and videos/GIFs interleaved exactly as posted;
* otherwise the legacy `videos` then `photos` order, verbatim.

`collect_media()` walks that single list, so a photo is emitted where the
tweet put it and every GIF/video keeps its chronological position relative to
the other GIFs/videos. Details:

* **Photo-only and video-only posts with valid media URLs preserve their
  previous order and output** — `all` reproduces the subset order in both
  cases. Entries without a usable URL are safely omitted instead of becoming
  empty gallery tiles (the one deliberate difference for malformed payloads).
* **Provider fallback keeps its documented behavior.** The vxtwitter and
  twitterez normalizers do not produce `media.all`, so they keep the
  videos-then-photos order.
* Entries without a usable URL are dropped rather than emitted as an empty
  tile, and the tweet payload is never mutated (ordering is an in-memory
  operation, no extra request).
* `media_entry_is_video()` classes an entry by the API's own `type`
  (`photo` / `video` / `gif`) and falls back to the video-only keys
  (`formats` / `thumbnail_url` / `duration`) when a payload omits it.

### GIF fallback priority

The chain is `gif_converter_candidates(video_url)` — the same four candidates
as round 11, unchanged URLs and unchanged order: `gif.fxtwitter` `.webp` →
`gifconvert` `.webp` (Referer-gated) → `gifconvert` `.gif` → `fastgif` `.gif`.

The pass is split so a caller never pays for it twice:

* `probe_gif_candidates(session, video_url)` — **one** pass over those four
  candidates (≤ 4 HEADs). It returns `(url, source, avif_url, avif_source)`:
  the first *animated* answer and the first AVIF answer seen along the way.
* `probe_gif_avif_routes(session, video_url)` — the AVIF-only routes
  (`gif.fxtwitter` `.avif`, then `gifconvert` `/convert.avif`, ≤ 2 HEADs),
  asked **only** when the caller already knows the mp4 is unusable and the
  first pass remembered no AVIF.
* `resolve_gif_image(session, video_url, allow_avif=False)` — the single-GIF
  convenience wrapper over both; with `allow_avif=True` it reuses the AVIF
  remembered by its own pass and only then asks the AVIF routes.

Answers are classed by the **returned** `Content-Type`, never by the URL
extension:

| Returned type | Tier | Use |
|---|---|---|
| `image/webp`, `image/gif` | animated | wins immediately (first match short-circuits) |
| `image/avif`, `image/heic`, `image/heif` | AVIF | remembered; returned only when `allow_avif=True` and no animated answer exists |
| any other `image/*` | static | not preferred (the mp4 outranks a still picture) |
| anything else / no answer | — | chain continues |

`collect_media()` therefore keeps the **original mp4** whenever an animated
rendition is unavailable — never an AVIF. The AVIF is used exactly once per
GIF, as a last resort, only for a GIF that has *no* playable gallery
rendition: the mp4 is oversized, no smaller `formats[]` variant fits, and no
animated WebP/GIF answered. In that one case the chain is **not** re-probed —
an AVIF already remembered by that GIF's single pass is reused, and only if
that pass found none are the AVIF routes asked — and the tile is the AVIF URL
that actually answered, logged with its source as `<source>-avif`; the card no
longer falls back to a static poster. If no AVIF answers either, the round-11
terminal behaviour stands: thumbnail + "▶️ Watch it on X" note.

## What deliberately did not change

* **No new environment variable** and no change to `MEDIA_HEAL`,
  `MEDIA_HEAL_SCOPE`, `MEDIA_HEAL_DELAY_SECONDS`, `MEDIA_HEAL_ATTEMPTS`,
  `VIDEO_SIZE_LIMIT`, `GALLERY_VIDEO_LIMIT`, `PORTRAIT_PROXY` or the probe
  order of the chain.
* **The evidence-based heal contract (rounds 47/56/70).** Healthy media is
  posted immediately with no delay, no revalidation request and no edit; only
  media Discord explicitly reports as unresolved (a non-positive
  width/height) and that is eligible for the configured scope — video
  renditions by default — enters the in-memory queue, which runs after the
  posting loop and PATCHes the identical payload, bounded by the attempt cap.
  A provider fallback on its own never queues a heal, and a converted
  `.webp`/`.gif` tile stays out of the default scope.
* Reddit, the caches, the workflows (other than CI running the new suite) and
  the X V1/V2 engines.

## Performance

| Path | Cost |
|---|---|
| Healthy FxTwitter tweet (photo-only) | unchanged — zero probes for photos |
| Healthy GIF (`gif.fxtwitter` answers) | unchanged — one HEAD, short-circuit |
| Video | unchanged — one size probe, no converter traffic |
| Converter unavailable | one HEAD per remaining candidate (as in round 11) |
| GIF with an animated rendition **or** a playable mp4 | ≤ 4 converter HEADs (one pass) + one mp4 size probe — **no AVIF route is ever asked** |
| GIF with no animated rendition and no playable mp4 | the same ≤ 4 converter HEADs (never repeated) + ≤ 2 AVIF-route HEADs — the only added round-trips in the whole round |

The last-resort path is bounded at **≤ 6 HEADs** (4 chain + 2 AVIF routes),
and the chain is probed exactly once per GIF: an AVIF remembered during that
single pass is reused rather than re-discovered, so the four candidates are
never probed twice. Every other path costs at most what round 11 cost.

Ordering itself is in-memory only. Healing work is unchanged: zero edits and
zero wait when Discord reports healthy media.

## Validation

```text
python -m compileall -q "testing area" tests
python tests/test_smoke.py            # SMOKE TEST: ALL PASS
python tests/test_reddit_signals.py   # REDDIT SIGNAL TEST: ALL PASS (96 pass)
python tests/test_twitter_media.py    # TWITTER MEDIA TEST: ALL PASS
git diff --check
```

`tests/test_twitter_media.py` (new, wired into CI) is the focused suite for
this round: canonical source order for photo-only / video-only / mixed /
legacy payloads, the observed live `JPG → GIF 1 → GIF 2 → GIF 3` shape
end-to-end through `collect_media()`, the converter probe order, the
content-type rules (including a `.gif` URL that answers `video/mp4` being
rejected), mp4-over-AVIF priority, the AVIF last resort, the direct-mp4
fallback, and the healthy-media / explicit-unresolved-evidence heal contract
with its request counts.

The performance contract is asserted, not just documented: the suite counts
probes per URL and pins that (a) no converter candidate is ever probed twice
on the last-resort path, (b) the animated chain contributes ≤ 4 HEADs and the
AVIF routes ≤ 2, (c) an AVIF remembered by the first pass is reused with the
AVIF routes never asked, and (d) a card whose mp4 plays probes the chain once
plus the mp4 size and nothing else.

The round-11 and round-47/56/70 smoke guards (`tests/test_smoke.py`) pass
unchanged — including the `twitter_proxy` GIF-chain order assertions, which
this round intentionally leaves alone.
