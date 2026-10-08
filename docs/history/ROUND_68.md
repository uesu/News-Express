# Round 68: Reddit video-quality fallback diagnostics

**Date:** 2026-10-08  
**Scope:** Observability only; no provider, media-selection, request, or delivery behavior changes.

## Why

The proxy video-quality path already retained the validated base when its
optional EmbedEZ 1080p candidate failed. Its unavailable message did not give
a normalized reason, and a candidate that failed the existing superiority
comparison returned the base without an explicit fallback notice. This made
it harder to distinguish an unavailable candidate from one that simply did
not win.

## Change

`proxy_video_quality_upgrade()` now emits one explicit fallback notice on
each existing post-attempt fallback path:

```text
quality fallback: candidate=embedez; retaining validated base provider=vxreddit; reason=quality_candidate_unavailable
quality fallback: candidate=embedez; retaining validated base provider=vxreddit; reason=quality_candidate_not_superior_or_unvalidated
```

Each notice identifies the optional quality provider being evaluated as
`candidate=embedez`; the retained base provider is computed from the retained
URL through `_provider_for_url()`:

- `vxreddit` → `vxreddit`
- EmbedEZ / RedditEZ → `embedez`
- Embeddit → `embeddit`
- native `v.redd.it` → `native-dash`
- unrecognized host → `unknown`

The default label was changed from `thumbnail` to `unknown` so future video
hosts are not incorrectly described as thumbnails. Add future host mappings
to `_provider_for_url()`; the fallback log template stays generic.

The accepted-upgrade branch and `prefer_quality_candidate()` selection logic
are unchanged. The new notices do not report a source maximum, infer quality
from a URL, or claim dimensions/audio without probe evidence. Existing
`_video_evidence()` output continues to distinguish verified dimensions,
unknown dimensions, confirmed audio, absent audio, and unknown audio.

## Explicitly unchanged

No provider order or reliability-first fallback behavior changed. No
EmbedEZ/Embeddit request policy, probe, media request, retry, delay, request
budget, timeout, cache operation, deduplication, posting behavior, Discord
payload, scheduling, image, GIF, gallery, or non-video path changed. The only
runtime addition is the local fallback log call after a valid candidate is
not selected; the existing unavailable log is replaced with its explicit
reason. No new network request is introduced.

The workflow summary already uses `count_matches 'retaining validated
base'`, so both formats remain countable. Its `quality fallback notices`
value is the number of matching log notices, not a complete count of all
quality decisions. The summary still reads only the local `monitor.log`.

## Regression coverage

Offline smoke guards verify:

- superior validated candidate acceptance keeps the existing success message;
- HTTP 400, network failure, and invalid HTML response log the unavailable
  reason and retain the already-validated vxreddit URL;
- a validated but non-superior candidate retains the base with the
  not-superior/unvalidated reason;
- fallback provider labels cover vxreddit, EmbedEZ/RedditEZ, Embeddit, native
  Reddit media, and an unknown future host;
- URL text containing `1080` is not reported as verified dimensions, and
  missing/absent audio is not reported as present;
- failed quality requests do not trigger the comparison probe, while the
  established two-request valid-candidate path remains unchanged;
- the proxy media path still keeps the validated vxreddit video when the
  quality opportunity fails, and workflow-summary wording remains compatible.

The existing smoke suite also continues to guard the quality budgets,
compatibility mode, video-only quality opportunity, and unchanged
image/GIF/gallery handling.
