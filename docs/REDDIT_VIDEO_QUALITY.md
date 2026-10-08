# Reddit video quality selection (round 67)

Video-only policy. Images, GIFs, photos, galleries, cache/state files,
webhooks, secrets and monitor scheduling are untouched by it.

## Which paths are covered

Every Reddit-hosted video a card can end up showing goes through the same
bounded quality opportunity:

| Path | Behavior |
| --- | --- |
| Native / FULL MODE (`resolve_video_url`) | vxreddit base + EmbedEZ 1080p raced inside the quality window, then 720p, then the durable native DASH ladder. |
| Proxy-delivered video (`PROXY_MEDIA=1`, the default: the round-49 wave muxed a video) | The validated proxy mux is the **held base**; one bounded EmbedEZ 1080p candidate may replace it, and only when the base's own probe facts allow it. Any failure keeps the proxy video verbatim. |
| Redlib gallery video | Same resolver as the native path. |
| Images, GIFs, photos, ordinary galleries | **Never** touch this subsystem: no quality request is made. |

Request accounting for the proxy path: exactly one extra request (the
EmbedEZ 1080p probe) when it fails; one more short 64 KiB probe of the
already-validated proxy video only when the EmbedEZ candidate validated and
the comparison needs the base's dimensions/audio evidence. `compatibility`
mode makes **zero** extra requests, so it is byte-for-byte the pre-round-67
proxy path.

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
first, then EmbedEZ 720p, then vxreddit, then EmbedEZ 1080p — and on the
proxy path the round-49 proxy video is used verbatim with no extra request.
This is the zero-code rollback: switch the Variable, no deploy needed.

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

### Quality fallback logging (round 68)

The proxy-path quality opportunity now states why an already validated base
video was retained. This is a logging-only change: it does not alter provider
selection, validation, request counts, timeouts, budgets, or the returned
media URL.

When the optional quality candidate is unavailable (for example, a failed
HTTP response, invalid body, or timeout), the log says:

```text
quality fallback: retaining validated base provider=vxreddit; reason=quality_candidate_unavailable
```

When a candidate was returned but the existing selector did not accept it as
a superior validated result, the log says:

```text
quality fallback: retaining validated base provider=vxreddit; reason=quality_candidate_not_superior_or_unvalidated
```

The provider label is computed from the retained URL, not hard-coded:

| URL family | Fallback provider label |
| --- | --- |
| vxreddit | `vxreddit` |
| EmbedEZ / RedditEZ | `embedez` |
| Embeddit | `embeddit` |
| native `v.redd.it` DASH | `native-dash` |
| unrecognized video host | `unknown` |

Add future host mappings to `_provider_for_url()`; an unrecognized host is
never mislabeled as a thumbnail. The explicit accepted-upgrade message is
unchanged. Dimensions and audio are reported only from probe facts; absent
evidence remains `unverified` / `unknown`, and a URL quality hint is marked
as non-evidence. These messages do not claim that the Reddit source is capped
at 720p or establish the source's maximum quality.

The workflow summary continues to count the stable `retaining validated
base` phrase from its local `monitor.log`. That total is a count of fallback
notices, not a complete count of all quality decisions; bypasses such as
compatibility mode or a spent quality budget need not create a fallback
notice. The summary adds no network or cache operation.

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
native ladder (on the proxy path it keeps the validated proxy video
untouched). Concurrency is bounded: at most two candidate probes are in
flight per post (vxreddit and EmbedEZ 1080p), the proxy-path opportunity is
one awaited probe plus at most one comparison probe, and posts are processed
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
Confirmed acceptance policy: [`VIDEO_ONLY_QUALITY_POLICY_CONFIRMATION.md`](VIDEO_ONLY_QUALITY_POLICY_CONFIRMATION.md).
