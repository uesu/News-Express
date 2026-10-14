# 🤖 Dependabot — dependency automation and runtime-boundary policy

> **TL;DR:** Dependabot is a **free, built-in GitHub feature** that watches
> `requirements.txt` and GitHub Actions references and opens dependency/action
> pull requests when the configured ranges or action pins need an update. It
> does **not** manage the CPython `python-version` runtime pin. Dependabot never
> pushes directly to `main`; merges require either human review or the separate
> opt-in, CI-gated auto-merge workflow. It is optional: the monitor can run
> without Dependabot, but dependency update review loses its automated PR path.

---

## 1. What is it?

Dependabot is **not** a bot you host, install, or pay for. It is a service
**built into GitHub** that runs on GitHub's own infrastructure:

1. **Scans** your repository's dependency files — here that means
   `requirements.txt` (pip) and the `uses: actions/...@v7` lines in
   `.github/workflows/*.yml` (GitHub Actions).
2. **Watches** the package registries (PyPI, the GitHub Actions marketplace)
   for new versions and published security advisories.
3. When a configured requirement needs to change, or a vulnerability fix needs
   a tighter lower bound, it **opens a pull request** from `dependabot[bot]`
   with the bump plus a summary and upstream links. This repository groups pip
   dependency updates together and groups GitHub Actions updates together to
   reduce PR noise.

That's the whole loop: **scan → open PR → you decide.**

## 2. Is it optional or not?

**Completely optional.** Concretely:

| Question | Answer |
|---|---|
| Does the monitor need Dependabot to run? | **No.** Zero. The cron jobs run exactly as before. |
| Does it cost money? | **No.** Free on every GitHub plan, public *and* private repos. |
| Does it need a token/API key? | **No.** It's native to GitHub. |
| Can I turn it off? | **Yes** — delete `.github/dependabot.yml` (one file) and no more update PRs appear. Security alerts can be switched off separately in Settings → Security. |
| Will it start posting to my Discord channels? | **No.** It only opens GitHub PRs. |

Think of it as a very polite roommate: it notices the milk is expiring,
leaves a note on your fridge (a PR), and waits for you to say "buy new
milk" (merge).

## 3. What exactly does it do — step by step

With the config in this repo (`.github/dependabot.yml`):

* **Every week** (schedule: `interval: weekly`), Dependabot checks:
  * **pip**: `requirements.txt` → `feedparser`, `aiohttp`, `python-dotenv`
  * **github-actions**: every workflow's `actions/checkout@v7`,
    `actions/setup-python@v7`, … (the old v4/v5 pins were auto-bumped to
    v7 by Dependabot itself — see the Node 20→24 FAQ below)
* For pip, `versioning-strategy: increase-if-necessary` means ordinary releases
  already allowed by the ranges (for example an `aiohttp` 3.x release below
  `<4`) do not create noisy PRs; the workflows install the newest allowed
  versions on each run. Dependabot opens a PR when the requirement itself must
  change, such as a security lower-bound update or a release outside the
  current range.
* For GitHub Actions, pinned action references are checked weekly and grouped
  into a single `github-actions` PR when updates are available.
* Security-update PRs are opened whenever a published vulnerability affects the
  configured dependency requirement.
* If a PR is left open and a newer applicable version lands, Dependabot updates
  the same PR instead of opening a duplicate. If a PR is closed unmerged, it
  stops re-opening that exact bump.

**What it will NOT do:** run your monitor scripts, post to Discord, change
application code, change the workflow `python-version` input, push directly to
`main`, or merge anything unless you enable the separate opt-in auto-merge gate.
It does not consume Actions minutes for creating the PR itself (public repos:
free; private repos: the CI checks use normal Actions minutes).

## 3a. Does Dependabot auto-bump Python itself?

**No.** Dependabot manages pip package manifests and `uses:` Action versions;
`python-version: '3.14.8'` is a workflow setting, not a Dependabot ecosystem.
That is intentional: floating `3.14` would silently take a newly released patch
into a live posting run without a dedicated PR or a pre-merge runtime test.

The repository uses an exact CPython pin and changes it through
`.github/workflows/python_version_bump.yml`, not Dependabot. The runtime policy
is:

* patch updates within the current series may be automatically proposed and,
  when all validation passes, auto-merged only if `AUTO_MERGE_PYTHON_BUMP=yes`;
* a new minor series such as Python 3.15 requires a PR and manual review;
* a major version such as Python 4 requires deliberate manual migration; and
* `AUTO_MERGE_PYTHON_BUMP` has no `all` mode.

See [Python runtime policy](PYTHON_RUNTIME.md) for the current official version
assessment, wheel-only validation, soak period, rewrite allowlist, and rollback
procedure.

## 4. How do I know it won't break anything? (the safety chain)

Three layers, in order:

1. **Nothing merges until you merge.** A Dependabot PR is just a branch.
   Your `main` and your live monitor are untouched until you click *Merge*
   (or auto-merge is enabled and green — see §5).
2. **CI gate (shipped in this repo — `.github/workflows/ci.yml`).** Every PR,
   including Dependabot's, runs:
   * `pip install -r requirements.txt` — a broken/renamed package fails
     **here**, before it can reach your production workflow;
   * `python -m compileall -q "testing area" tests` — syntax errors fail here;
   * `python tests/test_smoke.py` — offline monitor import and card-pipeline
     guards;
   * `python tests/test_reddit_signals.py` — pure Reddit gate/decision guards;
   * `python tests/test_twitter_media.py` — pure X (Twitter) V3 media guards.
   Red check = don't merge. For a routine dependency PR, green checks plus a
   minimal dependency/action diff are the required merge gate; live external
   services remain outside CI.
3. **Revert is one click.** If a merged bump ever misbehaves (rare for these
   three stable libraries), GitHub's *Revert* button on the merge commit
   undoes it in seconds; the next Dependabot run will simply try a different
   version later.

**Extra-cautious option** (optional, matches this repo's normal update
process): after merging a bump, trigger the Reddit workflow once with
`dry_run: yes` (or a `test_post`) and skim the log — the card payloads get
logged without touching Discord. Then do one real test-channel run if you
want the full confidence. For routine dependency patch bumps, the green check
is usually the repository's offline gate; it is not a live-service proof.

## 5. Making it fully automatic (PR **and** merge to main) — opt-in

Out of the box, Dependabot stops at the PR (recommended default). If you
want **automatic merge to main once checks are green**, pick ONE of:

### Option A — GitHub's built-in auto-merge (simplest)

1. Repo → **Settings → General → Pull requests** → enable **Auto-merge
   pull requests**.
2. On any green Dependabot PR, click **Enable auto-merge** → GitHub merges
   the moment checks pass (it also waits out required reviews if you have
   any). You can scope it in the same place.

### Option B — the bundled auto-merge workflow (already in the repo)

`.github/workflows/dependabot_auto_merge.yml` is included but **disabled**
until the repository variable below is set. It uses the trusted
`pull_request_target` trigger for `opened`, `synchronize`, and `reopened` PR
events. GitHub reads that workflow file from the default branch; the job does
**not** check out the PR and does **not** execute any PR-supplied code.

To turn it on, create this one repository variable (it is a switch, not a
credential):

* Repo → **Settings → Secrets and variables → Actions → Variables**
  → *New repository variable* → name **`AUTO_MERGE_DEPENDABOT`** = **`yes`**

The PR event can arrive before CI has created or finished its check run. To
avoid that race, the workflow captures the event's head SHA and polls **only
that immutable SHA** every 15 seconds for up to eight minutes. It never uses a
mutable branch name. No checks, pending checks, unknown mergeability, an API
error, a changed head SHA, an unexpected target, or a timeout all fail closed:
the workflow logs the reason and does not merge. After checks are ready it
refreshes the PR and checks once more immediately before calling the merge API;
the merge request also includes that exact SHA, so GitHub rejects a late head
change.

| Gate | Check |
|---|---|
| 0 | variable `AUTO_MERGE_DEPENDABOT` is exactly `yes` |
| 1 | trusted PR event and API response agree on one PR, its default-branch target, and its exact event head SHA |
| 2 | API reports author `dependabot[bot]`, state `open`, and `draft=false` — human, closed, and draft PRs are skipped |
| 3 | **at least one** Check Run exists for that exact SHA; pending or absent checks are polled, and every completed Check Run must conclude `success`, `skipped`, or `neutral` |
| 4 | the refreshed PR is cleanly mergeable; conflicts and unknown/non-clean mergeability are never merged |
| 5 | checks are read again on the same SHA, then GitHub is asked to **squash-merge** with that SHA as a final race guard |

The workflow has only `checks: read`, `contents: write`, and
`pull-requests: write` permissions. It has no checkout step and every action
reference is pinned to a full commit SHA. Its log names the material outcome:
variable disabled, non-Dependabot author, draft or closed PR, merge conflict,
checks pending, failed check, no checks, timeout, or successful merge.

To disable it again, set the variable to anything other than `yes` (or delete
it). GitHub's separate repository-level **Allow auto-merge** setting is not
required for this option: this workflow performs the guarded squash merge via
the GitHub API.

**Why keep the check requirement?** Because "Dependabot said so" is not a
test. The CI job is cheap (~30 s) and is what actually proves the new version
still installs and compiles.

## 6. Cost & limits (the fine print)

* **Free** on all plans, public and private. No subscription, no per-PR fee.
* **Public repo:** every Dependabot feature (alerts, security updates,
  version updates, the check runs) is free and does **not** consume your
  Actions minutes.
* **Private repo:** included with your plan; the PR check runs count against
  your normal monthly Actions minutes (a few seconds — negligible here).
* **Monitoring limits:** public repos — unlimited dependencies. Private repos
  — 10 per repo on Free, 100 on Pro/Team. This repo monitors a small set of
  pip requirements plus the GitHub Actions referenced in the workflows, so it
  fits comfortably within those limits.

## 7. Recommended review routine (60 seconds per PR)

1. Open the Dependabot PR.
2. Read the diff — for pip it should normally be a requirement-bound change,
   and for actions it should be action references only. Anything bigger? Read
   the changelog link; for a **major** dependency version (e.g. 3.x → 4.0) skim
   the migration notes.
3. Check the **CI** tab: green ✅ (install + compile + smoke + Reddit signals + X media).
4. **Merge** (or enable auto-merge per §5). Done — the next scheduled
   monitor run uses the new version automatically.

For **security-update PRs** (labeled, often marked with a vulnerability
description): treat as higher priority — review the advisory, then merge.

## 8. FAQ

* **"The 'Node.js 20 is deprecated' warning in my workflow logs is gone —
  is that because of the dependency auto-updates?"** Yes. GitHub's hosted
  runners deprecate **Node 20 as the runtime for GitHub Actions**, and older
  action versions (`actions/checkout@v4`, `actions/setup-python@v5`) still
  ran on it — which is what produced the warning line on every run.
  Dependabot opened a **github-actions** PR bumping those to **v7** (which
  run on **Node 24**), you merged it (or auto-merge did), and the warning
  disappeared. It was never a problem with *your* code or your Python
  scripts — just the runtime of the helper actions. You can verify it in
  any recent workflow log: it now downloads
  `actions/checkout@v7` / `actions/setup-python@v7` (see the 2026-09-15
  Reddit V1 run log — no deprecation warning). This is Dependabot doing
  exactly its job on the github-actions ecosystem.
* **"Will Dependabot break my `posted_reddit.json` / caches?"** No — it
  doesn't touch data files, only dependency pins.
* **"What if a bump breaks the live workflow?"** The next run logs the
  failure; hit *Revert* on the merge commit (or re-pin the old version) to
  restore the previous dependency set. That's why the CI gate matters — it
  catches install, syntax, import, and offline behavior failures before merge.
* **"Can it update the Reddit feed scripts' *code* or Python version?"** No.
  Code changes and the CPython runtime pin are deliberate human-reviewed work
  (the `testing area/` process and CI are the gate). Dependabot only manages
  third-party package/action versions. See [Python runtime policy](PYTHON_RUNTIME.md).
* **"Do I get an email?"** Yes — PR notifications work like any PR. You can
  mute the `dependencies` label if it's noisy, but the weekly cadence and
  grouped update configuration keep PR volume low.
* **"Is this the same as Dependabot alerts?"** Alerts (Security tab) just
  notify you about vulnerabilities; the PR feature here is the automated-fix
  part. Both are free; the PR part is what's configured by
  `.github/dependabot.yml`.

---

*Files involved: `.github/dependabot.yml` (the switch),
`.github/workflows/ci.yml` (the safety gate),
`.github/workflows/dependabot_auto_merge.yml` (opt-in auto-merge after CI),
`tests/test_smoke.py`, `tests/test_reddit_signals.py` and
`tests/test_twitter_media.py` (the offline suites the gate runs), `.github/workflows/python_version_bump.yml` (the separate
runtime automation), and `docs/PYTHON_RUNTIME.md` (the deliberately managed
CPython runtime pin).*
