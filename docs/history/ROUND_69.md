# Round 69: Reddit provider-order docs and Arctic outage reasons

**Date:** 2026-10-08  
**Scope:** Documentation/comment accuracy and one diagnostic log line; no provider, request, or delivery behavior changes.

## Why

Two things had drifted from the live code:

1. The README and several V3 module comments still described an older proxy
   order (`redditez → vxreddit → embeddit`), an architecture that no longer
   matched the code, and a V3 header that said EmbedEZ was absent from the
   quality path. Round 49 replaced the serial proxy chain with bounded
   concurrent waves, and round 67 added EmbedEZ as an optional, validated 1080p
   video-quality candidate.
2. When the Arctic Shift search failed with an exception that has no message
   (for example a bare `TimeoutError`), the log line ended in an empty reason:

   ```text
   Arctic Shift search unavailable:
   ```

## Provider order (documentation only)

`reddit_proxy.PROXY_SERVICES` is `("vxreddit", "redditez", "embeddit")`. That
tuple is the **priority / tie-break order**, not the request order. The
resolver dispatches the first two eligible services together (wave 1), holds
Embeddit back by `PROXY_WAVE_DELAY`, and cancels held-back work when a decisive
answer already exists. The README and the V3 comments now state this order and
point to the round-49 wave description. The historical round-13 notes are kept,
marked as superseded.

Behavior is unchanged: vxreddit remains the reliability-first base, EmbedEZ
remains an optional validated quality candidate, and Embeddit remains the
rewrite and last-resort provider.

## Arctic Shift search diagnostics

`fetch_arctic_subreddit_posts()` now computes the logged reason as:

```python
reason = str(exc).strip() or type(exc).__name__
```

Resulting log lines:

```text
Arctic Shift search unavailable: TimeoutError
Arctic Shift search unavailable: HTTP 422
Arctic Shift search unavailable: peer reset
```

HTTP status messages and descriptive exception text are kept as before. Only a
blank string representation now falls back to the exception class name. The
reason is not truncated or enriched with URLs, parameters, or response bodies.

## Explicitly unchanged

No provider order or dispatch behavior changed. No request, retry, timeout,
probe, cache, posting, scheduling, workflow-summary, quality-selection,
`candidate=embedez`, or retained-provider fallback behavior changed. The
`_arctic_fail_count` circuit breaker still counts every failure and still
returns `[]`. Content classification and the content-advisory gate were not
reintroduced. Image, GIF, photo, gallery, and non-video paths are untouched.

## Regression coverage

The offline smoke suite (`tests/test_smoke.py`, round 69 block) verifies:

- a blank-message `TimeoutError` returns `[]` and logs
  `Arctic Shift search unavailable: TimeoutError`;
- `HTTP 422` is still logged as `Arctic Shift search unavailable: HTTP 422`;
- descriptive exception text is still logged verbatim.

No network access is used.
