# Shared file manifest — News-Express development vs production copies

This is a **development-side** review document. It is not a runtime input.
`production_copy_exclude` lists `docs/`, so production copies must not require
this file. Correction handoffs and `NEWS_EXPRESS_UPDATE.md` are development-side
only and must not become required runtime inputs.

The machine-readable lists live in `.github/maintenance.json`:

* `runtime_files` — files a documentation-free production copy still needs
* `production_copy_exclude` — docs, onboarding, and **caches that must never
  be overwritten**
* `optional_docs` — present in this development tree; omitted in production

Copying to `uesu/7jkxmy9nvbc` / `uesu/wvkhabh2s22` is maintainer-only and later.
Do not blindly copy either production variant back into development.

## Exact heads reviewed 2026-10-16 (Asia/Manila)

| Role | Repository | Head SHA | Note |
|---|---|---|---|
| Development (this PR) | `uesu/News-Express` `arena/51e180af-news-express` | see git HEAD of this branch | PR #66 OPEN, unmerged |
| Reddit production | `uesu/7jkxmy9nvbc` `main` | `3691cc88b2ef446bcc11b25ad6360309aa63a68d` | last commit: auto cache update 2026-10-15 |
| Twitter production | `uesu/wvkhabh2s22` `main` | `58547a93c8668b005a5bce7d583ee52e6520580c` | last commit: auto cache update 2026-10-16 |
| Game (not a News copy) | `uesu/Game-Express` `main` | `e8588ac01dc5102bd221a556d04bb0593b1db984` | independent application |
| Game PR #49 helpers | `uesu/Game-Express` | `5837ce4c9eef9ad80bb1d2b8c154652b1836d1de` | helper blobs differ from News |

These three News-family heads are **not equivalent copies**. Green development
checks do **not** prove that production already contains these repairs.

## Must remain in every production copy

Both **engines** and **both monitor workflows** stay present in each production
copy even when that copy only posts one network. Shared helpers
(`maintenance.py`, `ci.py`, `python_version_bump.py`, `render_run_summary.py`),
hashed runtime + constrained development locks, and `.python-version` go with
them.

## Must not be copied onto production caches or required at runtime

* Dedup / pending / health JSON listed in `production_copy_exclude`
* README, AGENTS, PRIVACY/TERMS, and `docs/`
* Correction handoffs and `NEWS_EXPRESS_UPDATE.md`

## Reviewed difference list (blob comparison, 2026-10-16)

**Identical on both production copies, and matching this development tree**
(authorized to leave as-is until a later copy): `testing area/twitter_proxy.py`,
`testing area/reddit_signals.py`, `testing area/reddit_main.py`,
`testing area/reddit_main_v2_embedez.py`, `testing area/twitter_v1.py`,
`testing area/twitter_v2_button_outside.py`, `testing area/video_diag.py`,
`tests/fixtures/posted_cards.py`, `.github/scripts/merge_monitor_caches.py`.

**Identical on both production copies, different from this development tree**
(not yet copied; **not** authorized production behavior differences):

* `testing area/reddit_main_v3.py`, `testing area/twitter_v3.py`,
  `testing area/reddit_proxy.py`
* `.github/workflows/ci.yml`, `reddit_monitor.yml`, `twitter_monitor.yml`,
  `python_version_bump.yml`, `.github/dependabot.yml`
* `tests/test_smoke.py`, `tests/test_twitter_media.py`,
  `tests/test_reddit_signals.py`
* `requirements.txt` — production is a 65-byte unhashed range file
  (`feedparser`/`aiohttp`/`python-dotenv` lower bounds). Development is the
  3.14.8 hashed lock (12 packages / 752 hashes). Do not copy the unhashed
  production file back into development.

**Missing on both production copies, present here as `runtime_files`**
(required for documentation-free production once copied; **not** present today):
`.python-version`, `requirements.in`, `requirements-dev.in`,
`requirements-dev.txt`, `.github/maintenance.json`,
`.github/scripts/maintenance.py`, `python_version_bump.py`, `ci.py`,
`render_run_summary.py`, `.github/workflows/maintenance_merge.yml`,
`testing area/run_report.py`, `tests/test_maintenance.py`,
`tests/test_run_summary.py`, `tests/test_configuration_contract.py`,
`tests/test_crosspost_video.py`.

**Present on production, absent here (do not copy back):**
`.github/workflows/dependabot_auto_merge.yml` — legacy self-merge path. This
development tree retired it in favor of `maintenance_merge.yml`.

**Authorized production differences:** omitted documentation (`docs/`, README,
AGENTS, PRIVACY/TERMS), independent caches (`posted_reddit.json`,
`posted_tweets.json`, `pending_reddit.json`, `proxy_health.json`), and
repository-identity / webhook configuration. Cache files differ between the
two production copies by design; never overwrite them.

**Justified `.env.example` / `.gitignore` drift:** production copies omit
development-only report ignores and some later env examples. Unrelated posting
behavior is not an authorized difference.

## Game helper disposition (not byte-identical)

Game-Express shares helper *semantics* via identical helpers + a project
profile. The applications stay independent; do not force either runtime layout
onto the other.

At the heads above, the helpers are **materially different**:

| File | News PR #66 blob | Game PR #49 blob |
|---|---|---|
| `.github/scripts/maintenance.py` | `64ce7258f279…` (66 524 bytes) | `d8d69edf9b56…` (180 887 bytes) |
| `.github/scripts/ci.py` | `80e3e29191d7…` | `26d50f9eeca8…` |
| `.github/scripts/python_version_bump.py` | `cd90014f1520…` | `3148b1bcf05f…` |
| `.github/scripts/render_run_summary.py` | `ec5c73aa9a3a…` | `e0623e71876d…` |
| `.python-version` | `9b8fe2fbb856` (`3.14.8`) | same pin blob |

**Convergence plan:** keep News helpers on this PR. Do not overwrite them with
Game's files or vice versa. After both implementation PRs are accepted, a
separate shared-maintenance task can reconcile helper bytes against the master
spec. Until then, do **not** claim the helpers are identical.

Game `main` currently lacks `maintenance.py` / `ci.py` / `render_run_summary.py`
entirely (helpers live on PR #49). That is Game's copy state, not a News defect.

## Current review limitation

This inventory is an exact-head **difference list**, not a completed
content/parity review and not proof that production contains News's fixes.
Production copies do not inherit repairs automatically.
