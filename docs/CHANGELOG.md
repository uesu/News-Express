# Changelog

## Unreleased — Round 91: production-sync hardening + CPython 3.14.9 (2026-10-26)

### Production sync (both live repos)

- **Fixed a live production failure.** `uesu/7jkxmy9nvbc` and `uesu/wvkhabh2s22`
  were failing every `Python version bump (auto)` run at *Rewrite the allowlisted
  current-runtime files* with `::error::Expected runtime file missing: README.md`:
  `sync_prod.py` copies `python_version_bump.yml` into both production repos but
  never copies `README.md` or `docs/*`, which sat in the mandatory allowlist. The
  allowlist is now split into **required** surfaces (present in every checkout)
  and **optional** dev-only ones (rewritten where present, skipped with a
  `::notice::` where absent), and the `docs/PYTHON_RUNTIME.md` slug `sed` is
  guarded.
- **No more pin downgrades.** `.github/scripts/sync_prod.py` merges workflow files
  monotonically instead of overwriting them: a `python-version:` pin or SHA-pinned
  `uses:` that production already advanced is preserved, so a dev-side sync can no
  longer undo a production Dependabot/Python bump. The deployed
  `tests/test_smoke.py` r39 pin is re-aligned to the deployed `ci.yml` afterwards.
- Dev-only root markdown (`PRIVACY_POLICY.md`, `TERMS_OF_SERVICE.md`) joins the
  exclusion list, and the unused `import json` is gone.

### Runtime

- CPython pin `3.14.8` → `3.14.9` across the allowlisted runtime surfaces (the
  `actions/python-versions` Linux x64 build published 2026-10-21). Documentation
  now states the runner-image publication date instead of a CPython release date
  this repository cannot verify, and version examples are version-agnostic so the
  automated rewrite cannot turn them into nonsense.

### Guards

- `r91a` — every **mandatory** allowlist path must exist in a real production
  checkout; every **optional** one must genuinely be absent there.
- `r91b` — newer production pins survive a dev-side sync, dev-side workflow
  content still lands, the deployed r39 guard re-aligns, and the merged tree is
  idempotent.
- `r91c` — dev-only root markdown is excluded and never synced.
- `r89c` — reworked: it now runs the real rewrite shell in **both** layouts and no
  longer invents fixtures for missing files (that fixture is exactly why the
  production failure went unseen).

See [Round 91](history/ROUND_91.md) for the reproduction, evidence and limits.

## Unreleased — Round 90: multi-page indicator, proxy stats for text posts, formatting preservation (2026-10-26)

### Reddit delivery

- Long posts now say where you are: the main card ends `… • 📜 Page 1/N` and every
  continuation ends `-# 📜 Page n/N`. Single-page cards are byte-identical to before
  (no `Page 1/1`), and the printed page count is settled by a bounded fixed-point
  loop so it always matches the number of continuation messages actually sent.
- Text-only posts keep the `💬`/`👍` counts a proxy already observed (the `else`
  branch now reuses the same text/stats helper), and `fetch_proxy_post` backfills
  stats from a sibling wave responder instead of dropping them. Counts are never
  forced or fabricated: no source, no counts.
- Formatting survives delivery: HTML `<strong>`/`<b>`, inline CSS bold spans,
  `<h1>`–`<h6>`, `<i>`/`<em>`, `<del>`/`<s>`/`<strike>`, Markdown `####`–`######`
  subheadings (rendered as `**bold**`) and native `>!spoiler!<` (rendered as
  `||spoiler||`) outside code spans. JSON `selftext` is cleaned with a
  paragraph-preserving helper whose HTML detection is tag-agnostic — a narrow tag
  list leaked raw `<pre>`, `<code>` and inline-styled `<span>` markup into cards.
- Splits close and reopen fenced code blocks and inline `**`/`||`/`~~` emphasis
  across page boundaries inside the character budget; `~~…~~` and inline code are
  now protected spans.

See [Round 90](history/ROUND_90.md) for provenance, the corrected HTML router,
fuzz/parity evidence and limits.

## Unreleased — Round 89: zizmor-verifiable pins, CI annotation hygiene (2026-10-26)

### Development surfaces (no runtime/live change)

- Make every workflow action pin auditable by online `zizmor` again: version
  comments are bare `# vX.Y.Z` (prose on the line above), `actions/setup-python`
  moves to `v7.1.0` (`6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`), and
  `actions/checkout` / `actions/github-script` keep their commits with exact
  `v7.0.1` / `v9.0.0` tags. `runs-on: ubuntu-latest` stays everywhere so runner
  OS updates roll forward automatically.
- Fail the smoke suite (`r89d`) if the suite's own stdout ever emits a GitHub
  Actions workflow command (`::error::`, `::warning::`, `::notice::`, `::group::`,
  `::endgroup::`), so simulated faults cannot annotate a green run.
- Cover the dev-only `.github/workflows/sync_prod.yml` Python pin in the runtime
  bump when the file is present and skip it with a notice when it is absent (both
  production repositories receive the bump workflow but never `sync_prod.yml`);
  a missing required surface still fails closed.

See [Round 89](history/ROUND_89.md) for the reproduction, guards and limits.

## Unreleased — Round 88: full Reddit text and Twitter recovery (2026-10-25)

### Integration and final edge checks

- Integrate the complete sibling handoff for full Reddit text and queued Twitter GET revalidation.
- Persist multipart main-card ambiguity before POST, retain delayed-completion evidence for a full retention window, and reject malformed nested continuation progress before resuming.
- Report cache-load failure as incomplete, count resumed progress as saved local state, and bound Twitter revalidation GETs to 15 seconds. Exhausted recovery logs describe observed metadata without asserting Discord refused the asset.
- Retry proven pre-send connector failures without reconciliation; keep uncertain-response holds.
- Add interruption/rejection/restart/retention regressions and refresh local compatibility/CPU benchmark evidence in the PR. Existing deployment remains gated on a reviewed merge.

### Round 88: continuation and Twitter recovery handoff

- Reconcile setup/privacy/tracking documentation with the tested full-body and pre-edit revalidation enhancements. Correct stale three-page and retraction-only cache instructions; ignore atomic-save scratch files. No engine, provider, media-heal, schedule, Secret or Variable changes in this documentation follow-up.
- Preserve earlier history and record the authorized cap replacement, compatibility evidence, request/storage costs and recovery limits in [Round 88](history/ROUND_88.md).

### Retain dedup evidence after the last continuation

- Recover main-card dedup from completed continuation records as well as partial ones. A crash after the last page save but before the ordinary dedup save must not repost a completed card. Recovered keys count as newly saved keys for retention and persistence checks.
- Add an offline restart regression exercising the actual main loop, saved message IDs, missing dedup file and a repeated feed entry; it failed before the repair.

### Complete Reddit body continuations

- Remove the 16,000-character ingestion cap and three-continuation cap. Deliver all retrieved text in content-driven pages, keeping main-card media, stats and buttons intact. This intentionally supersedes Round 66’s cap.
- Persist continuation payloads, confirmed page IDs and next index independently of retraction. Resume explicit rate-limit rejections after Retry-After; stop at the first failure and hold uncertain outcomes for reconciliation instead of skipping or duplicating pages. Keep webhook credentials out of state.
- Cover part five, 40k-plus text, ten-plus pages, unbroken tokens, all message IDs, disk round-trip retry, and ambiguous-response holds offline. No production backfill or cache reset.

### Revalidate Twitter media before recovery edits

- Re-read queued Discord messages after the existing recovery delay and before each PATCH. Skip edits when no eligible unresolved media remains; stop on 401/403/404. Transient revalidation failures retain the existing bounded recovery.
- Preserve video-only defaults, identical PATCH payloads, four-attempt ceiling, proxy priority and GIF conversion. Healthy posts never enter this path; each queued attempt adds at most one GET.
- Offline media tests cover resolved-during-wait, still-unresolved, unavailable revalidation, and deleted/inaccessible messages. No production messages or caches are modified by testing.

## Unreleased — attended workflow updates (2026-10-18)

- Keep eligible package-only Dependabot auto-merge; require attended merges for
  workflow-path updates, including renamed/deleted files. Fetch all PR file pages.
- Continue Python detection/validation/publication but remove Python auto-merging;
  the legacy AUTO_MERGE_PYTHON_BUMP variable is no longer consulted.
- Preserve News exact pins, current validation and new-minor soak period.
- GitHub security approval can still be required; check real live execution
  after an attended update. No posting/state/scheduler or dependency-range change.

## Unreleased — application-only scope (2026-10-17)

- Improve existing summary output in place; no new reporting module or runtime
  file. Keep unmeasured values unavailable and preserve real cache-push status.
- Clarify privacy/terms disclosures for retained logs/summaries and repository
  access; preserve attribution and warranty provisions.
- Recover crosspost motion media from validated one-hop originals; reuse
  completed archive lookups (including misses/errors) and embedded parent data.
- Correct timestamp-prefixed Twitter feed counters in the existing workflow.
- Leave dependency/Python/Dependabot/update automation and posting/state rules
  unchanged. Proposed code, not a claim of production deployment.

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

* **2026-10-24 — Round 87: Automated dev → prod repository sync (`.github/workflows/sync_prod.yml` + `.github/scripts/sync_prod.py` → `uesu/7jkxmy9nvbc` & `uesu/wvkhabh2s22`).**

  - **Automated atomic multi-repo sync:** Runs `compileall` and all three offline suites (`test_smoke.py`, `test_reddit_signals.py`, `test_twitter_media.py`) on every push to `main` (and on manual `workflow_dispatch`) before atomically syncing `testing area/`, `tests/`, `.github/scripts/`, `.github/workflows/{ci,dependabot_auto_merge,python_version_bump,reddit_monitor,twitter_monitor}.yml`, `.github/dependabot.yml`, `.gitignore`, and `requirements.txt` to both `uesu/7jkxmy9nvbc` (Reddit prod) and `uesu/wvkhabh2s22` (Twitter prod) in a single commit per repo — eliminating the Round-75 "smoke guard landed before engine" manual upload race.
  - **Strict live cache protection & concurrent monitor retry:** Never creates, overwrites, stages, or deletes `posted_reddit.json`, `pending_reddit.json`, `proxy_health.json`, `posted_tweets.json`, or `posted_messages.json`; excludes dev-only docs (`docs/`, `README.md`, `AGENTS.md`, `.env.example`) and `sync_prod.yml` itself from production; retries with `git fetch` + `reset --hard FETCH_HEAD` if a 5-minute monitor cache commit lands mid-push; and falls back to non-workflow sync with a clear warning if the token (`secrets.PROD_SYNC_PAT || secrets.BUMP_PAT`) lacks `workflow` scope.

* **2026-10-24 — Round 86: Reddit fleet expansion (23 → 25), `REDLIB-REACH:` Step Summary, and 6 production log fixes (`#9626`, `#9651`, `#9659`, `#9662`, `#9669`, `#9677`).**

  - **Reddit fleet expansion (`23 → 25`):** Appends `https://redlib.reallyaweso.me` (`[23]`, live-verified `200 OK` on `/r/<sub>/new`, `/user/<acct>`, and `/r/<sub>/comments/<id>/`) and `https://redlib.ducks.party` (`[24]`, `v0.40.0` `200 OK` `/r/<sub>/new` listing with inline gallery carousels) at the tail of `REDDIT_RSS_INSTANCES`, preserving indices `0..22` with zero deletions.
  - **Step Summary instance telemetry (`REDLIB-REACH:`):** Records `redlib_reach`, `redlib_reach_answered`, `redlib_reach_probed`, and `redlib_instances_configured` in `reddit_run_result.json` and surfaces `- Instances (REDLIB-REACH): ...` under `### Providers and media` in `.github/workflows/reddit_monitor.yml` `$GITHUB_STEP_SUMMARY` with `monitor.log` fallback and zero network calls.
  - **Flood-cap ordering fix (`#9651`):** Moves `known-pending` (`_pending_throttle_skip`) and stateless `FRESH_HOLD_SECONDS` filtering ahead of `cap_new_posts(new_posts, MAX_POSTS_PER_RUN)` so suppressed archive ghosts no longer inflate `len(new_posts)` and falsely trigger `POST FLOOD GUARD` drops.
  - **Duplicate proxy wave & gallery enrichment skip on archive video posts (`#9662`):** `fetch_proxy_post_memo(..., need_video=True)` now reuses an already-cached `(id, path, False)` liveness probe when it holds a motion video (`_proxy_result_has_motion_video`), and `resolve_post_media()` gates `enrich_gallery_redlib` on `not (has_video or arctic_is_video or base.get("vred_id") or base.get("redgifs_url"))`.
  - **Exact `reddit.com` host check & error-shell detection:** `_is_direct_reddit_host()` checks exact `reddit.com`/`www.reddit.com`/`old.reddit.com` hostnames so `[17] https://safereddit.com` is no longer skipped by substring matching (`"reddit.com" in instance`), and `_is_redlib_error_page()` detects backend-issue, clearnet-retired, rate-limit, and `__goaway_challenge` shells.
  - **Accurate provider attribution & tie-break logging (`#9626`, `#9659`, `#9669`, `#9677`):** `resolve_post_media()` tracks `media_provider` (`vxreddit`, `embeddit`, `redditez`, `arctic`, `redlib`, `native`, `full`) and `proxy_media_used`, logs `card media via arctic` on the `arctic_items` gallery branch, eliminates `provider=unknown` / `| native |` misattribution on proxy-resolved image cards, and logs `tied ... preferring higher-priority <service>` on equal-count priority tie-breaks in `reddit_proxy.py`.

* **2026-10-23 — Round 82: Reddit fleet expansion (19 → 23, Game-Express PR #63 parity).**

  Adopt Game-Express PR #63 `fabbe4c` live-verified 2026-10-23 Redlib fleet: `19 → 23` entries with **zero hosts deleted** (keep `redlib.nohost.network` + `redlib.kylrth.com` which Game-Express excludes as traps/Azure-gated). **Round 83b fix:** preserve R78 19-member order exactly (`www`/`old`/`miningtcup`/`catsarch`/`privacyredirect`/`snoo`/…/`nadeko` 0-18) and **append** 4 new hosts at tail (19-22: `mint.lgbt`, `jeremyh.xyz`, `jeikobu.net`, `vanillax.me`) so they do not affect prior 19 priority — PR #76 had moved `mint.lgbt` to head and `www`/`old` to Tier 3, causing `REDLIB-REACH 11/23` with `catsarch`/`snoo`/`miningtcup`/`nohost`/`idevicehacked` `0/1` → `redlib gallery enrichment failed (all instances)` → every post `archived counts` with `media=text|native|0` (observed #9560/#9563 `HonkaiStarRail_leaks` `1xd8ofn`/`1xd8vra`, ZZZ `1xd8ppc`). Appended tail restores media (`catsarch` etc. priority unchanged) while keeping new hosts for redundancy (R78 order verbatim; `privacyredirect` stays at #4). **Savings/calls unchanged:** concurrent first-win `_fetch_new_listing` (8 s) + combined RSS `1 req/run` + `REDDIT_FEED_TOKEN` memoization `≤1 JSON req/run` — Tier 3 tail 0 hits while Tier 1 healthy. Tests: `R78 19 preserved 0-18`, `r82 23-member appended tail` + `no-deletion` 19→23, `SMOKE TEST: ALL PASS`.

* **2026-10-23 — Round 80: emoji outside link (Discord forward fidelity).**

  AnantaLeaks `1xd1tks` `"You'll never guess where the game starts😂"` posted as `### […😂](url)` — renders in-channel but Forward shows raw `([https://…/… ) *by` leak (Discord Components V2 `### [title](url)` strict). Trailing emoji now outside the markdown link: `### [clean](url) 😂` for **all future posts** (every sub, every title) via `_split_trailing_emoji80` (`unicodedata So/Sk` + `ZWJ/VS/skin-tone/flag` sequences, `clean.rstrip()`); empty-title guard keeps `😂`-only titles inside. Original HTML/JSON/sources untouched, presentation-only, 0 extra req, no perf loss. `compileall OK`, `SMOKE TEST: ALL PASS` (emoji helper unit + full suite).

* **2026-10-23 — Round 79: token-powered JSON-first instant fallback.**

  JSON-first: `REDDIT_FEED_TOKEN` on `auto` (default) now powers `www.reddit.com/comments/{id}.json?limit=25&raw_json=1&{feed_q}` FIRST (host/path-agnostic `format_reddit_feed_query`, `BROWSER_HEADERS`), instant 1-request fallback to combined `.rss` on datacenter 403. Stagger capped `min(FEEDTOKEN_JSON_STAGGER,2)` for token tier vs `65 s` anonymous, 403 remembered per run (`_feedtoken_json_failed`), ≤1 JSON req/run (first new post only, memoized). No Secret/Variable change needed (`auto` valid token = enabled, empty/invalid = OFF per r31, `force`/`off` unchanged); header `1b` wording updated from stale Round-31-only to Round 79.


  Tests: `r31 auto without app OFF` preserved, R25 extraction intact, `SMOKE TEST: ALL PASS`.

* **2026-10-22 — Fleet refresh: 16-member Twitter + 19-member Reddit fleets + docs cleanup.**

  Twitter V3 expanded from 12 to 16 (Round 77 2026-10-22): Teapawt operator expansion adds `teapaw.org`, `teapawt.net`, `teapawt.org` (same 4cuck/teapawt 0.19.0 stack as `nitter.cf`/`xitter.cf`, verified same SOCKS5 exit + `fetch_page` top-id parity), plus `nitter.mie.foundation` from Codeberg shitter wiki (verified RSS top-id parity) — both placed as trials per runner-evidence rule (no datacenter-block host above a non-blocking one). Reddit V3 refreshed to 19-member `REDDIT_RSS_INSTANCES` (same code already on `main`): 8 verified dual-path hosts (`catsarch`, `privacyredirect`, `snoo.habedieeh.re`, `tiekoetter.com`, `nohost.network`, `privadency 1/2`, `idevicehacked`) + 5 listing-only reserves (`artemislena`, `awy.one`, `kylrth.com`, `freedit.eu`, `utilibre.org`) + 3 tail restores (`privadency.com`, `safereddit.com`, `nadeko.net`) kept at tail per live prod #9283 2026-10-22 03:35 UTC `REDLIB-REACH 4/9` partial/timeout-still-works verdict. Docs fully cleaned: README resilient-feeds count, Nitter credits order (16), Redlib credits (19, refreshed 2026-10-22), PRIVACY/TERMS Redlib instance lists, AGENTS invariant, plus earlier 2026-10-21 pristine removal consistency (PRIVACY/TERMS/CI_SMOKE). Historical snapshots under `docs/history/` intentionally preserved verbatim per header.

* **2026-10-21 — Reddit delivery cleanup: pristine-listing removal, accurate completion/persistence reporting, secret-redacted diagnostics.**

  Remove the mandatory pristine listing-confirmation dependency (`LISTING_CONFIRM` parsing, cache, `_fresh`/`no-cache` headers, gate branches, workflow wiring, docs/tests) per the approved handoff. The `FRESH_HOLD_SECONDS` floor (default 30 s, stateless) and posted-post deduplication are preserved. Useful pending suppression with bounded timed retries (48 h expiry, source-provenance `rss`/`arctic`), provenance-aware RSS reconsideration (still subject to removal checks; archive/media presence not proof of visibility) and bounded transient retry are retained.

  Reddit logs now use stage-accurate aggregated `INFO` (considered/entering/delivered/known-pending/retry-backoff/fresh-hold/etc., removal/liveness at `INFO` with conditional wording) with per-candidate `DEBUG`; the misleading “Found X new Reddit posts” wording is removed. The Actions run summary is derived from a stable local `reddit_run_result.json` record (inline YAML Python, validates JSON object, handles missing/malformed/wrong-shape as `unavailable`, no scraping or extra network calls):

  - Completion is `completed` true only after required work including persistence; `normal`/`no-candidate`/`dry-run` completed vs `failed`/`interrupted` incomplete (not by JSON write/`finally`), dry-run explicitly labelled (`skipped_dry_run`), no claim of live delivery/persistence for dry-run; failures during or before required persistence are `incomplete` with `not-reached` (only never-started) vs `failed` distinction (preparation/copying/recovery-reset/staging/commit/push failures all `failed`, entered defaults to `failed`, confirmed no-change `unchanged`, confirmed `saved`), and `finally` does not overwrite success.
  - Local persistence (`unchanged`/`saved`/`failed`/`not-reached`/`skipped_dry_run`, preparation `git config`/`git add`/`cp`, copying `mktemp`/`cp`, recovery `fetch`/`reset`/`merge`/`staging`/`commit`, and push failures all `failed`) and repository persistence (same set, observed commit/push, `unchanged` vs `saved` distinct, dry-run explicit; local save not conflated with repository push) are reported separately and not conflated; the real workflow persistence shell is syntax-checked with `bash -n` and mocked for `unchanged`/`successful push`/`recovered push`/`copying`/`recovery-reset`/`staging`/`commit`/`push` `CACHE_RESULT` in tests (no copied test-only shell).
  - Error messages are sanitized and bounded (webhook URLs, `token=` query, `Authorization:[^\n]*`/`Bearer` redacted to `[REDACTED]`, bounded 500 chars, exception type/operation/category preserved, safe diagnostics retained; no leak in JSON/summary/logs; delivery decisions unchanged; original exception remains observable).
  - Provider/media diagnostics are retained locally without extra network requests, distinguishing zero vs unavailable and reported separately when observed: proxy warmup `ok`/`disabled`/`failed`/`unavailable` with service map, video quality mode `balanced` default (`highest`/`compatibility`), media resolved via provider, final media endpoint/hosting category, final card media kind and tile count, optional quality candidate result, whether validated base was retained, terminal media fallback (proxy→native, distinct from feed fallback `ok`/`partial`/`all_failed`/`not_attempted` and quality fallback), heal queued/edit-performed/skipped-after-revalidation; neither warmup, HTTP validation, player controls nor “chain complete” proves audio inclusion and Embeddit remains video-only; per-candidate logs remain supporting evidence. Production baselines #8982 (`1xbbdbs` direct video retained after EmbedEZ failure (HTTP 400, `quality_candidate_unavailable`), 1 tile, 3 buttons, `8ace078`), #8988 (`1xbby22` vxReddit image retained after Redlib enrichment failure (not terminal fallback, provenance preserved), `caa7421`) and #8989 (`1xbc1mn` vxReddit 720p retained after EmbedEZ failure (HTTP 400, `quality_candidate_unavailable`), heal queued then skipped after revalidation cleared, `60fb8f7`) are recorded as successful baselines, not defects requiring audio/muxing/provider rewrite or repost/edit (new counters not emitted by historical runs; expected new reporting for equivalent mocked scenarios).

  Documentation, `.env.example`, `AGENTS.md`, `README` and `docs/REPOSITORY_TRACKING.md` updated; `reddit_run_result.json` remains reporting-only, ignored per-run (not delivery state, not cache-merge input, not Twitter state); historical audits preserved. Tests moved into existing suites (no standalone formatter/cleanup-test file) and verify normal/no-candidate/dry-run/failure paths, unchanged-vs-saved, secret-redaction, provider diagnostics and summary-generation without network.

* **2026-10-20 — Plain-text profile crosspost attribution.**

  The `🔁 Crosspost of u/<name> Profile` line for profile crossposts
  (`/user/`, `/u/`, `/r/u_<name>/` permalinks) is now plain text — the
  user-profile Markdown hyperlink is removed from this branch only. The
  username and `Profile` wording stay; subreddit crosspost links, Read Post
  destinations, crosspost resolution, source selection, media, statistics
  and delivery/rate-limit behavior are unchanged. Future deliveries only —
  no edits to already-posted Discord messages and no state reset.

* **2026-10-19 — Table/continuation documentation housekeeping.**
  Align README, `.env.example` comments and the CI guide with the merged generic
  HTML/Markdown table renderer and removal of generated continuation labels.
  Keep supported-shape limitations explicit. No runtime, workflow, settings,
  cache, schedule or delivery changes; no new Variable or live test required.

* **2026-10-19 — Remove generated Reddit continuation labels.**

  Follow-up body messages now start directly with the remaining source text,
  without the bot-added `(continued)` heading or a leading newline. Keep
  the same accent, message count cap, 3800-character component limit,
  safe Markdown splitting and overflow tail. Source-authored wording is
  unchanged. Future deliveries only; no edits or reposts of existing messages.

* **2026-10-19 — Reddit HTML table preservation (future posts).**

  Run #8358 delivered WutheringWavesLeaks `1x9geq7`, but its RSS HTML
  table became a flat list before the Markdown-only formatter could run.
  Preserve innermost rectangular HTML tables with TH headers before tag
  stripping and render them as bold row headings plus `- Column: value`
  bullets, using the same formatter as Markdown tables across subreddits.
  Decode entities, preserve literal dates, wording, links and pipes; leave
  unsupported spans, layout tables and malformed widths to existing cleanup
  rather than infer missing structure. No network, gates, state, media,
  continuation limits or historical messages are changed. Regression input
  for `1x9geq7` is a screenshot transcription, not a fetched raw capture.
  Deploy the engine file after review; do not reset or replace production
  caches. Already-flattened upstream text cannot safely be reconstructed.

* **2026-10-15 — Round 76: the runner-clean head + the xcopy.uk verdict.**
  `xcopy.uk`'s round-75 seat-3 trial ended with a measured runner refusal:
  Game-Express's first four post-merge runs (#2662–#2665, 2026-10-14
  17:19–17:30 UTC) got HTTP 403 on all six handles, every run, from four
  Azure regions (westus, westus3, eastus2, centralus) — 24/24 fetches
  refused — while an off-runner probe the same afternoon read a clean 8/8
  body with `nitter.cf` parity: the `nitter.kareem.one` signature. The
  operator set this round's ranking rule — **no member that blocks GitHub
  Actions / Azure datacenter IPs (or datacenter IPs generally) sits above one
  that doesn't** — and directed the head for both monitors: the operator pair,
  then `nitter.meowing.monster` (4 → 3) and the token-gated
  `nitter.miningtcup.me` (8 → 4), making the chain head entirely runner-proven
  for the first time. The probe round ranked the rest on union coverage (all
  eight handles both monitors watch): `nitter.freedit.eu` 5 (8/8, zero
  refusals anywhere), `nitter.gravitywell.xyz` 6 (5/8; `GenshinImpact` gap
  newly observed alongside Wuthering_Waves/HonkaiNA), `tw.eir-nya.gay` 7
  (passes the rule but holds the only measured runner non-deliveries and
  429-throttled every GE-handle probe), then the measured runner refusals:
  thepixora 8 (flapping 403), kareem 9 (standing 403), **xcopy 10 — demoted,
  not deleted**. The walled tail stays last. Membership stays twelve; the
  operator pair untouched; Reddit untouched. The smoke suite pins the new
  exact order; the r75 "eir-nya ahead of the token fallback" relative guard is
  updated in place into the round-76 rules. See
  [`docs/history/ROUND_76.md`](history/ROUND_76.md).

* **2026-10-15 — Housekeeping (same PR as round 76): stale words and dead
  constants.** No behavior change. `twitter_v3.py` drops three never-referenced
  leftovers — the retired round-34 `MAX_CACHE_SIZE = 500`, an unused
  `MAX_AGE_SECONDS` and the unused `_env_float` twin (the float reader lives
  in `reddit_proxy.py`, where it is used) — rewrites the pre-round-59 fleet
  header above `RSS_INSTANCES` into the current serial-chain / runner-evidence
  / demote-not-delete rules, and fixes the `docs/ROUND_56.md` →
  `docs/history/ROUND_56.md` pointer. Everything that still described two
  offline suites now names all three: `python_version_bump.yml` runs
  `tests/test_twitter_media.py` in both of its verify steps (it had claimed
  parity with CI since round 73 without it), and `README.md`,
  `docs/CI_SMOKE.md`, `docs/DEPENDABOT.md` and `docs/PYTHON_RUNTIME.md` say
  so. The README's "11-instance" fleet line and its round-59 credits order are
  replaced by the twelve-member round-76 order and ranking rule, the
  troubleshooting entry no longer sends you to the retired tracker method, and
  `docs/REPOSITORY_TRACKING.md` joins the docs index. `AGENTS.md` gains the
  fleet invariant (operator pair, no-datacenter-block rule, demote-not-delete,
  engine-before-guard deploy order) and lists every current topic guide;
  `.env.example`'s round-63 note names the checks that actually remain. A
  duplicate `import tempfile` leaves `tests/test_smoke.py`. On operator
  request the pass also dropped the identical retired `MAX_CACHE_SIZE = 500`
  from `reddit_main_v3.py` (cosmetic; no behavior change, no guard depends on
  it) and corrected the displayed text of six `docs/history/` links that
  still read `docs/ROUND_NN.md` after the 2026-10-05 move (targets were
  already correct).

* **2026-10-14 — Round 75: Twitter RSS fleet re-ranked + Redlib RSS audit record.**
  The initial `nitter.meowing.monster` demotion was reversed the same day
  after the host revived around 13:35 UTC (d420 healthy from 13:45; version
  `2026.10.12-f97b733`; 5/6 handles served from IPv4 runners). The earlier
  production precheck saw no meowing delivery, but the serial chain had
  stopped at an earlier serving host and had not tested its recovery. The
  operator directed `xcopy.uk` to seat 3 after an 8/8 full-coverage parity
  test against `nitter.cf`; the probe round ranked meowing 4, `tw.eir-nya.gay`
  5, `nitter.freedit.eu` 6, thepixora 7 (recent runner-403 watch), token
  fallback miningtcup 8, `nitter.gravitywell.xyz` 9 and `nitter.kareem.one`
  10. The fill-in sweep grows the fleet from ten to twelve: freedit.eu (5/5
  current bodies, no runner history) and gravitywell.xyz (3/5, complementary
  gaps to kareem.one) enter as trials; `nitter.pp.ua` is excluded as a
  thepixora feed alias. The operator pair remains in seats 1–2; the two
  challenge/interstitial hosts remain at the tail and nothing is deleted.
  Reddit V3 remains comments-only: all six Redlib `.rss` candidates returned
  the same upstream Reddit 400, the HTML `/new` listing remains usable, and
  list membership/order plus native-first behavior and round-64 checks are
  unchanged. The smoke guard pins the final 12-member Twitter order and
  unchanged Reddit membership. No workflows, proxies, gates or media paths
  changed. See [`docs/history/ROUND_75.md`](history/ROUND_75.md).

* **2026-10-13 — Round 74: Reddit cold Discord video-proxy healing.** Reddit
  V3 now recognizes the observed cold-proxy response: a video tile has a
  Discord `proxy_url`, but does not yet have both positive dimensions and a
  `video/*` content type. The existing explicit non-positive-dimension signal
  remains supported; sparse metadata without a proxy attempt is still unknown
  and is not queued. Initial delivery, selected provider/URL, and the delayed
  revalidation path are unchanged: after the default six-second wait, one
  Discord GET skips the edit if the proxy has resolved, otherwise at most one
  identical PATCH is sent. Healthy videos, photos, provider selection and
  Twitter behavior are unaffected. Focused offline regression checks cover
  cold, sparse-without-proxy, healthy, image-only, resolved-during-wait and
  still-cold cases. See [`docs/history/ROUND_74.md`](history/ROUND_74.md).

* **2026-10-13 — Round 73: Twitter mixed-media order + GIF fallback quality.**
  Two X (Twitter) V3 media-presentation fixes. (1) The gallery now follows the
  tweet's **canonical order**: FxEmbed/FxTwitter's `media.all` (its own
  `extended_entities` order — verified in the FxEmbed processor, not inferred)
  is read instead of photos-after-videos, so a mixed post keeps the observed
  live order `JPG → GIF 1 → GIF 2 → GIF 3` and GIFs/videos keep their
  chronological order relative to each other. Photo-only and video-only posts
  with valid media URLs preserve their previous order and output (entries
  without a usable URL are safely omitted instead of becoming empty tiles, the
  one deliberate difference for malformed payloads), providers without
  `media.all` (vxtwitter, twitterez) keep the legacy videos-then-photos order,
  and ordering costs no request and mutates no payload. (2) GIF fallback
  selection now classes every converter answer by its **actual returned
  content type** — an `image/webp`/`image/gif` animated answer wins, a `.gif`
  URL that answers `video/mp4` is rejected, and the extension is never
  trusted. An AVIF answer is remembered but never preferred: the **original
  mp4 always outranks it** (an AVIF can preview as a static frame in Discord's
  gallery while still animating when opened), and the AVIF is used exactly
  once per GIF as a last resort — a GIF whose mp4 is oversized, has no
  playable variant, and has no animated WebP/GIF rendition. The chain is
  probed **once per GIF** (`probe_gif_candidates`, ≤ 4 HEADs) and an AVIF it
  remembered is reused rather than re-discovered, so the last-resort path
  adds at most the 2 AVIF-route HEADs and never repeats the four candidates;
  the chosen AVIF's real source is logged as `<source>-avif`; if that is down
  too, the round-11 thumbnail + "Watch on X" fallback stands.
  The evidence-based heal contract is unchanged: healthy media posts
  immediately with no delay, no revalidation and no edit, only media Discord
  explicitly reports as unresolved and in scope enters the in-memory queue
  (one identical bounded PATCH after the posting loop), a provider fallback
  alone never triggers a heal, and no new Variable is wired. New focused suite
  `tests/test_twitter_media.py` (offline, wired into CI) covers canonical
  ordering, the chain and its content-type rules, mp4-vs-AVIF priority, the
  direct-mp4 fallback, the single-probe performance contract and the heal
  contract; the round-11/47/56/70 smoke guards pass unchanged. See
  [`docs/history/ROUND_73.md`](history/ROUND_73.md).

* **2026-10-12 — Round 72 follow-up: explicit-evidence + revalidated Reddit
  proxy-video heal.** The shipped round-72 pass inferred "unresolved" from
  missing metadata, so Discord's sparse-but-healthy create responses could
  re-edit a card that already rendered. Two corrections to the same one-card
  path: (1) a repair is queued only on explicit evidence — a returned
  `width`/`height` `<= 0`; omitted fields, `null`, non-numeric values and an
  empty `content_type` are unknown, not failure (empty type alone is no longer
  evidence); (2) the queued edit re-reads the delivered message
  (`GET …?with_components=true`) and PATCHes the identical payload only when
  one of the EXACT URLs the create response queued is still explicitly
  unresolved — a healthy or sparse revalidation means no edit, an unrelated
  video component in the same message can never trigger a PATCH, and a failed
  revalidation fails closed. Initially healthy videos are never flagged (no
  edit, no delay, no revalidation); a flagged candidate always spends one
  revalidation read, and no PATCH when it has rendered by then. Video classification
  stays provider-agnostic (video-rendition URL or Discord's `video/...` type,
  no proxy hostname list); native Reddit media and ordinary posts are still
  untouched, repairs stay bounded to one concurrent edit, and both Variables
  keep their defaults and workflow wiring. The round-72 smoke section grows
  from 24 to 59 guards, including the 2026-10-12 production regression and the
  URL-specific revalidation end-to-end through `main()`. See
  [`docs/history/ROUND_72.md`](history/ROUND_72.md).

* **2026-10-12 — Documentation/configuration audit: retain Reddit operational pending state.**
  Canonical `main` and both production repositories still run Reddit V3 code
  that reads and writes `pending_reddit.json`; the empty object is not evidence
  that the active cache is obsolete. Current docs now distinguish those
  operational rechecks from the stateless round-64 fresh-age/listing checks,
  clarify Twitter V3's response-based in-memory media-heal queue, document
  `MEDIA_HEAL_SCOPE`, and mark Round 72 shipped in merged PR #59. No runtime,
  workflow persistence, cache contents, or production repository was changed.

* **2026-10-12 — Round 72: Reddit proxy-video cold-start media heal.**
  Discord may initially show a 0×0 or failed tile for a video that becomes
  playable shortly afterward. Video cards request a message ID (`wait=true`)
  so the returned gallery metadata can identify unresolved video tiles.
  Only unresolved non-native videos get one identical same-message webhook
  edit after delivery and a bounded default 6-second delay; healthy videos
  get no edit. Detection covers future providers without a hostname list
  (refined by the follow-up entry below: a tile is covered when Discord
  returns a video type or the URL exposes a recognized video rendition, so an
  untyped extensionless URL is deliberately left untouched).
  Native media is not edited; ordinary cards, provider selection, YouTube and
  dedup behavior remain unchanged. `PROXY_VIDEO_HEAL=0` disables it;
  `PROXY_VIDEO_HEAL_DELAY` adjusts the delay (0–60 seconds). See
  [`docs/history/ROUND_72.md`](history/ROUND_72.md).

* **2026-10-11 — Round 71: Reddit Markdown-table readability.**
  The active Reddit V3 formatter now renders a detected Markdown table as
  compact, grouped row blocks — a plain label line (`Patch 3.7`) followed by
  one `- <column>: <value>` bullet per populated column, a blank line between
  rows, HTML entities decoded (`&amp;` → `&`), and a blank line before a
  `Q1:`-style FAQ question that follows text. This **supersedes the round-66
  rendering** (per-row `**bold-label**` bullets), which read as a wall of bold
  on mobile. Detection is unchanged: header row + a well-formed separator of
  the same width + a full run of data rows; malformed/glued tables and
  ordinary prose containing a pipe stay byte-identical, and nothing is
  date-converted (the card's 🕐 stays the only timestamp). The transform is
  local and linear in body length, runs at the single card-build choke point
  (RSS, FULL MODE, Arctic and proxy bodies all render identically), and adds
  no provider, proxy, media, cache, retry or Discord request; existing
  Components V2 text budgets still bound the output. Reddit media handling,
  provider fallback, cache behavior, continuation components, buttons and
  YouTube previews are unchanged, as is the round-67 no-content-decision
  policy. Review fix (PR #58): a following pipe line only counts as a table
  continuation when it has real table-row boundaries (leading/trailing `|`),
  so ordinary pipe prose (`Suoming | 5\* Electro Sword`) can no longer
  suppress formatting of the valid table above it — while mismatched
  boundary rows and glued tables still stay byte-identical. 16 new smoke
  guards (846/846; 96/96 signals). See
  [`docs/history/ROUND_71.md`](history/ROUND_71.md).

* **2026-10-11 — Round 70: bounded Twitter video media heal (4 attempts).**
  The default Twitter media-heal re-edit count rises from 2 to 4 for
  unresolved video tiles, hard-capped at 4 (`MEDIA_HEAL_ATTEMPTS`). The 45-second
  delay, immediate exit on resolved media, video-only scope, and 256 MiB
  preflight cap are unchanged. This does not add automatic 4K-to-lower-quality
  switching or cross-run healing. See
  [`docs/history/ROUND_70.md`](history/ROUND_70.md).

* **2026-10-08 — Round 69: Reddit provider-order docs + Arctic outage reasons.**
  The README and the Reddit V3 module comments now describe the live proxy
  priority/tie-break order (`vxreddit → redditez → Embeddit rewrite`), dispatched
  as bounded concurrent waves rather than a serial chain. The stale V3 header
  that said EmbedEZ was absent from the quality path is corrected: EmbedEZ is an
  optional, validated 1080p candidate. The Arctic Shift search diagnostic now
  logs the exception class name when `str(exception)` is empty
  (`Arctic Shift search unavailable: TimeoutError`). HTTP messages such as
  `HTTP 422` and descriptive exception text are unchanged. Offline smoke
  coverage was added for blank-exception Arctic failures. No provider order,
  request, retry, timeout, probe, cache, posting, scheduling, quality-selection,
  or image/GIF/gallery/non-video behavior changed. See
  [`docs/history/ROUND_69.md`](history/ROUND_69.md).

* **2026-10-08 — Round 68: Reddit video-quality fallback diagnostics (logging only).**
  The optional EmbedEZ quality path now logs `candidate=embedez` separately
  from the dynamically identified retained-base provider, with an explicit
  fallback reason when the candidate is unavailable or is not accepted as a
  superior validated result. It keeps the stable `retaining validated base`
  phrase used by the existing local workflow-summary counter. The retained
  base provider is labeled dynamically (`vxreddit`, `embedez` for
  EmbedEZ/RedditEZ, `embeddit`, `native-dash`, or conservatively `unknown`
  for unrecognized hosts). The accepted-upgrade message and
  candidate-selection logic are unchanged.
  No provider order, reliability fallback, request/probe, timeout, quality
  budget, cache, deduplication, posting, Discord payload, scheduling, retry,
  or image/GIF/gallery/non-video behavior changed. URL text is not quality
  evidence; unprobed dimensions/audio stay unverified/unknown. The summary
  remains local-log-only and its fallback-notice count is not a complete
  quality-decision count. See
  [`docs/REDDIT_VIDEO_QUALITY.md`](REDDIT_VIDEO_QUALITY.md) and
  [`docs/history/ROUND_68.md`](history/ROUND_68.md).

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
  all. The module header of `testing area/reddit_proxy.py` was also
  corrected (comment-only) to describe the round-49 wave dispatch and the
  vxreddit-first tie-break accurately, and the confirmed acceptance policy
  is committed as `docs/VIDEO_ONLY_QUALITY_POLICY_CONFIRMATION.md`.
  Evidence and the manual canary checklist:
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
