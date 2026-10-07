# 🔴 Reddit video media test report — evidence base for round 67

> **Status:** evidence report from manual Discord/Discohook tests, production
> observations, source inspection and local automated tests (2026-10-07).
> It records what was measured on real posts. The implementation it
> recommended now ships as round 67 — see
> [`REDDIT_VIDEO_QUALITY.md`](REDDIT_VIDEO_QUALITY.md) for the
> shipped policy and [`history/ROUND_67.md`](history/ROUND_67.md) for
> the decision record.

## Executive result

Repeated live tests on Reddit videos showed a consistent quality difference
between the available media paths:

```text
EmbedEZ 1080p  -> playable with audio and visibly higher quality
EmbedEZ 720p   -> playable with audio and visibly lower quality
vxreddit       -> playable with audio, but visibly lower quality even when
                  supplied with a CMAF 1080 input in the tested cases
Signed native  -> highest/original quality when currently valid, but expires
```

The quality result was reproduced across multiple posts:

- Genshin Impact video: `1wzkhnu`.
- Genshin Impact video: `1wzkk1o`.
- Honkai: Star Rail video: `1ww0mmv`.
- Wuthering Waves portrait video: `1wzlx8d`.

The post identifiers above are test evidence only. They are **not**
hard-coded into the monitor.

## Manual live evidence

### Native Reddit packaged-media URL

The manually tested signed Reddit URL:

```text
packaged-media.redd.it/.../m2-res_1080p.mp4?...signed parameters...
```

played successfully in Discord with audio and showed the highest-quality
rendition for the tested Genshin video.

This is **not** a durable production candidate because the URL includes
signed, expiring parameters. It must not be persisted in cache/state or
relied on for future playback after expiry. Round 67 enforces exactly that:
`media_url_is_durable()` refuses it as a card candidate.

### vxreddit

The tested muxing URL used separate Reddit CMAF tracks:

```text
CMAF_720.m3u8
CMAF_AUDIO_128.m3u8
```

It played successfully in Discord with audio.

Changing the video input to:

```text
CMAF_1080.m3u8
```

also produced a playable result, but the tested output remained visibly
similar to the lower-quality rendition. This indicates that the vxreddit
service may select, cache, transcode or cap its own output quality. **A URL
containing `1080` is not proof that the returned file is 1080p.** Round 67's
resolver therefore decides on validated response facts (and, where the byte
prefix allows it, real MP4 dimensions), never on the URL text.

### EmbedEZ / redditez

The tested EmbedEZ render URLs were:

```text
https://proxy.embedez.com/render/video.mp4?videoUrl=...CMAF_720.mp4&audioUrl=...CMAF_AUDIO_128.mp4&headers=%7B%7D
```

and:

```text
https://proxy.embedez.com/render/video.mp4?videoUrl=...CMAF_1080.mp4&audioUrl=...CMAF_AUDIO_128.mp4&headers=%7B%7D
```

Both played successfully with audio. The 1080p output was visibly sharper on
the tested landscape and portrait videos.

The `redditez.com` post page also rendered successfully for the tested posts
and exposed the EmbedEZ media path.

## Portrait-video result

The Wuthering Waves portrait video confirmed that quality selection must
preserve the source aspect ratio.

Observed behavior:

- 720p EmbedEZ: playable portrait video with lower detail.
- 1080p EmbedEZ: playable portrait video with higher detail.
- No observed stretching or incorrect landscape conversion.
- No observed crop that removed the primary subject.

Any resolver must validate both quality and aspect ratio. It must not compare
landscape assumptions against portrait media. Round 67 implements this as
`prefer_quality_candidate()`: a candidate whose measured dimensions flip the
orientation of the base result never replaces it.

## Source behavior at the time of the tests

The then-current implementation included:

- Native Reddit video discovery.
- Native DASH candidate checks.
- EmbedEZ muxing URLs.
- vxreddit muxing URLs.
- Audio/video fallback behavior.
- Media response validation.
- A maximum media-size guard.
- Thumbnail-plus-Reddit-button fallback.
- Proxy warm-up and per-run proxy health handling.

Video selection was not quality-first: it could accept a valid lower-quality
candidate before testing a higher-quality EmbedEZ candidate, and it used 720p
as its initial CMAF quality.

## Proven compatibility matrix

| Media path | Tested playback | Tested audio | Tested quality result |
|---|---:|---:|---|
| Reddit signed packaged MP4 | Yes | Yes | Highest/original for the tested post; expires |
| vxreddit 720 input | Yes | Yes | Lower-quality output |
| vxreddit 1080 input | Yes | Yes | Playable, but no visible quality improvement in tested cases |
| EmbedEZ 720 input | Yes | Yes | Lower-quality output |
| EmbedEZ 1080 input | Yes | Yes | Higher-quality output |
| Portrait EmbedEZ 720 | Yes | Yes | Correct portrait playback |
| Portrait EmbedEZ 1080 | Yes | Yes | Correct portrait playback with higher detail |

## Local automated validation

The repository suites were executed successfully:

```text
python -m compileall -q "testing area" tests
python tests/test_smoke.py
python tests/test_reddit_signals.py
```

Results:

```text
SMOKE TEST: ALL PASS
REDDIT SIGNAL TEST: ALL PASS
```

Counts differ between checkouts (path-dependent checks) — `ALL PASS` is the
contract, not the number. The local tests cover media extraction and decision
behavior including:

- Native Reddit image and video signals.
- GIF detection.
- Gallery extraction and ordering.
- Full-resolution image normalization.
- Duplicate-media handling.
- Proxy parsing.
- Proxy fallback selection.
- Text-only proxy responses.
- Dead-proxy handling.
- All-proxy retry behavior.
- Native video fallback.
- Video-first card behavior.
- Poster-image de-duplication.
- Cache and monitor workflow behavior.

Round 67 added deterministic video-resolution guards on top of the above
(candidate validation, error bodies, size limits, audio evidence, portrait /
landscape, the signed-URL refusal, the compatibility rollback and the
bounded budgets) — see `tests/test_smoke.py`, section `ROUND 67`.

## Production runner evidence

The supplied GitHub Actions logs showed:

- CPython `3.14.8` installed successfully.
- Dependencies installed from compatible wheels.
- Proxy warm-up succeeded for `redditez`, `vxreddit` and `embeddit`.
- Combined Reddit feed retrieval succeeded.
- The Reddit monitor completed and persisted cache state successfully.
- The relevant Wuthering Waves post was manually tested separately for media
  quality and was not evidence of an automated Discord post.

## Reliability and performance boundary

The tests prove compatibility for the tested URLs and the implemented local
decision paths. They do **not** prove permanent uptime or universal
compatibility, because final behavior depends on:

- Reddit CDN availability.
- Signed URL expiry.
- EmbedEZ service availability and transcoding.
- vxreddit service behavior and cache/transcoding policy.
- Discord media fetching and limits.
- GitHub Actions runner/network availability.
- Future source-format or domain changes.

No claim of 100% uptime, zero bugs or guaranteed future playback is made.

## Verified implementation direction (now shipped in round 67)

The tested evidence supported a video-only quality-aware resolver using
durable proxy outputs while preserving the historical reliability order:

```text
1. vxreddit remains the first/winner path and the reliable immediate fallback.
2. A validated EmbedEZ 1080p result may replace vxreddit when it is healthy,
   within the time budget, and demonstrably usable.
3. If EmbedEZ 1080p fails, times out, is unavailable, returns an error, or
   produces an unusable result, use vxreddit without delaying the post.
4. EmbedEZ 720p is optional and must not displace a healthy vxreddit result
   unless a separately approved policy explicitly chooses it.
5. Thumbnail plus the Reddit button is the final fallback when no playable
   output survives validation.
```

EmbedEZ 1080p is a quality enhancement, not a replacement for the
vxreddit-first reliability behavior. The past production evidence that
vxreddit was more consistent for video remains part of the design basis.
Embeddit remains a later fallback mainly for photos, multi-photo galleries
and other media shapes; its tested video path has not been treated as the
primary audio-capable video route.

Signed native Reddit packaged-media URLs must not be stored or treated as
durable output URLs.

Image, photo, GIF, gallery, cache, webhook and monitor scheduling behavior
remain outside the scope of the video-quality change.

## Final evidence verdict

The manual tests establish a repeatable quality advantage for EmbedEZ 1080p
over EmbedEZ 720p and the tested vxreddit outputs, while preserving
successful audio playback and portrait-video compatibility.

The result is strong evidence for a quality-aware video-selection update, but
it remains an external-service compatibility result rather than a guarantee
against future upstream failures.
