# Round 119 — Twitter media headroom and age-independent feed eligibility

## Changes

### Fixed 400 MiB gallery-video cap

The active V3 monitor and the optional V2 engine now use a fixed **400 MiB**
external-video gallery cap. The old `TWITTER_HIGH_VIDEO_LIMIT` opt-in was removed
from the engines and workflow, so there is no repository Variable to enable or
maintain.

The operator supplied a live Discord example where an approximately 395 MB
1920x1080 X video was manually switched from 1280x720 and embedded/played on its
first try. The new cap admits that rendition. It does not claim that all 4K
renditions or every file near 400 MiB will work through every Discord proxy.

When the chosen source file exceeds the cap, the monitor probes all known MP4
variants in descending bitrate and selects the best fitting rendition. That
allows a source to fall from 4K to 1080p or 720p as needed instead of stopping
after only a few variant probes. If none fits (or a size cannot be determined),
the existing conservative fallback behavior remains in place. The existing
cold-media repair still revalidates/re-edits the selected URL; this change does
not change video quality just because a proxy is temporarily cold.

### Faster cold-media revalidation

`MEDIA_HEAL_DELAY_SECONDS` now defaults to **15 seconds** (was 45). A queued
repair waits, revalidates the Discord message, and only edits if eligible media
is still unresolved. The bounded attempt count, identical-payload edits,
video-only default scope, and later-run carry behavior are unchanged. Healthy
media still avoids the repair queue and adds no wait to delivery.

### Remove the Twitter age cutoff

The engine no longer reads `TWITTER_MAX_AGE_HOURS`, calculates age from feed
dates or tweet snowflakes, or emits `STALE-SKIP`. Uncached feed entries remain
eligible regardless of age. This prevents a fixed 24-hour window from silently
excluding a legitimate post such as `TYPEII_EN/2119676737907007696`, which had
remained in old feed logs but was skipped after crossing the threshold.

The normal `posted_tweets.json` key check still runs before tweet-data fetching,
and keys already present are skipped. The cache is bounded by its existing
per-account and global retention settings: a key evicted from the cache, or
missing after a reset/deployment issue, cannot be guaranteed to deduplicate.
Removing the time floor intentionally trades protection against old uncached
backlog items for not losing legitimate old posts. The manual `TEST_TWEET_ID`
path and scheduled-run behavior otherwise remain unchanged; force repost remains
available only through its existing explicit manual opt-in.

## Workflow summary and docs

- Replace stale-backlog counts/key lists with an age-neutral **Deduplication
  state** section. It reports the engine's cache/post counters and explains the
  cache-retention boundary without implying old entries are refused.
- Remove the retired age setting and high-video opt-in from current docs and
  workflow environment wiring. Historical Round 94/95c records remain as a
  record of the earlier decisions and are marked as superseded in the changelog.
- Update the active video/heal guidance and this record.

## Reference and verification plan

The user also supplied Game-Express run evidence showing its media-heal path can
observe a cold tile load by itself without editing. The News-Express implementation
already revalidates before PATCH; this round only shortens its configured wait.
Game-Express is a separate repository and is not changed by this PR.

Offline regression coverage should prove:

- exactly 400 MiB is accepted and the next byte over triggers variant selection;
- ~395 MB 1080p media stays on its original URL;
- over-limit 4K media falls through 1080p to 720p when necessary;
- every known MP4 variant is eligible for probing;
- both engines use the fixed cap and no longer read the deleted opt-in;
- the 15-second default is applied while repair remains bounded and skips media
  that resolves on its own;
- an old uncached tweet is no longer age-rejected, while an already cached key
  is still skipped; and no age-floor variable or `STALE-SKIP` path remains in the
  active engine/workflow/README.

No live Discord repost or external service mutation is performed by these tests.
