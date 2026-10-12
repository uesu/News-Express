# Round 72 — Reddit proxy-video cold-start media heal

**Status:** Shipped — merged in [PR #59](https://github.com/uesu/News-Express/pull/59);
precision follow-up in this PR

**Scope:** Active Reddit V3 video delivery across all configured subreddits

**Date:** 2026-10-12

## Problem

A Reddit video endpoint can be reachable before Discord has completed its
media probe. The initial Components V2 card may then contain a media item with
`width: 0`, `height: 0`, and an empty `content_type`, which appears as
`Image failed to load`. The same URL can become playable shortly afterward.

The observed incident was an AnantaLeaks vxreddit video. Other Genshin cards
in the same testing period returned valid dimensions and rendered correctly.

## Detection and behavior

The monitor now follows the response-based pattern already proven by the
Twitter media-heal path:

1. Video cards use `wait=true` so Discord returns the created message JSON.
2. The returned Components V2 media items are inspected.
3. A repair is queued only when Discord explicitly reports a video item with
   a non-positive width or height. Omitted width/height/content-type fields are
   treated as unknown rather than failure, preventing healthy sparse responses
   from causing unnecessary edits.
4. Healthy videos are not edited.
5. Queued candidates wait for the configured delay, then re-read the complete
   existing Discord message (including Components V2 metadata). If the media
   is now healthy or the revalidation response is sparse, no PATCH is sent.
   Only a still-explicitly-unresolved video receives one identical same-message
   edit; repairs remain concurrent after delivery.

This is provider-agnostic. The decision is based on Discord's returned media
metadata, not on whether the URL belongs to vxreddit, redditez, Embeddit,
EmbedEZ, or another supported provider. It applies to future posts in every
configured subreddit, including subreddits added later.

Images, text posts, resolved videos, native Reddit media, provider selection,
buttons, continuation components, YouTube previews, and cache behavior are
unchanged. An already-posted historical card is not automatically revisited;
that card must be manually edited if it needs repair.

## Follow-up precision correction (2026-10-12)

The first shipped version (PR #59) inspected the create response and PATCHed a
queued card after a fixed delay. Production then showed the failure mode that
had already been learned on the Twitter side: Discord's create response can
report `0x0` / missing metadata for a card that is already playable, so an edit
was sent for cards that needed no repair — and a missing `content_type` alone
was being treated as "unresolved", which is exactly what a *healthy sparse*
response looks like.

Two bounded corrections, both in the same one-card path:

1. **Only explicit evidence is heal-eligible.** A tile queues a repair only
   when Discord returns a non-positive `width` or `height` (the documented
   cold-proxy shape, normally `0 x 0`). Omitted fields, `null`, non-numeric
   values, and an empty `content_type` are *unknown*, never failure. Video
   classification is still provider-agnostic: a video rendition URL
   (`.mp4`/`.m4v`/`.mov`/`.webm`/`.m3u8`) or Discord's own `video/...`
   content type — no proxy hostname list. An extensionless URL that carries no
   video content type is therefore left untouched (unknown ⇒ no edit).
2. **The edit revalidates before it changes anything.** After the delay the
   monitor re-reads the delivered message (`GET
   /messages/<id>?with_components=true`) and PATCHes the identical payload only
   if the media is *still* explicitly unresolved. A healthy or sparse
   revalidation means no edit; a failed revalidation (HTTP error, non-JSON
   body, network exception) fails closed and never fails the delivered card.

Native Reddit media, ordinary posts, images, provider selection, buttons,
continuations, YouTube previews, cache behavior, and the `RETRACT_DEAD_POSTS`
message-ID/payload record are unchanged. A returned video that the outgoing
card did not carry as a non-native video still cannot trigger a repair.

## Performance and safety

Healthy video cards receive no PATCH/edit and no six-second heal delay. The
initial `wait=true` response is used only to inspect the message returned by
the same webhook POST; it does not add a second request. Only a card Discord
explicitly reports as unresolved receives the delayed revalidation read (and,
only if it is still unresolved, the identical edit).

Repairs are bounded to one identical edit per unresolved video card, run
concurrently after delivery, and use the existing 15-second request timeout.
A failed or missing repair does not fail or undo the already-delivered card.
There is no retry loop, provider fallback change, cache reset, lower-resolution
fallback, or media-cap change.

## Configuration

```env
PROXY_VIDEO_HEAL=1
PROXY_VIDEO_HEAL_DELAY=6
```

The feature is enabled by default. `PROXY_VIDEO_HEAL=0` disables repairs.
The delay is clamped to 0–60 seconds and applies only after Discord has
reported unresolved video metadata. Both Variables are workflow-wired, and
empty values use the documented defaults.

## Validation

```text
python -m compileall -q "testing area" tests
python tests/test_smoke.py
python tests/test_reddit_signals.py
git diff --check
```

The regression coverage includes zero-dimension detection, missing content
metadata, healthy video no-op behavior, native-video no-op behavior, provider-
agnostic URLs, opt-out behavior, same-payload editing, error handling, and
future-post workflow wiring.
