# AGENTS.md — onboarding for AI coding agents

## Fast, exact incremental PR updates

- Continue the specified existing PR; implement only the newest requested delta.
- Use concise unified diffs: `-` removes old code, `+` adds replacement code.
  Do not replay full historical patches or add unrelated cleanup/new files.
- Reuse relevant prior evidence. Inspect affected code and run targeted checks;
  do not repeat a full audit/benchmark unless drift, failures or risk justify it.
- Let normal CI validate the resulting head. Inspect advisory findings too;
  never hide/suppress failures or remove safeguards to save time.
- Update existing AGENTS/README/docs/changelog/privacy/terms only where affected.
- Write an accurate PR title/body; report head, changes, checks and blockers briefly.
- No extra audit MD, production posting, state reset or merge without approval.

## Media recovery and workflow summaries

Keep crosspost recovery one-hop and provenance-validated; preserve child identity,
Read Post destination, gallery order and existing quality/audio checks. Reuse
completed archive lookups, including misses/errors, and validated embedded parents.
Reporting stays in the existing monitor summary steps, not engine wrappers or a
new module. Treat counts as log observations; missing measurements are unavailable.
Do not add reporting HTTP calls, reset dedup state or replay repaired messages.

Read this first. It encodes the hard-won operational knowledge of 76 rounds
of production fixes so you do not re-learn it the expensive way — or
"fix" something that is deliberate.

## What this repository is

Discord news bots: a **Reddit monitor** (leak subreddits) and a **Twitter/X
monitor** (game accounts) that post rich Components-V2 cards to Discord
webhooks. They run as GitHub Actions workflows triggered every few minutes
by an external cron (cron-job.org) via `workflow_dispatch`.

## The three-repo architecture (critical — get this wrong and nothing works)

| Repo | Role |
|---|---|
| `uesu/News-Express` (this repo, private) | The MAIN repo — development only. Nothing runs live from here; it exists to receive development updates (rounds, docs, tests) as PRs. |
| `uesu/7jkxmy9nvbc` (public) | **Reddit production.** Runs `reddit_monitor.yml` live. |
| `uesu/wvkhabh2s22` (public) | **Twitter production.** Runs `twitter_monitor.yml` live. |

Deployment is **manual**: merge a PR here, then the maintainer uploads the
production-relevant files to the prod repo(s) through the GitHub web UI. Agents
work on their session branch: open the PR from it when the platform lets you
push, otherwise deliver local commits and the maintainer opens the PR. Typical
upload set per fix: the engine file + `tests/test_smoke.py` + the touched
workflow yml, **engine file first** (a guard that lands before its engine turns
the prod smoke check red — the round-75 deploy lesson). Do **not** copy this
repository's development documentation, historical audit records, or agent
onboarding files into production unless a task explicitly asks for that.

Both prod repos intentionally contain BOTH monitors' files. They are NOT
leftovers. Never advise deleting the "other" platform's files.

## File map

- `testing area/reddit_main_v3.py` — LIVE Reddit engine (gates, cards, caches).
- `testing area/twitter_v3.py` — LIVE Twitter engine (cards, media heal).
- `testing area/reddit_signals.py` — pure decision logic (gates, tombstones).
- `testing area/reddit_proxy.py`, `twitter_proxy.py` — proxy-service parsers.
- `testing area/*_v1.py`, `*_v2*.py`, `video_diag.py` — maintained fallback
  engines, switchable via one commented line in the workflows. NOT dead code.
- `tests/test_smoke.py` — the main suite; every past bug is a named guard
  (`rNN: ...`). `tests/test_reddit_signals.py` — gate-logic suite.
  `tests/test_twitter_media.py` — focused X media suite (canonical media
  order, GIF converter chain + content types, mp4-vs-AVIF priority, the
  media-heal contract).
- `docs/` — current changelog + topic guides: `CHANGELOG.md` (current release
  notes, round 63 onward), `CI_SMOKE.md`, `DEPENDABOT.md`, `DISCOHOOK.md`,
  `PYTHON_RUNTIME.md`, `REPOSITORY_TRACKING.md` (per-monitor Variable
  inventory + run-summary notes), and the round-67 video-quality trio
  (`REDDIT_VIDEO_QUALITY.md`, `REDDIT_VIDEO_MEDIA_REPORT.md`,
  `VIDEO_ONLY_QUALITY_POLICY_CONFIRMATION.md`). For the live
  secrets-vs-Variables inventory read `.env.example` and the workflow `env:`
  blocks.
- `docs/history/` — the history archive: `ROUND_*.md` decision records per
  incident, `CHANGELOG_ARCHIVE.md` (full dated history, rounds 1–62),
  `ENGINE_HISTORY.md` (detailed round notes moved out of the README on
  2026-10-05) and `REPOSITORY_TRACKING_2026-10-01.md` (pre-round-63 audit
  snapshot). Read the round doc before touching its area.

## How to test (ALWAYS before committing)

```bash
python3 tests/test_smoke.py           # expect: SMOKE TEST: ALL PASS
python3 tests/test_reddit_signals.py  # expect: ALL PASS
python3 tests/test_twitter_media.py   # expect: TWITTER MEDIA TEST: ALL PASS
```

Counts differ slightly between this repo and prod checkouts (path-dependent
checks) — "ALL PASS" is the contract, not the number. The suites stub
`aiohttp`/`feedparser`/`dotenv` in `sys.modules`, so no pip installs are
needed. If you must import an engine standalone, copy the stubbing pattern
from the top of `test_smoke.py`.

Convention: every behavioral fix gets (1) a `docs/history/ROUND_NN.md` decision
record, (2) a `docs/CHANGELOG.md` entry, (3) named smoke guards (`rNN: ...`).

## Invariants — NEVER violate these

1. **The monitor makes no content-based posting decision.** Round 67 removed
   the content-advisory gate entirely (engine, Variables, tests, docs) at the
   maintainer's request: do not reintroduce any content classification,
   allowlist, fail-open/fail-closed logic or "unknown metadata" hold for it.
   Current delivery still includes dedup, the stateless fresh-age and pristine
   listing checks, plus operational liveness/media-readiness checks. Some
   operational holds are recorded in `pending_reddit.json` and rechecked
   according to `PENDING_RECHECK_SECONDS` (default 1800 s); the two round-64
   stateless checks do not write pending entries. The truthful record of
   content-gate removal is `docs/history/ROUND_67.md`.
2. **Gates never guess.** Every hold/skip requires exact, provable evidence
   (same URL, same author+title, removal notice on the post's own page).
   Fuzzy/similarity matching has been explicitly rejected (see round 56/57
   era discussions and ROUND_43 scope).
3. **Every env Variable must be explicitly wired** into the workflow yml
   `env:` block, or prod silently ignores it (guard tests enforce this —
   the round-42 pattern).
4. **Variables must be empty-string-safe.** GHA passes unset Variables as
   `""`. Pattern: `(os.getenv(X) or "default")...` or a normalizer function
   with a safe fallback (see `media_heal_scope()` in `twitter_v3.py`).
5. **`concurrency: cancel-in-progress: false` must stay false** in the
   monitor workflows (P0 double-post fix, 2026-09-19). Cancelling a run
   between "Discord posted" and "cache committed" causes re-posts.
6. **cron-job.org is the single scheduler.** GitHub's native `schedule:` is
   disabled on purpose (it raced the external cron → double posts).
7. **Actions stay SHA-pinned** (round 57); jobs keep `timeout-minutes`.
8. Heal eligibility is classified by **URL**, never by response
   `content_type` (it is empty exactly when unresolved — round 56).
   `heal_eligible_items` reads module-global `MEDIA_HEAL_SCOPE` at call
   time (tests monkeypatch it).
9. **The X RSS fleet (`RSS_INSTANCES` in `twitter_v3.py`) is a serial chain
   ranked by runner evidence.** Seats 1–2 are the operator pair (`nitter.cf`,
   `xitter.cf`, round 40) — never move or remove them without operator
   sign-off. Round-76 ranking rule: **no instance that blocks GitHub Actions /
   Azure datacenter IPs (or datacenter IPs generally) may sit above one that
   doesn't.** A clean feed body read off-runner is a trial ticket, never
   proof — the verdict comes from the GitHub Actions runners (Game-Express,
   the sister monitor on the same runners, usually measures it first).
   Members are demoted, not deleted (a blocked host moves back up the day it
   answers the runners). The smoke suite pins the exact order, so every
   re-rank updates the guard in the same commit; V1/V2 keep their own,
   separately pinned lists. Reddit's `REDDIT_RSS_INSTANCES` is audited by
   body too and has been intentionally unchanged since round 39.

## Landmines — things that LOOK like bugs but are deliberate

- X "GIFs" are `video.twimg.com/tweet_video/*.mp4` → heal-eligible as
  videos. Converted `.gif`/`.webp` image files are excluded. By design.
- (historical — gate removed in round 63) Re-uploaded Reddit media gets NEW
  `i.redd.it` URLs, so the former duplicate-media gate was never allowed to
  catch cross-author re-uploads. Do not reintroduce any media-fingerprint
  gate — invariant 2: same URL = provable, new URL = guesswork.
- Benign log lines (do NOT "fix"): `dedup cache near cap` (eviction
  handles it), the OAuth-skip INFO line, `redlib gallery enrichment failed`
  (fallback works). (The `MODQUEUE-LISTING ... fail open` line was removed
  with the mod-queue gate in round 63 — if you see it in old logs only.)
- Long Reddit bodies deliver as the main card + up to 3 text-only
  continuation messages ("-# (continued)" heading). Gallery, stats and
  buttons live ONLY on the main card, and every split lands outside
  links/URLs/spoilers — by design (round 66, live 1wxfuj5). Do not
  "fix" continuations into the card or move media between parts.
- The engine versions v1/v2 are documented fallbacks, enrolled in the
  smoke suite. Not stale code.
- Blocked or walled nitter hosts at the bottom of `RSS_INSTANCES` (kareem,
  xcopy, netbub, jaydenha…) are deliberate: demoted, not deleted (invariant
  9). A 403 is a fast fail in the serial chain; deleting a member loses the
  revival path and the ledger that justifies the ranking.

## Key defaults (all overridable via repo Variables, no code change)

- `FRESH_HOLD_SECONDS=30` — flat minimum post age before a candidate is
  considered (round 64); `LISTING_CONFIRM` (default on) requires a pristine
  /new listing read before posting. These two checks are stateless.
- `PENDING_RECHECK_SECONDS=1800` — active throttle for retryable operational
  holds tracked in `pending_reddit.json`; confirmed removed/deleted archive
  entries use a no-recheck path unless they reappear via RSS. Distinct from
  the stateless age/listing checks.
- `MEDIA_HEAL_SCOPE` — `video` (default) | `on`/`all` | `off` (round 56/56b).
- `RETRACT_DEAD_POSTS` — default OFF; `1` enables dead-post tombstoning
  (round 44; requires two independent proofs before touching a message).
  (Round 66 removed the workflow mappings for the round-42-45 gate Variables
  — settle windows, dup-media/repost/mod-queue gates, listing racing — that
  round 63 had already deleted from the engine; round 67 removed the four
  content-advisory Variables along with the gate itself.)
- `REDDIT_VIDEO_QUALITY` — `balanced` (default) | `compatibility` | `highest`
  (round 67). `compatibility` restores the pre-round-67 video ladder exactly,
  so it is the zero-code rollback for the quality-aware resolver. The
  resolver's budgets (window / candidate / per-post / per-run) are constants
  in the engine, deliberately not Variables.

## Writing conventions

- Refer to the Embeddit rewrite neutrally as "the Embeddit rewrite";
  do not link external PRs of other people's repos in PR bodies or docs.
- Latest rounds at the top of `docs/CHANGELOG.md`.
- When a round intentionally changes behavior that an older guard test
  pins, update the guard IN THE SAME commit and annotate why in place
  (e.g. "r52 guard updated in round 66: ...") — never silently delete or
  weaken a guard.
- Verify repository CONTENT, not git history — the agent-platform
  workspace flattens local history between sessions.
