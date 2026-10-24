# Round 87 (2026-10-24) — Automated Dev → Prod Repository Sync (`sync_prod.yml` + `sync_prod.py`)

## Summary

Adds automated, test-gated GitHub Actions synchronization from `uesu/News-Express` (development) to both live production repositories (`uesu/7jkxmy9nvbc` for Reddit and `uesu/wvkhabh2s22` for Twitter/X) whenever changes land on `main` or via manual `workflow_dispatch`.

## Problem

Previously, deploying changes from `uesu/News-Express` required manually uploading modified files through the GitHub web UI to both `uesu/7jkxmy9nvbc` and `uesu/wvkhabh2s22` one file at a time. Aside from manual toil across two mirror repositories, single-file web-UI uploads created a timing window (documented in Round 75) where uploading `tests/test_smoke.py` before `testing area/reddit_main_v3.py` triggered a transient red CI run on the production repository.

## Solution

1. **`.github/scripts/sync_prod.py`:**
   - Synchronizes the production runtime subset (`testing area/`, `tests/`, `.github/scripts/`, `.github/workflows/{ci,dependabot_auto_merge,python_version_bump,reddit_monitor,twitter_monitor}.yml`, `.github/dependabot.yml`, `.gitignore`, `requirements.txt`) into each target repository (`uesu/7jkxmy9nvbc`, `uesu/wvkhabh2s22`) and commits all changes atomically in a single Git commit.
   - **Live cache protection:** Never creates, overwrites, stages, or deletes `posted_reddit.json`, `pending_reddit.json`, `proxy_health.json`, `posted_tweets.json`, or `posted_messages.json` (enforced both in `sync_tree()` with byte-for-byte pre/post verification and in `_stage_and_verify()` via `git reset` / `git checkout`).
   - **Dev-only exclusion:** Never copies `docs/`, `README.md`, `AGENTS.md`, `.env.example`, or `.github/workflows/sync_prod.yml` into the production repositories.
   - **Concurrent monitor cache push resilience:** If a 5-minute `reddit_monitor.yml` or `twitter_monitor.yml` cache commit lands while a sync push is in flight, `sync_remote_repo()` fetches `origin/main`, resets to `FETCH_HEAD`, and re-applies `sync_tree()` on top of the freshly committed caches.
   - **Workflow-scope fallback:** If `.github/workflows/*` changed and the token (`secrets.PROD_SYNC_PAT || secrets.BUMP_PAT`) lacks `workflow` scope, automatically retries without workflow files so engine/test updates still deploy immediately while emitting a clear warning.

2. **`.github/workflows/sync_prod.yml`:**
   - Triggers on `push` to `main` and `workflow_dispatch` (`target_repos`, `dry_run`, `skip_ci` inputs).
   - Guards execution with `if: github.repository == 'uesu/News-Express'` and `concurrency: cancel-in-progress: false`.
   - Runs `compileall`, `tests/test_smoke.py`, `tests/test_reddit_signals.py`, and `tests/test_twitter_media.py` before executing `python .github/scripts/sync_prod.py`.
