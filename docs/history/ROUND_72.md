# Round 72 — Reddit proxy-video cold-start media heal

**Status:** Shipped — merged in [PR #59](https://github.com/uesu/News-Express/pull/59)

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

The monitor follows the response-based pattern already proven by the Twitter
media-heal path:

1. Video cards use `wait=true` so Discord returns the created message JSON.
2. The returned Components V2 gallery media items are inspected.
3. A repair is queued only when Discord reports a video item with missing or
   zero width/height, or missing `content_type`.
4. Healthy videos are not edited.
5. Queued repairs run concurrently after the posting loop and perform one
   identical same-message edit.

Video detection uses the outgoing card's media kind together with Discord's
returned media metadata, not an allowlist of vxreddit, redditez, Embeddit,
EmbedEZ, or other provider hosts. It also handles extensionless video URLs
when the outgoing card identifies them as video. The pure inspector can
recognize an unresolved native `v.redd.it` video too, but **native Reddit
media is not queued for repair**: this round preserves its existing no-edit
behavior. For all non-native video providers the edit decision comes from
Discord's returned metadata, not the provider name. The returned URL must
match a video in the outgoing card; unrelated gallery images and thumbnails
cannot trigger a repair.

Images, text posts, resolved videos, native Reddit media, provider selection,
buttons, continuation components, YouTube previews, and cache behavior are
unchanged. An already-posted historical card is not automatically revisited;
that card must be manually edited if it needs repair.

## Performance and safety

Healthy video cards receive no PATCH/edit and no six-second heal delay. The
initial `wait=true` response is used only to inspect the message returned by
the same webhook POST; it does not add a second request. Only Discord-
unresolved non-native video cards receive the delayed PATCH. When
`RETRACT_DEAD_POSTS=1`, its original message ID and payload are still saved.

Repairs are bounded to one identical edit per unresolved video card, run
concurrently after delivery, and use a 15-second request timeout. A failed
or missing repair does not fail or undo the already-delivered card. There is
no retry loop, provider fallback change, cache reset, lower-resolution
fallback, or media-cap change.

## Configuration

```env
PROXY_VIDEO_HEAL=1
PROXY_VIDEO_HEAL_DELAY=6
```

Both optional repository Variables are wired in the Reddit workflow; empty
values use defaults. `PROXY_VIDEO_HEAL=0` disables the inspection/repair path.
The delay is clamped to 0–60 seconds and applies only after Discord has
reported unresolved non-native video metadata.

## Validation

```text
python -m compileall -q "testing area" tests
python tests/test_smoke.py
python tests/test_reddit_signals.py
git diff --check
```

The regression coverage includes zero-dimension detection, missing content
type, healthy video no-op behavior, native-video detection without edit,
provider-agnostic and extensionless URLs, opt-out behavior, same-payload
editing, error handling, retraction coexistence and workflow wiring.
