# Python runtime policy — CPython 3.14.7

**Current production/CI pin:** `3.14.7`
**Reviewed:** September 30, 2026

The CI, Reddit monitor, and X monitor workflows all use the same exact
CPython version through `actions/setup-python@v7`:

```yaml
with:
  python-version: '3.14.7'
  cache: 'pip'
```

This file is the source of truth for why that number is exact, how it is
validated, and what is and is not automated.

## Why 3.14.7

Python **3.14.7** is the latest stable production release on the current
3.14 line (released August 5, 2026). Python 3.15 is still a release candidate
on this review date, so it is intentionally not used in a production monitor.
The authoritative release pages are:

* [Python 3.14.7](https://www.python.org/downloads/release/python-3147/)
* [Python 3.15.0 RC1](https://www.python.org/downloads/release/python-3150rc1/)

An exact patch pin gives every scheduled run, CI run, and manual dispatch the
same interpreter. That makes failures reproducible and means a new CPython
patch cannot silently alter a live posting run before this repository's CI has
examined it.

## Compatibility assessment

This repository is compatible by design with standard (GIL-enabled) CPython
3.14:

* The scripts use standard-library `asyncio`, `json`, `re`, and HTTP clients;
  no removed Python 3.11 API or CPython implementation detail is relied on.
* `feedparser` and `python-dotenv` are pure-Python dependencies in this use.
* `aiohttp>=3.14.3` publishes CPython 3.14 wheels, including Linux wheels used
  by GitHub-hosted Ubuntu runners. Its release line includes Python 3.14
  support and fixes.
* The workflows leave `freethreaded` at setup-python's default (`false`). This
  is deliberate: the monitor has not been validated on the experimental
  free-threaded build, and its work is primarily asynchronous network I/O.

Compatibility is **proved for a proposed change only when the PR's CI is
green**: it installs the real requirements under 3.14.7, compiles every
script, and runs the offline smoke suite. A manual dry-run of each monitor
remains the final recommended production check because third-party feeds and
Discord webhooks are intentionally not exercised by CI.

## Performance: realistic expectations

This is a safe runtime modernization, not a promise of a fixed percentage
speed-up:

* CPython 3.14 contains runtime and standard-library improvements. They can
  reduce interpreter overhead in Python-heavy sections.
* News Express is overwhelmingly **I/O-bound**: feed requests, mirror
  fallbacks, media probes, and Discord webhooks dominate a normal run. Network
  availability and latency therefore determine almost all end-to-end duration.
* The first job on the new patch can have a pip-cache miss. Subsequent runs
  reuse `actions/setup-python`'s dependency cache; its cache key includes the
  resolved Python environment and `requirements.txt`, so it avoids reusing an
  incompatible environment.
* The refreshed mirror chains improve worst-case latency more directly: known
  RSS-disabled/stale X endpoints are no longer serially waited on, while the
  current healthy RSS hosts are tried first.

In short: expect equal or modestly improved local CPU overhead after the first
cache warm-up, but judge monitor speed from Actions logs over several runs—not
from a benchmark claim that ignores the network.

## Is the Python runtime auto-bumped?

**No, and that is intentional.** The shipped Dependabot configuration has two
update ecosystems:

| Managed automatically (as PRs) | Not managed automatically |
|---|---|
| pip packages in `requirements.txt` | `python-version` workflow inputs |
| GitHub Actions used by `uses:` | CPython major/minor/patch selection |

Dependabot can update `actions/setup-python@v7`, but that action's
`python-version: '3.14.7'` input is repository configuration, not a dependency
manifest that Dependabot manages. The opt-in Dependabot auto-merge workflow
can merge a **green Dependabot dependency PR**; it never changes the Python
runtime itself.

Using `python-version: '3.14'` would float automatically to a later 3.14 patch,
but it would trade away reproducibility and pre-merge validation. This project
chooses the safer model: an explicit, reviewed runtime-bump PR followed by CI
and a monitor dry-run. Do not auto-jump major/minor versions in a live posting
workflow.

## Safe update procedure

1. Confirm the candidate is a final stable CPython release on python.org.
2. Change the one exact pin in **all three** executable workflows:
   `ci.yml`, `reddit_monitor.yml`, and `twitter_monitor.yml`.
3. Update this document and the README's embedded workflow examples.
4. Require a green CI run on the new interpreter.
5. Merge, then dispatch each monitor once with safe test controls (`dry_run:
   yes` for Reddit; a controlled `test_tweet`/test channel for X) and verify
   the Actions log reports the expected interpreter.
6. If an issue appears, revert the small workflow-only pin change; the prior
   interpreter is restored on the next run.
