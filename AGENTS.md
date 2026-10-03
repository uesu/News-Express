# AGENTS.md — onboarding for AI coding agents

Read this first. It encodes the hard-won operational knowledge of 58 rounds
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
| `uesu/News-Express` (this repo, private) | Development. All fixes happen HERE via PR. |
| `uesu/7jkxmy9nvbc` (public) | **Reddit production.** Runs `reddit_monitor.yml` live. |
| `uesu/wvkhabh2s22` (public) | **Twitter production.** Runs `twitter_monitor.yml` live. |

Deployment is **manual**: merge a PR here, then the maintainer uploads the
changed files to the prod repo(s) through the GitHub web UI. Agents usually
cannot push anywhere — deliver work as local commits on the session branch;
the maintainer opens the PR. Typical upload set per fix: the engine file +
`tests/test_smoke.py` + the touched workflow yml.

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
- `docs/ROUND_*.md` — decision records per incident. README `## 🗒 Changelog`
  — the full dated history. Read the round doc before touching its area.

## How to test (ALWAYS before committing)

```bash
python3 tests/test_smoke.py           # expect: SMOKE TEST: ALL PASS
python3 tests/test_reddit_signals.py  # expect: ALL PASS
```

Counts differ slightly between this repo and prod checkouts (path-dependent
checks) — "ALL PASS" is the contract, not the number. The suites stub
`aiohttp`/`feedparser`/`dotenv` in `sys.modules`, so no pip installs are
needed. If you must import an engine standalone, copy the stubbing pattern
from the top of `test_smoke.py`.

Convention: every behavioral fix gets (1) a `docs/ROUND_NN.md` decision
record, (2) a README changelog entry, (3) named smoke guards (`rNN: ...`).

## Invariants — NEVER violate these

1. **The NSFW gate is never removed or weakened.** Non-negotiable.
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
8. Mod-queue page evidence must render THIS post: any fixture fed to
   `mod_queue_reason` as a "real page" must contain the post's own
   `/comments/<id>/` marker (round 55).
9. Heal eligibility is classified by **URL**, never by response
   `content_type` (it is empty exactly when unresolved — round 56).
   `heal_eligible_items` reads module-global `MEDIA_HEAL_SCOPE` at call
   time (tests monkeypatch it).

## Landmines — things that LOOK like bugs but are deliberate

- X "GIFs" are `video.twimg.com/tweet_video/*.mp4` → heal-eligible as
  videos. Converted `.gif`/`.webp` image files are excluded. By design.
- Re-uploaded Reddit media gets NEW `i.redd.it` URLs → the duplicate-media
  gate cannot and should not catch cross-author re-uploads. By design
  (invariant 2): same URL = provable, new URL = guesswork.
- Benign log lines (do NOT "fix"): `dedup cache near cap` (eviction
  handles it), the OAuth-skip INFO line, `redlib gallery enrichment failed`
  (fallback works), `MODQUEUE-LISTING ... fail open` (by design when all
  listing sources are down).
- The engine versions v1/v2 are documented fallbacks, enrolled in the
  smoke suite. Not stale code.

## Key defaults (all overridable via repo Variables, no code change)

- `POST_SETTLE_SECONDS=300` (unverified) / `POST_SETTLE_VERIFIED_SECONDS=60`
- `DUP_MEDIA_GATE`, `REPOST_GATE`, `MOD_QUEUE_GATE` — default ON; empty
  Variable = ON (only explicit off-values disable).
- `MEDIA_HEAL_SCOPE` — `video` (default) | `on`/`all` | `off` (round 56/56b).
- `RETRACT_DEAD_POSTS` — default OFF; `1` enables dead-post tombstoning
  (round 44; requires two independent proofs before touching a message).

## Writing conventions

- Refer to the Embeddit rewrite neutrally as "the Embeddit rewrite";
  do not link external PRs of other people's repos in PR bodies or docs.
- Latest rounds at the top of the README changelog.
- Verify repository CONTENT, not git history — the agent-platform
  workspace flattens local history between sessions.
