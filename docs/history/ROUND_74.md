# Round 74 — Reddit cold Discord video-proxy healing

**Status:** Shipped — [PR #63](https://github.com/uesu/News-Express/pull/63)
**Scope:** Reddit V3 only (`testing area/reddit_main_v3.py`)
**Date:** 2026-10-13

## Incident evidence

Evidence post: `r/Genshin_Impact_Leaks/1x4vzun` — `[7.2v3] Local Legend - Rowdy Beast Host`.

EmbedEZ returned a valid generated video URL and was selected after a validated
1080p candidate became available. Discord initially created a blank/cold video
tile: its response contained a Discord `proxy_url`, but did not yet include
complete media metadata. Manually editing that same message caused Discord to
populate `proxy_url`, dimensions and `video/mp4` metadata, after which the video
rendered normally.

This is distinct from provider failure. The generated URL and selected
provider were valid; Discord's own media proxy was still resolving.

## Detection and behavior

Initial media selection and delivery are unchanged. Reddit V3 continues to
select the best validated provider result and posts that URL once. The heal
inspector remains provider-agnostic and classifies video items by the existing
video-rendition URL or Discord `video/*` content type rules.

A video tile is queued when either condition is true:

1. **Existing explicit failure evidence:** Discord returns a non-positive
   width or height.
2. **Observed cold-proxy evidence:** the video has a Discord `proxy_url`, but
   does not yet have both positive numeric width/height values and a
   `video/*` content type.

A sparse response without a Discord proxy attempt remains unknown and does
not queue healing. A healthy video with positive dimensions and a video
content type is untouched. Images, photos, thumbnails and native Reddit media
remain outside the repair path; provider selection is not changed by the heal
pass.

## Bounded healing sequence

```text
post the selected card normally
        |
        v
video response has explicit invalid dimensions or a cold Discord proxy?
        |
        +-- no --> no healing request
        |
        +-- yes --> wait for the configured delay (default 6 seconds)
                         |
                         v
                  re-fetch the same Discord message
                         |
             +-----------+-----------+
             |                       |
       metadata valid          still unresolved
             |                       |
          no edit               one identical PATCH
```

The revalidation is URL-specific and happens before any edit. If Discord
resolves the media during the wait, no PATCH is sent. If the queued video is
still unresolved, at most one identical same-message edit is sent. The
existing delay clamp, one-edit bound, request timeout and fail-closed behavior
are unchanged. The initial post is not held while Discord resolves its proxy;
no provider search, full video download or conversion request is added.

## No-healing guarantees

No healing occurs for:

- photos or image galleries;
- healthy videos with positive dimensions and a `video/*` content type;
- sparse video metadata when Discord supplied no `proxy_url` and there is no
  explicit non-positive dimension;
- provider selection or fallback alone (including EmbedEZ being selected);
- a video that resolves before the delayed revalidation;
- Twitter/FxTwitter/VxTwitter posts.

The change reuses the existing Reddit V3 delayed revalidation and one-edit
path. It does not change provider ordering, media quality selection, the
initial URL, caching, or the Twitter implementation.

## Request bounds

| Scenario | Additional Discord work |
|---|---:|
| Photo-only post | None |
| Healthy video | None |
| Cold proxy resolves during the wait | 1 GET |
| Cold proxy remains unresolved | 1 GET + 1 PATCH |
| Repeated automatic edits | Not allowed |

## Validation

```text
python -m compileall -q "testing area" tests
python tests/test_smoke.py
python tests/test_reddit_signals.py
git diff --check
```

The smoke regression covers a proxy URL with incomplete video metadata,
positive dimensions with a missing video content type, a healthy rendered
proxy, sparse metadata without a proxy, image media, the outgoing-card video
scope, one delayed GET plus at most one PATCH, and a proxy that resolves before
revalidation. Existing explicit `0x0` behavior and prior bounded-healing
regressions remain covered.
