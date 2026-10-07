# Video-Only Quality Update — Confirmation Policy

**Status:** Confirmed — implemented by round 67 / PR #53
**Scope:** Reddit-hosted video posts only
**Related change:** Round 67 / PR #53
**Non-goal:** This document does not change the content-advisory removal policy, which is already final.

## 1. User-approved objective

The current News-Express behavior is reliable and must remain reliable. The newest update is intended only to provide a potential quality improvement for Reddit-hosted videos.

The update must:

- Preserve the existing provider structure for every media type.
- Keep the existing general priority for photos, images, GIFs, and galleries: vxreddit first, EmbedEZ second, Embeddit third; stop after the first usable provider and do not continue unnecessary provider requests.
- Add a video-only quality attempt so EmbedEZ/RedditEZ can provide the original/highest validated video quality when available.
- Keep vxreddit as the reliable video path and automatic fallback.
- Automatically use vxreddit when the video quality attempt fails or produces unusable output.
- Use the existing/default EmbedEZ/RedditEZ video result only when vxreddit is unavailable or unusable.
- Require no manual variable change before the update becomes effective.

This is a video-quality enhancement, not a replacement of the established media-provider structure or vxreddit reliability path.

## 2. Required provider structure and video decision

### 2.1 Existing provider structure for all media

The existing provider priority remains in force for photos, images, GIFs, and galleries:

```text
vxreddit → EmbedEZ/RedditEZ → Embeddit
```

This is the provider priority and tie-break policy, not necessarily a serial request sequence. The current resolver uses bounded concurrent waves: it can test the first eligible providers, holds back the later provider, stops when a decisive usable result is available, and cancels or avoids unnecessary remaining work. A bounded gallery grace period may still allow a slower provider to contribute a more complete gallery when appropriate.

For those media types, a usable winner must stop unnecessary provider requests. If vxreddit succeeds, the resolver must not continue to EmbedEZ/RedditEZ or Embeddit merely to make extra requests. This behavior is outside the video-quality change and must remain unchanged.

### 2.2 Video-only quality enhancement

For an eligible Reddit-hosted video, preserve the current proxy architecture and its vxreddit-first tie-break. The already validated proxy video is the held base. The quality enhancement then makes one bounded EmbedEZ/RedditEZ 1080p opportunity when a video id and the per-run budget allow it:

```text
Select the validated proxy video using the existing provider waves.
        |
        +-- vxreddit is the preferred/reliable base when available.
        |
        +-- Hold the validated base video.
                |
                +-- Probe EmbedEZ/RedditEZ original/highest quality.
                        |
                        +-- Valid, usable, Discord-compatible improvement
                        |       -> use the EmbedEZ/RedditEZ video URL.
                        |
                        +-- Error, timeout, unavailable, invalid, oversized,
                            wrong content, unusable audio, or any other failure
                                -> keep the held base video unchanged.

If vxreddit is unavailable or unusable:
        -> the existing provider selection may use the normal/default
           EmbedEZ/RedditEZ video result as the base.
        -> continue through the existing fallback order only if needed.
```

The quality probe is video-only. It must never change the existing provider behavior for images, photos, GIFs, or ordinary galleries. EmbedEZ/RedditEZ may improve video quality, but it must never become a reliability dependency. Any failed quality attempt preserves the already validated base; when that base is vxreddit, the result is simply vxreddit.

## 3. Winner and fallback rules

### 3.1 Validated EmbedEZ/RedditEZ 1080p

EmbedEZ/RedditEZ may replace vxreddit only when the delivered result is validated as usable. Validation should include, where practical:

- Successful HTTP response.
- Video content type.
- Rejection of HTML or JSON error bodies, including error bodies returned with HTTP 200.
- Bounded range/body probing.
- Candidate timeout and overall post budget.
- Maximum-size enforcement.
- Real MP4/container evidence rather than trusting `1080` in a URL.
- Best-effort video dimensions.
- Best-effort usable audio-track evidence.
- Discord-compatible MP4 behavior.

A URL containing `1080` is never, by itself, proof of 1080p output.

### 3.2 EmbedEZ/RedditEZ failure

Any of the following must preserve the already validated base result. When vxreddit is valid, that base is vxreddit; when vxreddit is unavailable and the existing provider chain selected a valid default EmbedEZ/RedditEZ video, that validated EmbedEZ/RedditEZ base must remain available:

- Connection failure.
- DNS or proxy failure.
- HTTP error.
- Timeout.
- Empty response.
- HTML error page.
- JSON error response.
- Wrong content type.
- Invalid or incomplete MP4.
- Unusable dimensions.
- Missing or unusable audio where detectable.
- Size-limit violation.
- Any exception or unexpected provider response.

The post must not fail merely because EmbedEZ/RedditEZ failed when vxreddit is usable.

### 3.3 EmbedEZ/RedditEZ 720p

EmbedEZ/RedditEZ 720p must not replace a healthy vxreddit result.

The 720p rung may only be considered when the vxreddit base itself is unusable, subject to the resolver's bounded time and size budgets. It is not the normal result for a post where vxreddit already validated successfully.

### 3.4 Native Reddit fallback

Durable native `v.redd.it` DASH/video candidates may be used as a lower fallback when the proxy candidates are unusable and the native result is durable and valid.

Signed or expiring `packaged-media.redd.it` URLs must not be used as durable Discord media URLs and must not be persisted in cache/state.

### 3.5 Final fallback

If no usable video remains, preserve the existing safe fallback:

```text
thumbnail + Read Post button
```

A failed video enhancement must not prevent the post from being delivered through the existing fallback flow.

## 4. Effective mode

The newest update is expected to be effective without requiring a new repository variable to be added first.

The intended default is therefore the quality-aware video mode:

```text
missing or empty REDDIT_VIDEO_QUALITY -> balanced
```

In `balanced` mode:

- vxreddit remains the held reliability result;
- EmbedEZ/RedditEZ 1080p is tried as the optional quality upgrade;
- a valid EmbedEZ/RedditEZ result may win;
- any EmbedEZ/RedditEZ failure returns to vxreddit;
- EmbedEZ/RedditEZ 720p cannot displace healthy vxreddit.

If a rollback mode exists, `compatibility` may preserve the pre-quality-enhancement ladder. `highest` must remain an explicitly more aggressive/canary mode unless the final confirmed implementation states otherwise. No mode may weaken the vxreddit fallback rule.

## 5. Expected quality of future posts

The system must not promise that every future post will be highest quality. The result depends on the actual delivered media and the external provider's availability.

Expected outcomes are:

| Condition | Expected card video |
|---|---|
| Validated EmbedEZ/RedditEZ 1080p | EmbedEZ/RedditEZ proxy URL |
| EmbedEZ/RedditEZ fails and vxreddit is valid | vxreddit URL |
| EmbedEZ/RedditEZ is flaky or unavailable and vxreddit is valid | vxreddit URL |
| EmbedEZ/RedditEZ 1080p is invalid but vxreddit is valid | vxreddit URL |
| vxreddit is invalid and 720p is usable | Allowed lower-quality fallback, subject to budget |
| Proxy candidates fail but durable native video is usable | Durable native Reddit URL |
| No usable video remains | Thumbnail plus Read Post |

The normal reliable result remains vxreddit unless the validated EmbedEZ/RedditEZ result is a safe quality improvement.

## 6. Request and performance expectations

The resolver must remain bounded and must not wait indefinitely for a flaky provider.

Required safeguards include:

- Per-candidate timeout.
- Per-post time budget.
- Per-run quality budget.
- Maximum response/body size.
- Bounded probe range.
- Bounded probe concurrency.
- Immediate fallback to a validated vxreddit result when the quality candidate fails.
- No candidate URL, temporary media, or proxy state persisted to cache/state JSON.

The quality attempt is allowed only on video paths. It must not add provider requests to image, GIF, photo, or ordinary gallery paths.

## 7. Unchanged behavior

This update must not alter:

- Image extraction or delivery.
- GIF extraction or delivery.
- Photo extraction or delivery.
- Gallery photo extraction, ordering, count, or marking.
- Gallery behavior except that a Reddit-hosted video item may use the video-only resolver.
- Cache/state format or deduplication behavior.
- Fresh-hold behavior.
- Listing confirmation.
- Pending recheck throttling.
- Retraction behavior.
- Webhooks.
- Secrets.
- Scheduling.
- Proxy priority outside the video resolver.
- The completed content-advisory removal policy.

The active repository must continue making no content-based posting decision.

## 8. Required tests before deployment

The full local suite must pass before any production upload:

```bash
python -m compileall -q "testing area" tests
python tests/test_smoke.py
python tests/test_reddit_signals.py
```

The video-specific tests must cover at least:

- Valid EmbedEZ/RedditEZ 1080p wins over a valid lower-quality candidate.
- Valid vxreddit remains available as the fallback.
- EmbedEZ/RedditEZ timeout returns vxreddit.
- EmbedEZ/RedditEZ connection/provider error returns vxreddit.
- EmbedEZ/RedditEZ unavailable response returns vxreddit.
- EmbedEZ/RedditEZ HTML/JSON error body is rejected.
- Invalid content type is rejected.
- Invalid or incomplete MP4 is rejected.
- Missing or unusable audio is rejected where detectable.
- Oversized output is rejected.
- A URL containing `1080` without matching delivered evidence is rejected.
- EmbedEZ/RedditEZ 720p never displaces healthy vxreddit.
- 720p is only reachable when vxreddit is unusable.
- Signed/expiring packaged-media URLs are rejected as durable output.
- Native fallback remains available.
- Thumbnail plus Read Post remains available when all video candidates fail.
- Images, GIFs, photos, and ordinary gallery paths do not call the video quality resolver.
- A gallery video may use the video resolver while gallery photos remain intact.
- Cache/state behavior remains unchanged.
- Posting, deduplication, fresh-hold, listing confirmation, and retraction behavior remain unchanged.

## 9. Acceptance checklist

Before confirming the update:

- [x] EmbedEZ/RedditEZ is used only for Reddit-hosted video quality improvement.
- [x] vxreddit is still the primary held reliability result.
- [x] Valid EmbedEZ/RedditEZ 1080p may win.
- [x] Every EmbedEZ/RedditEZ failure falls back to vxreddit when vxreddit is valid.
- [x] EmbedEZ/RedditEZ 720p never displaces healthy vxreddit.
- [x] No new variable is required before the quality update is effective.
- [x] The default mode is confirmed as `balanced` for the intended seamless rollout.
- [x] All video failure conditions are tested.
- [x] Full compile, smoke, and signal tests pass.
- [x] The full diff has been reviewed.
- [x] Image, GIF, photo, gallery, cache/state, webhook, secret, scheduling, and proxy behavior are unchanged.
- [x] Production upload remains a separate process from this development repository.

## 10. Evidence boundary

Repository tests can demonstrate resolver decisions, fallback behavior, bounds, and unchanged local code paths. They cannot guarantee future uptime of Reddit, EmbedEZ/RedditEZ, vxreddit, Discord, or any external CDN.

The reliability requirement is therefore implemented as a fail-safe policy:

```text
Use EmbedEZ/RedditEZ when it is valid and improves video quality;
otherwise use vxreddit without making the post fail.
```

## 11. Audio-evidence note (why "where detectable" appears)

The audio rule is a **relative tripwire**, not a statement that vxreddit or
EmbedEZ lack audio:

- It fires only when a candidate's probed MP4 evidence shows **no audio
  track while the held base has one** — i.e. exactly the mux/response failure
  shape that once produced a silent card (round 50, incident `1wv12qb`).
- If the held base is silent (Embeddit's DASH fallback stream is, per the
  round-49 field table and the round-53/54 rewrite notes) and the candidate
  carries audio, the candidate is **accepted** — the rule can never keep a
  silent result in front of an audio-bearing one.
- Detection is best-effort (the 64 KiB prefix, when a leading `moov` is
  present) and never gates a card URL on its own; it only decides which of
  two validated candidates is shown.
- Embeddit's own audio support (`?audio=1`, and the rewrite's PR #2 to-do)
  is upstream work; this policy does not depend on it, and nothing here
  needs to change when Embeddit's video gains audio — the tie-break order
  stays and an audio-bearing Embeddit result would simply compare like any
  other.
