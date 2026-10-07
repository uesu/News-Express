# Round 67 (2026-10-07) — content-advisory gate removed; quality-aware video resolver

Decision record. It is the complete, future-proof record of everything round
67 removed and everything it added. Historical documents in `docs/history/`
may still describe the former gate truthfully; this file is the index of what
changed and why.

## Part 1 — the content-advisory gate is gone

The maintainer's final policy: the Reddit monitor makes **no content-based
posting decision**. There is no gate, no hold, no allowlist, no fallback
metadata classification, no "unknown metadata" state, and no repository
Variable for any of it. A post that the feed and the other safeguards accept
is posted.

The removal was executed at every level — engine, pure decision module,
workflow, configuration, tests and current documentation — and is enforced by
tests that search the active files for the removed names.

### Complete removed-name record

Removed **engine symbols** (`testing area/reddit_main_v3.py`):

- `NSFW_ALLOWLIST`, `NSFW_FAIL_OPEN`, `NSFW_REQUIRE_SUBREDDIT`,
  `NSFW_PAGE_FALLBACK` (module constants and their reads).
- `NSFW_BADGE_*`/badge parsing helpers call path: the live-page badge reader
  wired through `fetch_first_redlib_post_page` → `nsfw_from_post_page`.
- `fetch_arctic_nsfw_flags()` — the batched Arctic Shift marker lookup
  (`_arctic_nsfw_markers()`, `_arctic_bool()`).
- `nsfw_from_post_page()` and the `_nsfw_allowlist_forms()` wrapper.
- `nsfw_gate_reason()` — the gate decision call.
- The whole main-loop gate block: the per-post marker lookup
  (`nsfw_flags.get(...)`), the `TEST_POST_ID` bypass, the
  `over_18`/`thumbnail`/subreddit-source decisions, the `nsfw_unknown`
  hold (`mark_pending(..., "nsfw_unknown", ...)`), the allowlist info log,
  the pending-status `nsfw*` skip recheck path, and the round-42/45
  fail-closed comments.
- The NSFW entries in `_NO_RECHECK_REASONS`.

Removed **pure-module symbols** (`testing area/reddit_signals.py`):

- `_NSFw_BADGE_RE`, `_POST_PAGE_HINT_RE`, `_UNREADABLE_PAGE_RE` (page
  parsing regexes).
- `nsfw_from_post_page()`, `nsfw_allowlist_forms()`, `_allowlisted()`,
  `_bool_or_unknown()`, `nsfw_gate_reason()`.

Removed **workflow mappings** (`.github/workflows/reddit_monitor.yml`):
the `env:` entries for `NSFW_ALLOWLIST`, `NSFW_FAIL_OPEN`,
`NSFW_REQUIRE_SUBREDDIT`, `NSFW_PAGE_FALLBACK`.

Removed **configuration** (`.env.example`): the round-35 gate block
(including the `nsfw` thumbnail sentinel description), the round-42
fail-closed block, and the round-45 live-page fallback block.

Removed **tests**:
- `tests/test_reddit_signals.py`: the badge cases, the gate decision
  matrix, the allowlist cases, the crosspost-source cases, the
  unknown-hold cases, the arctic marker fetch cases, the fail-open /
  require-subreddit cases, and the main-loop gate scenarios.
- `tests/test_smoke.py`: the round-42/45 gate guards, the fail-open /
  page-fallback WiringGuard rows, the NSFW rows of the "true by default"
  flag list, and every remaining gate assertion.

Removed **documentation**: the README gate rows/sections and Variables, the
`AGENTS.md` invariant "The NSFW gate is never removed or weakened", the
`docs/CI_SMOKE.md` gate description, the NSFW lines of the current
`docs/CHANGELOG.md`, and the terms clause that named the removed gate
(rewritten to "age-restricted-into-general-channel" so the prohibition on
reposting restricted content survives without the removed name).

### What deliberately stayed

Dedup cache and semantic cache recovery, `FRESH_HOLD_SECONDS`, the
`LISTING_CONFIRM` pristine `/new` listing confirmation, the pending
recheck throttle, archive liveness, stale-dispatch sync, cache-commit
recovery, media resolution and validation, proxy health and warm-up,
Discord webhook delivery, Actions permissions/timeouts/SHA pinning, the
opt-in retraction seatbelt, and the whole image/GIF/photo/gallery pipeline
(rounds 12, 38, 44, 47, 57, 61, 64, 66 behavior). No cache/state JSON,
webhook, secret or proxy-order changed.

## Part 2 — quality-aware video resolver

Change surface: `resolve_video_url()` and its new helpers only. Images,
GIFs, photos and galleries were not touched (their tests still pass
unchanged).

- **Modes** (`REDDIT_VIDEO_QUALITY`, empty-safe, default `balanced`):
  `balanced`, `compatibility` (pre-round-67 ladder, byte-order identical —
  the zero-code rollback), `highest` (wider quality window; canary-only).
- **Reliability order**: vxreddit is attempted first and its result is
  held; a validated EmbedEZ 1080p may replace it only when the probe
  evidence supports it; EmbedEZ 720p is reached only when vxreddit itself
  is unusable; the durable `v.redd.it` DASH ladder (720 → 1080 → 480 → 360)
  is the reliability floor; thumbnail + Read Post is the last resort.
- **Validation**: HTTP 200/206, compatible content type, HTML/JSON error
  body rejection even on a 200 transport, range/bounded-body probe,
  `MAX_MEDIA_BYTES` (256 MiB) limit, candidate timeouts, and best-effort
  MP4 facts (real dimensions + audio-track evidence parsed from the 64 KiB
  body prefix). A URL containing `1080` is never treated as proof of
  1080p; URL hints are ordering-only.
- **Durability**: signed/expiring `packaged-media.redd.it` URLs are
  refused outright as card URLs and are never persisted. No candidate URL,
  proxy state or temporary media is written into cache/state JSON.
- **Budgets**: 40 s per post, 20 s per proxy candidate, 10 s per native
  candidate, 8 s quality window (15 s in `highest`), 180 s of quality
  attempts per run; then the native ladder directly. At most two probes in
  flight per post.
- **Covered paths**: the quality opportunity runs on every path that can put
  a Reddit video in a card — the native / FULL MODE resolver, the redlib
  gallery video, and (follow-up, same round) the PROXY-delivered video path.
  On the proxy path the round-49 wave's validated mux is the held base and
  one bounded EmbedEZ 1080p candidate may replace it against the base's own
  probe facts; `compatibility` makes no extra request there at all. Image,
  GIF, photo and ordinary gallery paths still make zero quality requests.
- **Evidence**: [`docs/REDDIT_VIDEO_MEDIA_REPORT.md`](../REDDIT_VIDEO_MEDIA_REPORT.md)
  and the policy doc [`docs/REDDIT_VIDEO_QUALITY.md`](../REDDIT_VIDEO_QUALITY.md).

## Verification performed

```text
python -m compileall -q "testing area" tests     -> OK
python tests/test_smoke.py                       -> SMOKE TEST: ALL PASS
python tests/test_reddit_signals.py              -> REDDIT SIGNAL TEST: ALL PASS
```

Round-67 guards added (all offline and deterministic): EmbedEZ 1080p
success; 1080p failure → 720p success; EmbedEZ failure → vxreddit success;
vxreddit 1080-input lower-quality output (name ≠ quality); timeout and HTTP
failure; HTML body on a 200 transport; oversized media; missing
audio/failed mux; portrait; landscape; no usable video → thumbnail +
button; no duplicate poster image; image/GIF/photo/gallery unchanged; no
cache/state writes; bounded budgets; mode rollback. Plus the removal guards:
the active files contain none of the removed names, the removed Variables
are not wired anywhere, no removed decision function is called, and no
recheck reason can record a removed state.

## Deployment notes

- News-Express ships engine + workflow + tests + docs; the corresponding
  production repository files must receive the same final policy after this
  PR is accepted.
- Set the repository Variable `REDDIT_VIDEO_QUALITY` only if a mode other
  than `balanced` is wanted; `compatibility` is the instant rollback.
- Post IDs used in the evidence report are test evidence only and are not
  hard-coded anywhere in the monitor.

## Canary checklist (maintainer)

- [ ] Watch one full cron cycle with `balanced`: EmbedEZ 1080p success rate,
      added latency, native-ladder fallbacks.
- [ ] Confirm the log lines for rejected candidates and budget exhaustion.
- [ ] Confirm a portrait video keeps its framing (evidence IDs from the
      report; never hard-coded).
- [ ] Only then consider `highest`.
