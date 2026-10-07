# Reddit video quality selection (round 67)

Video-only policy. Images, GIFs, photos, galleries, cache/state files,
webhooks, secrets and monitor scheduling are untouched by it.

The variable is optional and empty-string-safe:

| Variable | Values | Default |
| --- | --- | --- |
| `REDDIT_VIDEO_QUALITY` | `balanced` · `compatibility` · `highest` | `balanced` |

It is wired into `.github/workflows/reddit_monitor.yml` as
`REDDIT_VIDEO_QUALITY: ${{ vars.REDDIT_VIDEO_QUALITY }}`. An unset or empty
repository Variable resolves to `balanced` without a warning; any
unrecognized value logs one warning and also resolves to `balanced`.

## Mode behavior

### `balanced` (default)

```text
1. vxreddit (CMAF_1080 m3u8 input — the tested service output did not
   visibly improve with a 1080 input, but the best available source is
   offered) — the reliable winner path and immediate fallback, never
   starved while EmbedEZ is pending.
2. EmbedEZ 1080p, attempted in the same bounded window — may REPLACE the
   validated vxreddit result only when the probe evidence supports it.
3. EmbedEZ 720p — only when vxreddit itself is unusable.
4. Durable v.redd.it DASH ladder (720 → 1080 → 480 → 360) — the reliability
   floor, straight from Reddit, muxed with audio.
5. Nothing playable survives validation → first-frame thumbnail + Read Post.
```

### `compatibility`

The pre-round-67 ladder, unchanged in order: durable native `v.redd.it`
first, then EmbedEZ 720p, then vxreddit, then EmbedEZ 1080p. This is the
zero-code rollback: switch the Variable, no deploy needed.

### `highest`

`balanced` with a wider quality window (15 s instead of 8 s). This mode is
intended only for a deliberate canary: it is still bounded by the same size
and per-run limits.

## Why the order is vxreddit-tolerant

- vxreddit is attempted first and its result is held: an EmbedEZ timeout,
  HTTP error, HTML error page, oversized file or failed mux simply keeps it.
- The EmbedEZ 1080p attempt is bounded by `VIDEO_QUALITY_WINDOW_SECONDS`
  (8 s; 15 s in `highest`), so it can never hold the post indefinitely.
- A failed 1080p attempt never costs the 720p rung its chance: in
  `balanced` the EmbedEZ 720p rung is reached when the vxreddit base itself
  failed to validate (a validated vxreddit result is never displaced by it),
  and in `compatibility` the 720p rung is tried before the 1080p attempt.
  The candidates are independent probes, so one failure never suppresses
  the others.
- A failed proxy never prevents the durable native ladder or, ultimately,
  the thumbnail + Read Post fallback.

## Candidate validation

A candidate is usable only when all of the following hold:

- HTTP success (200/206) within its candidate timeout.
- The content type is a compatible video type (a missing content type is
  accepted only when the byte prefix looks like an MP4).
- The response is not an HTML or JSON error body, even on a 200 transport.
- The range/bounded-body probe succeeds.
- The reported size is below the configured Discord safety limit
  (`MAX_MEDIA_BYTES`, 256 MiB).
- Where the byte prefix contains a `moov` box, the parsed MP4 facts
  (real width/height and audio-track evidence) support the quality claim.

**A URL containing `1080` is never proof of 1080p.** URL quality hints are
used for ordering only.

### Signed / expiring native URLs

Signed and expiring `packaged-media.redd.it` URLs (any URL carrying
signature or expiry parameters) are never card URLs and are never persisted
in cache or state. They are refused outright by `media_url_is_durable()`.
Durable unsigned media (for example `v.redd.it/<id>/DASH_720.mp4`) is the
only native family that can be a card URL, and only as the last playable
resort before the thumbnail fallback.

## Budgets (constants, not Variables)

| Budget | Value |
| --- | --- |
| One post, wall clock | 40 s |
| One proxy candidate | 20 s |
| One native candidate | 10 s |
| Quality window (`balanced` / `highest`) | 8 s / 15 s |
| One run, total quality attempts | 180 s |

After the per-run budget is spent, the resolver goes straight to the durable
native ladder. Concurrency is bounded: at most two candidate probes are in
flight per post (vxreddit and EmbedEZ 1080p), and posts are processed
sequentially.

Nothing in this subsystem writes candidate URLs, proxy state or temporary
media into production cache/state JSON.

## Live canary checklist

Before widening `highest`, and to validate `balanced` in production, run a
representative corpus and record:

- [ ] EmbedEZ 1080p success rate and median added latency.
- [ ] vxreddit unusable rate (how often the 720p rung is reached).
- [ ] Native-ladder fallback rate and untouched thumbnail+button rate.
- [ ] Resulting file sizes versus the 256 MiB limit.
- [ ] Portrait videos (`1wzkhnu`, `1wzkk1o`, `1ww0mmv`, `1wzlx8d` — evidence
      IDs from the round's manual tests, never hard-coded in code).
- [ ] Log lines for budget exhaustion and rejected candidates.

Evidence base: [`REDDIT_VIDEO_MEDIA_REPORT.md`](REDDIT_VIDEO_MEDIA_REPORT.md).
Decision record: [`history/ROUND_67.md`](history/ROUND_67.md).
