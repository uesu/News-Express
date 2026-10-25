# Round 88 (2026-10-25) — Full Reddit text and Twitter recovery revalidation

## Scope and original contract

The maintainer requested complete long Reddit bodies and safer recovery of cold Twitter videos.
Round 66 limited source text to 16,000 characters and output to three continuation messages.
This enhancement intentionally replaces those caps with content-driven pagination. Earlier
round records remain historical; their caps are superseded, not erased.

Reddit media providers, video quality/audio checks, gallery order, main-card stats/buttons,
fresh-age hold, operational gates and existing Reddit media-heal behavior are preserved.
Normal short posts retain their payload and ordinary send path. There is no fleet promotion,
content classification, new Variable/Secret, scheduler change or historical-post replay.

## Implementation and recovery

- Keep all retrieved source text; split the remainder into text-only Components V2 messages.
- Persist main/page IDs, continuation payloads and next index independently of retraction.
- Save an ambiguity hold before the multipart main card and each continuation send. Confirmed 200 responses with IDs advance;
  explicit 429 rejections defer until Retry-After; timeout/5xx/missing IDs hold for reconciliation.
  Stop at the first failure. Resume confirmed-unsent pages without repeating accepted pages.
  Proven pre-send connector failures can retry: defer a continuation for 60 seconds or
  release the unsent main-card hold for the next feed attempt. Timeouts remain uncertain.
- Every continuation 429 defers to a later run, including short Retry-After values.
  This is the accepted stop-on-first-rejection policy; other posts can appear between
  deferred parts. In-run POST retry is a separate policy change.
- Save atomically and reject corrupt delivery state. Completed continuation markers restore
  ordinary dedup if the process stopped after the last page save but before the dedup save.
  Retain completed page evidence for the retention window after the final page, even when
  delivery resumed long after the main card. Retraction still uses the original delivery time.
- Reject malformed nested progress before resuming; main-card timeouts/server errors retain
  a reconciliation hold. Explicit main-card 4xx rejections remain eligible for later delivery.
  Cache-load failures produce a fresh incomplete run record; resumed page changes count as
  saved local state even if ordinary post dedup did not change.
- Cache records contain public rendered content and IDs, not webhook URLs. Preserve each live
  target’s cache. Existing workflow force-add/sync protection already covers posted_messages.json.
- The existing run-end Git commit/push still bounds runner-loss recovery. A local save is not
  proof of repository persistence. Operator reconciliation remains necessary for ambiguous sends.

## Twitter enhancement

Only heal_unresolved_media changes: after the existing 45-second wait, GET the existing webhook
message before its same-payload PATCH. Resolved media skips editing; 401/403/404 stops;
transient GET failure preserves the existing bounded edit. The default video-only scope,
four-attempt ceiling, provider selection, GIF conversion and post-loop concurrency remain.
A healthy post adds no request; queued attempts add at most four GETs total. The queue is not
persistent. Playback is not guaranteed after exhausted attempts, and existing messages are not
backfilled. Manual Discohook success is operator evidence, not an automated end-to-end test.

## Verification and measured costs

All three repository offline suites pass on the enhancement implementation. Restart, explicit
rate-limit retry, ambiguous-outcome hold, atomic-save failure and corrupt-cache cases are covered.
A differential check against development main 04de03d verifies 12 text/image/video/table/link/
spoiler fixtures produce identical main-plus-continuation payloads within the old limits.
The 45k fixture preserves the same main card and all readable text, growing from 4 to 15 messages.
This adds 11 webhook requests for that fixture; one-second continuation pacing remains, and
atomic progress saves add filesystem work. Complete content necessarily costs more than truncation.

The earlier sibling handoff’s local CPU benchmark (Python 3.14.4; 200 repetitions after 10 warmups, no network/cache
writes) measured main/candidate median microseconds: short 9.73/9.73; within-old-limit 357.49/
356.11; 45k 2240.78/4298.07. These are single-machine samples, not a speed improvement or live
latency claim. The 45k baseline only renders its truncated four-message result. Differential
benchmarks do not measure webhook latency, sleep, filesystem durability or provider fetches.

## Handoff and documentation

Development main remains the source of code updates; both production repositories intentionally
contain both engines. Sync atomically copies engines/tests/helpers/selected workflows while
preserving live caches; it excludes development documentation. No deployment or feature switch
is implied by this record. The patch must land in development and pass its normal CI before sync.
This task integrates the latest complete sibling handoff against development main `04de03d`,
then adds the interruption/retention/validation corrections above. The earlier sibling task’s
publication-scope blocker is historical; this News task delivers the changes through its own PR.
Fresh verification and current benchmark samples are recorded in that PR.
