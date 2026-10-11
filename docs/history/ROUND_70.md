# Round 70 — Bounded Twitter Discord Media Healing

**Status:** Proposed in PR #57
**Scope:** Active Twitter V3 media delivery
**Date:** 2026-10-11

## Problem

Discord can initially return a Components V2 video gallery item with zero
width and height and an empty content type. The client then shows "Image
failed to load", even though the direct `video.twimg.com` URL is valid and can
play after a later message edit.

## Decision

Raise the default same-payload media-heal attempts from 2 to 4 and keep the
45-second delay between edits. The attempt count is hard-capped at 4:

```python
MEDIA_HEAL_ATTEMPTS = min(4, max(1, _env_int("MEDIA_HEAL_ATTEMPTS", 4)))
```

A repository Variable can lower the count, but it cannot raise it above 4.

## Why the same URL is retried

A live check showed an unchanged 1920×1080 Twitter URL that initially returned
Discord metadata of 0×0 with an empty content type, then resolved after a
manual edit. The failure is therefore plausibly a temporary Discord
external-media proxy condition, not a bad URL.

## Performance

- Healthy media exits immediately and receives no heal delay.
- An unresolved video gets up to four re-edits at 45-second intervals: a
  maximum of about 180 seconds of scheduled waiting, versus 90 seconds before,
  plus PATCH round trips.
- Heal tasks for multiple messages run concurrently, so wall-clock cost is
  bounded by the slowest task rather than the sum.

## Unchanged safeguards

- 256 MiB preflight video safety cap.
- Video-only heal scope (`MEDIA_HEAL_SCOPE=video`).
- Components V2 layout and direct Twitter media URLs.
- Cache, workflow concurrency, provider, and feed behavior.

## Not in this round

- No automatic 4K-to-1080p/720p variant switching.
- No persistent cross-run healing.

## Limitation

The monitor can verify that Discord resolved the media metadata. It cannot
simulate every client's playback environment, so this raises the odds of
recovery but does not guarantee playback for every external video.
