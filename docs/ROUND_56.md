# Round 56 — media heal targets videos only (decision record)

> **Purpose of this document:** capture WHY the Twitter media-heal pass is
> scoped to videos, what evidence that decision rests on, and exactly how to
> widen the scope again if images are ever seen broken. Future sessions:
> read this before touching `MEDIA_HEAL*` in `testing area/twitter_v3.py`.

## History

* **Round 47 (2026-10-01).** The first and only confirmed broken tile in
  production: `Wuthering_Waves/2105598609827737874` — a **video** posted
  with `"width": 0, "height": 0, "content_type": ""` in the stored message,
  rendering as an "Image failed to load" tile. An identical-payload edit
  (Discohook Edit with no changes) made the same URL play. The monitor
  learned to do that edit itself: post with `wait=true`, inspect the created
  message, re-PATCH anything unresolved after 45 s. Round 49 extended the
  detection to thumbnails/section accessories.
* **2026-10-02 observation.** Three **photo** posts triggered the heal:
  `PomPom_HonkaiSR/2105885490486427815` (1 item, ja),
  `PomPom_HonkaiSR/2105870388106322223` (2 items, the coffee quote) and
  `TYPEII_EN/2105870393584074977` (1 item). Discord's create response
  reported their image tiles as unresolved (same zero-metadata shape), and
  the heal edited each message once. **But the owner saw the live messages
  BEFORE the edit and the photos were already rendering fine.** The heals
  were harmless no-ops visually — identical payload, no "(edited)" marker —
  but unnecessary: ~45–50 s extra run time and a misleading log line
  ("the video now plays" for photos).

## Why images do not need the heal

An image tile renders from its raw/proxy URL even while Discord's media
probe is still cold — the client just fetches the picture. A **video** tile
is different: the player will not start without resolved metadata, which is
exactly what round 47 hit. In production, cold-image metadata has never
produced a visibly broken tile; cold-video metadata has.

## The change (round 56)

* `is_video_media_url(url)` — True for `.mp4/.m4v/.mov/.webm/.m3u8`
  (case-insensitive, query/fragment tolerated) or any `video.twimg.com`
  URL. X "GIFs" ship as `tweet_video/*.mp4`, so they stay covered — they
  use the same player. Converted GIFs (`.gif`/`.webp` image files from
  gif.fxtwitter/gifconvert) and photos are **not** heal-eligible.
* `heal_eligible_items(message)` — `unresolved_media_items(message)`
  filtered to video URLs. Used at both heal decision points (queueing after
  the POST, and the resolved-check after each PATCH edit).
* `unresolved_media_items()` itself is **unchanged** — it still detects
  every cold tile; only the heal's scope narrowed.
* Log wording fixed: success line now says "the media now renders" (the old
  "the video now plays" was hardcoded from the round-47 incident); the
  queue line reports `heal-eligible` items and the active scope.

## If a photo/GIF/webp tile IS ever seen broken

Set the repository **Variable** `MEDIA_HEAL_SCOPE=all` (Settings →
Secrets and variables → Actions → Variables) in the Twitter prod repo —
no code change needed. That restores the full round-47 behaviour: every
unresolved media item of any type is healed. The default (`video`) also
survives an empty/unset Variable (GHA empty-string pitfall, round 53
pattern: `(os.getenv(...) or "video").strip().lower() or "video"`).

## What did NOT change

* The heal mechanism itself: identical-payload PATCH, 45 s delay, 2
  bounded attempts, runs strictly AFTER the posting loop (zero delivery
  latency), opt-out via `MEDIA_HEAL=off`.
* `unresolved_media_items()` detection (rounds 47/49) — byte-identical.
* The video path: a cold video queues and heals exactly as before.

## Test coverage (tests/test_smoke.py, ROUND 56 block)

Video-URL detection (mp4 with query tag, tweet_video mp4, uppercase m3u8,
webm with fragment), image exclusion (jpg/png/gif/webp/empty/None), mixed
cold message heals only the video, photos-only cold message queues nothing
(the 2026-10-02 case), video-only message unchanged vs round 47,
`MEDIA_HEAL_SCOPE=all` restores images, `unresolved_media_items` unchanged,
and the default scope is `video`.
