# Round 72 — Reddit proxy-video cold-start media heal

**Status:** In review — follow-up PR pending

**Scope:** Active Reddit V3 generated proxy-video delivery

**Date:** 2026-10-12

**Predecessor:** Round 71 Reddit Markdown-table readability

## Problem

A generated proxy-video URL can be reachable and downloadable before Discord
has completed its own media probe. The initial Components V2 card can then
show a one-off `0 × 0` media record or `Image failed to load`, even though
the same proxy URL becomes playable moments later in a browser and in
Discord after a manual edit.

The observed case used a vxreddit CMAF gateway URL. The monitor successfully
validated the video bytes, but Discord received the card while the proxy
render endpoint was still becoming ready. This is a transient media-probe
readiness issue, not a Reddit delivery failure or a bad source video.

## Behavior

The initial Reddit V3 post remains unchanged. For cards containing a generated
proxy-video URL, the monitor:

1. posts the card normally;
2. receives the message ID using the webhook's `wait=true` response;
3. once all cards and follow-ups have been delivered, waits the bounded
   `PROXY_VIDEO_HEAL_DELAY` interval (multiple repairs wait concurrently);
4. edits the same Discord message once with the identical Components V2
   payload, allowing Discord to re-fetch the now-ready media URL.

The repair covers generated proxy-video URL shapes from vxreddit, redditez,
Embeddit-style proxies, and EmbedEZ render-video endpoints. Host and path are
matched rather than trusting arbitrary URLs containing a proxy-looking query
string. It does not replace the provider winner, change the media URL,
delete/repost the message, or lower video quality. A missing message ID or a
failed PATCH logs/skips the repair without failing the already delivered card.

Native Reddit media, images, text posts, buttons, cache behavior, provider
selection, continuation components, and YouTube previews are unchanged.

## Configuration

```env
PROXY_VIDEO_HEAL=1
PROXY_VIDEO_HEAL_DELAY=6
```

Both optional repository Variables are wired in the Reddit workflow; empty
values use defaults. Setting `PROXY_VIDEO_HEAL=0` disables the repair. Delay
is in seconds, clamped to 0–60, and applies only to generated proxy-video
cards.

## Performance and safety

Normal posts have no additional wait or edit. Affected proxy-video cards
receive one same-message edit after the initial post; deferring repairs until
after the posting loop avoids delaying subsequent posts. There is no retry
loop, provider fallback change, cache reset, lower-resolution fallback,
media-cap change, or remote request before the normal post. The PATCH has
a 15-second request timeout. Enabling the opt-in dead-post retraction seatbelt
still stores the original message ID and payload for future tombstones.

An already-posted historical card is not automatically revisited. Existing
failed cards must be manually edited once if they need repair; this feature
applies to future delivery attempts.

## Validation

```text
python -m compileall -q "testing area" tests
python tests/test_smoke.py
python tests/test_reddit_signals.py
git diff --check
```

Results in this checkout: `SMOKE TEST: ALL PASS` and
`REDDIT SIGNAL TEST: ALL PASS (96 pass)`.

Offline smoke guards cover eligible and ineligible URLs, feature opt-out,
workflow wiring, bounded same-payload edit behavior, error handling, and the
conditional `wait=true` response path (including a mocked main-loop delivery).
