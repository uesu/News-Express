# Changelog

Current, in-progress release notes for News-Express. This file covers
**round 63 onward** (2026-10-05 and later) — the state after "The Great
Simplification" rewrote the Reddit engine's delivery pipeline.

For everything before that, see the historical archive:

* [`docs/history/CHANGELOG_ARCHIVE.md`](history/CHANGELOG_ARCHIVE.md) — full dated changelog, rounds 1–62
* [`docs/history/ENGINE_HISTORY.md`](history/ENGINE_HISTORY.md) — detailed round-by-round engine notes
* [`docs/history/`](history/) — decision records per incident (`ROUND_*.md`) and other dated snapshots

Entries below are newest first. As this file grows, older entries may be
moved into `docs/history/` and replaced here with a pointer — they are never
rewritten when that happens, only relocated.

## Unreleased / current

* **2026-10-07 — Round 67: content-gate removal + video quality selection.**
  **Part 1 — complete removal of the content-advisory gate.** The Reddit
  engine no longer reads, classifies, holds, caches or logs any
  content-advisory metadata: the gate, its four repository Variables, the
  batched archive lookup, the Redlib badge reader, the crosspost-source
  checks, the allowlist and the fail-closed "unknown metadata" hold are gone
  from `reddit_main_v3.py`, `reddit_signals.py`, `reddit_monitor.yml`,
  `.env.example`, the tests and the current docs. A case-insensitive search
  for the removed names returns nothing in any active file; the truthful
  record of the removal — every removed name and behavior — lives in
  [`docs/history/ROUND_67.md`](history/ROUND_67.md). The remaining
  protections are unchanged: dedup cache, `FRESH_HOLD_SECONDS`, the pristine
  `/new` listing confirmation, the pending-recheck throttle, archive
  liveness, media handling and the opt-in retraction seatbelt. No cache,
  webhook, secret, proxy-order, image, GIF, photo or gallery behavior
  changed. **Part 2 — video quality selection.** `resolve_video_url` is now
  quality-aware and fully bounded: EmbedEZ 1080p and vxreddit are attempted
  together (vxreddit started first — it stays the winner path and the
  immediate fallback), a validated EmbedEZ 1080p result may replace it,
  EmbedEZ 720p is only tried when vxreddit itself is unusable, and the
  durable `v.redd.it` DASH ladder is the reliability floor before the
  thumbnail + Read Post button. Every candidate is validated (status,
  content type, HTML/JSON error body, 256 MiB limit, candidate timeout, and
  real MP4 dimensions + audio-track evidence read from the byte prefix) —
  a URL containing "1080" is never proof of quality, and signed/expiring
  `packaged-media.redd.it` URLs are never card media and are never
  persisted. New `REDDIT_VIDEO_QUALITY` Variable: `balanced` (default),
  `compatibility` (the pre-round-67 ladder, byte-order identical — the
  zero-code rollback) and `highest`. Strict budgets keep latency bounded:
  8 s quality window (15 s in `highest`), 20 s per proxy candidate, 10 s per
  native candidate, 40 s per post, 180 s of quality attempts per run.
  The opportunity covers every path that can put a Reddit video in a card —
  including the **proxy-delivered** video (the default configuration): there
  the round-49 wave's validated mux is the held base and one bounded EmbedEZ
  1080p candidate may replace it only against the base's own probe facts,
  while `compatibility` keeps that video verbatim with zero extra requests.
  Images, GIFs, photos and ordinary galleries make no quality requests at
  all. Evidence and the manual canary checklist:
  [`docs/REDDIT_VIDEO_MEDIA_REPORT.md`](REDDIT_VIDEO_MEDIA_REPORT.md) and
  [`docs/REDDIT_VIDEO_QUALITY.md`](REDDIT_VIDEO_QUALITY.md). **Part 3** — the
  manual media test report is committed as the round's evidence base.

* **2026-10-06 — Python automation documentation sanitation.** Current docs
  now spell out CPython 3.14.8, patch/minor/major terminology, wheels-only
  runtime bump validation, the 30-day new-minor soak, `AUTO_MERGE_PYTHON_BUMP=yes`
  as patch-only, `BUMP_PAT` as a secret reference only, the explicit runtime
  rewrite allowlist, and the absence of any direct-to-main fallback. Dependency
  docs now match the grouped Dependabot configuration, and production scope is
  clarified: News-Express development docs/history are not copied into the
  separate production repositories. Historical 3.14.7 records remain historical.
* **2026-10-06 — Docs: changelog moved under `docs/`.** Current release notes
  moved out of the README and into this file; the README's Changelog section
  is now a short pointer to `docs/CHANGELOG.md` (current) and `docs/history/`
  (archive), matching the structure used by Game-Express. No entries were
  rewritten — only relocated — and historical dates/versions in
  `docs/history/` were left untouched.
* **2026-10-05 — Docs: stale-gate sweep.** The current docs no longer
  describe gates that round 63 deleted. `AGENTS.md` drops the
  `mod_queue_reason` fixture invariant (the function no longer exists) and
  rewrites the duplicate-media landmine as history — the rule that survives
  is "do not reintroduce any media-fingerprint gate". `docs/CI_SMOKE.md`
  drops the removed `page_is_post_page` page-identity check and its
  shell-page scenario, stops calling the smoke suite's gate list a "queue"
  gate, and re-attributes the listing fixtures to the round-64 pristine
  listing confirmation and the round-44 retraction seatbelt — the checks
  the suites actually run today. The Privacy Policy and Terms of Service
  keep the same `/new` listing disclosures but credit them to those two
  consumers instead of the removed mod-queue gate (effective dates
  bumped). The 2026-10-01 audit record moved to
  [`docs/history/REPOSITORY_TRACKING_2026-10-01.md`](history/REPOSITORY_TRACKING_2026-10-01.md)
  with a historical-snapshot banner, and every reference was repointed. No
  engine, workflow, or test changes.
* **2026-10-05 — Round 66: long-post continuations + table rendering + stale env cleanup.**
  A post body that no longer fits the card's text budget is no longer
  truncated: the main card keeps the first chunk (identical layout —
  header, gallery, stats, buttons) and the remainder is delivered as up to
  3 follow-up messages — text-only Components V2 containers, same accent
  color, each opening with a small `-# (continued)` heading; beyond the
  cap the last message ends with `… full post on Reddit`. Retraction
  covers every part: continuation message IDs are recorded alongside the
  main card's, so the tombstone/delete pass hits them all. Every split —
  the main budget AND continuation boundaries — lands on a safe point
  (paragraph break → line break → space) and never inside a link, bare
  URL, `||spoiler||`, or bold/italic marker pair, fixing the live 1wxfuj5
  card that was cut mid-link (`[Set](https://…` rendered broken). Markdown
  tables — which Discord does not render — now convert to per-row
  `**bold-label**` bullets (the first header composes with the first cell:
  `**Patch 3.8**` + `- **Drip Market:** October 9/10, 2026` + …, matching
  the hand-checked example); malformed or ambiguous tables stay
  byte-identical and nothing is date-converted (the card's posted-time 🕐
  stays the only timestamp). `reddit_monitor.yml` env list cleanup: 11 mappings for gates
  removed in round 63 (settle windows, duplicate-media/repost/mod-queue
  gates, listing outage racing, approval recheck) are dropped, and the
  round-64 `FRESH_HOLD_SECONDS`/`LISTING_CONFIRM` are wired; round-61
  deploy steps untouched.
* **2026-10-05 — Docs: history folder.** All dated records now live in
  [`docs/history/`](history/) — the changelog archive (rounds 1–62),
  the engine round notes, and every `ROUND_*.md` decision record — with a
  short index. `docs/` keeps only the current topic guides. Stale deployment
  artifacts of already-merged rounds were deleted (`round_46b.patch`,
  `bump_3.14.8.patch` — superseded by the automated
  `python_version_bump.yml` workflow — and the copy-paste PR packages for
  rounds 42–45). Every cross-reference was repointed and link-checked.
* **2026-10-05 — Round 65: body entity hygiene.** Live 1wxvl13: a card built
  from the Arctic Shift backup path showed literal `&gt;` — Arctic (like
  Reddit's API) serves selftext HTML-escaped, and only the JSON path
  unescaped it. Every body path now HTML-unescapes exactly once
  (double-unescape explicitly tested against), and empty-blockquote artifact
  lines (a line that is only `>`) are dropped. Quoted content, and all other
  paths, are byte-identical.
* **2026-10-05 — Round 64: Pristine Listing Protocol.** A post now delivers
  only when a cache-busted, pristine read of the subreddit's /new listing
  proves it is live on the subreddit at that moment (unique `_fresh`
  cache-buster + no-cache request headers on every listing read — no stale
  CDN/cache view can linger). Not there → skipped, never blocked: it posts
  instantly on the tick it first appears. Plus a stateless
  `FRESH_HOLD_SECONDS=30` floor computed from the post's own timestamp — no
  trackers, no pending entries, no inference. `LISTING_CONFIRM=0` restores
  round-63 behavior. Dedup, the round-42/45 fail-closed content-advisory gate
  (REMOVED in round 67 — see
  [`docs/history/ROUND_67.md`](history/ROUND_67.md)), and the retraction
  seatbelt were unchanged at the time.
* **2026-10-05 — Round 63: The Great Simplification.** The Reddit engine is
  reduced to three protections: the dedup cache, the round-42/45 fail-closed
  content-advisory gate (polished: over_18 + thumbnail marker + subreddit
  flag + page markers on every data path; that gate was itself REMOVED in
  round 67 — see
  [`docs/history/ROUND_67.md`](history/ROUND_67.md)), and the opt-in
  retraction seatbelt (edit/delete/off — all three verified by tests).
  Removed: settle window, mod-queue gate,
  dup-media gate, repost gate, page-identity check, listing health guards
  and all their Variables. Posts now deliver as-is at cron speed.
* **2026-10-05 — Docs: README restructure.** The README was rebuilt around
  the current shipped behavior (hero + badges, features, setup, config,
  delivery pipeline, testing, troubleshooting). Every dated round-by-round
  note (~1,450 lines) moved verbatim to
  [`docs/history/ENGINE_HISTORY.md`](history/ENGINE_HISTORY.md); the dated changelog
  for rounds 1–62 remains in
  [`docs/history/CHANGELOG_ARCHIVE.md`](history/CHANGELOG_ARCHIVE.md). No behavior,
  engine, workflow, or test changes.
