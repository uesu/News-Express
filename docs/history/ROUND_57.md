# Round 57 — Workflow hardening: SHA-pinned actions + hung-run caps

**Date:** 2026-10-03
**Scope:** `.github/workflows/*.yml` + guard checks in `tests/test_smoke.py`.
**Engine code:** untouched — zero behavior change for posting, gating or healing.

## Why

A review against the 2026 GitHub Actions hardening checklists found the
repository already implements most controls (single-scheduler cron, P0
concurrency double-post guard, least-privilege `permissions:`, exact CPython
pin, pip caching, Dependabot for pip **and** actions, dispatch inputs passed
via env). Two gaps remained.

## 57a — Pin every action to an immutable commit SHA

A version tag like `@v7` is a movable pointer: whoever controls the action
repo (or compromises it) can repoint the tag and every consumer runs the new
code on its next trigger. This is exactly how the March 2025
`tj-actions/changed-files` compromise (CVE-2025-30066) spread — tags v1
through v45 were repointed to a malicious commit within a day.

Every `uses:` is now pinned to its 40-hex commit SHA with the tag kept as a
comment:

| Action | Pinned SHA | Tag |
|---|---|---|
| `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | v7 |
| `actions/setup-python` | `5fda3b95a4ea91299a34e894583c3862153e4b97` | v7 |
| `actions/github-script` | `3a2844b7e9c422d3c10d287c895573f7108da1b3` | v9 |

The checkout/setup-python SHAs were taken from the production run logs
(what GitHub itself resolved for `@v7`); github-script's from the GitHub
API tag dereference. Dependabot's `github-actions` ecosystem updates pinned
SHAs through reviewed PRs, so pinning does not mean going stale.

## 57b — `timeout-minutes` on every job

No job declared a timeout, so a single hung network call could hold a run
for GitHub's **6-hour** default. Because the P0 concurrency guard
intentionally queues (never cancels) subsequent triggers, one hung run
would silence the monitor for up to 6 hours. Caps added:

| Workflow | Cap | Rationale |
|---|---|---|
| reddit_monitor / twitter_monitor | 15 min | worst legitimate run (backlog + heal delays + cache-push retries) stays well under 10 |
| ci | 15 min | suites finish in ~2 min |
| python_version_bump | 30 min | full validation gate |
| dependabot_auto_merge | 5 min | single API script |

A timed-out monitor run simply ends; the next cron tick starts clean on the
newest cache commit — the same recovery path as any failed run.

## Guard tests (round 57 block, tests/test_smoke.py)

For both monitor workflows: every `uses:` matches `@[0-9a-f]{40}` (no
mutable tags), `timeout-minutes` is declared, and the P0 concurrency guard
(`concurrency:` + `cancel-in-progress: false`) is still present.

## Considered and NOT adopted

* **uv (Astral) instead of pip** — the install step already runs ~4-5 s on
  a warm pip cache; uv would save ~3 s/run at the cost of a new third-party
  action in the supply chain. Not worth it for these workloads.
* **OIDC, harden-runner, SBOM gates** — aimed at cloud-credential and
  artifact-publishing pipelines; this repo has neither.
* **Exact-pinning requirements.txt (`==`)** — optional; floating `>=` plus
  weekly Dependabot PRs is the current, deliberate trade-off.
