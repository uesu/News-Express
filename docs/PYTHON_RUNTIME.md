# Python runtime policy — CPython 3.14.8

**Current production/CI pin:** `3.14.8`

**Reviewed:** 2026-10-06 against official Python sources

The CI, Reddit monitor, and X monitor workflows use the same exact CPython
version through SHA-pinned `actions/setup-python@v7`:

```yaml
with:
  python-version-file: .python-version
  cache: 'pip'
```

The pin file `.python-version` currently contains `3.14.8`. Workflows install
the frozen hashed graph with `pip install --require-hashes --only-binary=:all:`.

This file is the current operational policy for the exact runtime pin, the
validation gates around it, and what the automation is allowed to change.
Historical records under `docs/history/` are intentionally not rewritten just
because the current pin changes.

## Official status reviewed for this pin

Python **3.14.8** is the current News-Express runtime. The official Python
release page identifies it as the eighth maintenance release of Python 3.14 and
lists its release date as **September 30, 2026**:

* [Python 3.14.8 release page](https://www.python.org/downloads/release/python-3148/)

As of this 2026-10-06 review, News-Express is **not** adopting Python 3.15:

* the official Python downloads page still serves Python 3.14.8 as the latest
  Python 3 source release;
* the Python Developer's Guide lists Python 3.15 as `prerelease`; and
* `https://www.python.org/downloads/release/python-3150/` does not publish a
  final Python 3.15.0 release page.

When Python 3.15 final is officially available, it is still a **new minor
series** for this repository and must receive a pull request plus manual review;
it is not treated as an ordinary patch update merely because it exists.

## Version terminology used here

News-Express uses the normal `MAJOR.MINOR.PATCH` terminology:

| Example | Classification | Repository policy |
|---|---|---|
| `3.14.7 -> 3.14.8` | **PATCH** update inside the same `3.14` series | eligible for automated proposal and, when every gate passes, optional patch auto-merge |
| `3.14.8 -> 3.15.0` | new **MINOR** series | PR only; manual review required even if validation passes |
| `3.x -> 4.x` | **MAJOR** update | deliberate manual migration; never handled as an ordinary patch/minor bump |

A new minor series must never be described as a patch update. A lower
patch such as `3.14.8 -> 3.14.7` is a **downgrade**, not an auto-eligible
proposal, even when forced. Forced versions must exist as a stable
linux-x64 archive in the setup-python manifest; missing, prerelease, or
out-of-policy majors remain review-required or failed.

## Repository and production scope

`uesu/News-Express` is the development repository. The Reddit and X/Twitter
production repositories have their own production-only workflows and receive
production changes separately. The Python runtime bump workflow in this
repository only opens and optionally merges PRs in **this** repository; it does
not copy News-Express documentation into production repositories and does not
modify production caches or state files.

## Compatibility assessment

This repository is designed for standard (GIL-enabled) CPython 3.14:

* The scripts use standard-library `asyncio`, `json`, `re`, and HTTP clients;
  no removed Python 3.11 API or CPython implementation detail is intentionally
  relied on.
* `feedparser` and `python-dotenv` are pure-Python dependencies in this use.
* `aiohttp>=3.14.3` publishes CPython 3.14 wheels, including Linux wheels used
  by GitHub-hosted Ubuntu runners. Its transitive C-extension dependencies
  (`multidict`, `yarl`, `frozenlist`, and `propcache`) also need wheels for a
  proposed interpreter.
* The workflows leave `freethreaded` at setup-python's default (`false`). This
  is deliberate: the monitor has not been validated on the experimental
  free-threaded build, and its work is primarily asynchronous network I/O.

Offline repository validation means the real requirements install under the
pinned interpreter, all Python files in `testing area/` and `tests/` compile,
and every registered offline suite passes. Third-party feeds, Discord delivery, external
cron triggers, and future service outages remain outside offline validation and
should be checked with the documented dry-run/test-post controls when needed.

## Performance: realistic expectations

This runtime pin is for reproducibility and controlled upgrades, not a promise
of a fixed percentage speed-up:

* CPython 3.14 contains runtime and standard-library improvements. They can
  reduce interpreter overhead in Python-heavy sections.
* News-Express is overwhelmingly **I/O-bound**: feed requests, mirror
  fallbacks, media probes, and Discord webhooks dominate a normal run. Network
  availability and latency therefore determine almost all end-to-end duration.
* The first job on a new patch can have a pip-cache miss. Subsequent runs reuse
  `actions/setup-python`'s dependency cache; its cache key includes the resolved
  Python environment and `requirements.txt`, so it avoids reusing an
  incompatible environment.

Judge monitor speed from Actions logs over several runs, not from benchmark
claims that ignore network behavior.

## Is the Python runtime auto-bumped?

**Not by Dependabot.** Dependabot manages dependency manifests and `uses:`
Action versions; it does not manage `python-version` workflow inputs.

| Managed by Dependabot | Managed by the Python runtime workflow |
|---|---|
| pip dependency ranges in `requirements.txt` | exact CPython `python-version` pins |
| GitHub Actions used by `uses:` | patch/minor candidate selection and validation |

Using `python-version: '3.14'` would float automatically to a later 3.14 patch,
but it would trade away reproducibility and pre-merge validation: the new
interpreter could first be seen by a live posting run.

`.github/workflows/python_version_bump.yml` keeps the exact pin while still
checking for safe candidates. Weekly, and on manual dispatch, it considers only:

1. the newest stable patch of the current series, or
2. if no newer patch exists, the newest stable patch of the next minor series.

It never skips a minor series and never proposes a major-version migration.
Release candidates, betas, alphas, and versions absent from the
`actions/python-versions` linux-x64 manifest are ignored.

## Runtime bump validation gates

A runtime bump PR is only opened after these gates pass under the candidate
interpreter:

| Gate | Why |
|---|---|
| candidate exists in the `actions/python-versions` manifest with a linux-x64 build | that manifest is what `setup-python` resolves; a version absent from it breaks the workflows |
| `pip install --only-binary=:all: -r requirements.txt` | compiled dependencies must have prebuilt wheels for the candidate ABI; if wheels are missing, the bump is deferred instead of compiling from source |
| soak period for new minor series only (`PYTHON_BUMP_SOAK_DAYS`, default `30`) | an `x.y.0` minor release is deliberately reviewed after it has been available; the selector uses the manifest `release_date`/`published_at` or a bounded GitHub release lookup, and **defers** when no date is available; patch releases skip the soak. The GitHub `published_at` for `actions/python-versions` is the **setup-python artifact publication time**, not the CPython python.org release date. A rebuilt archive must not silently redefine soak age. |
| `python -m compileall -q "testing area" tests` | syntax/importability gate for every Python file used by the monitors and tests |
| `python tests/test_smoke.py` | offline card-pipeline and workflow invariant guards |
| `python tests/test_reddit_signals.py` | pure Reddit gate/decision guards |
| `python tests/test_twitter_media.py` | pure X (Twitter) V3 media guards (canonical order, GIF chain, heal contract) |
| repeat the full `ci.py` registry after the rewrite (`application`, `maintenance`, `lock-consistency`, `workflow-security`) | the rewrite updates `.python-version`; the candidate tree is revalidated with the same groups PR CI uses |

The rewrite scope is an explicit current-runtime allowlist: workflow pins,
current runtime documentation, README runtime references, and the smoke-test
pin guard. `docs/history/` is checked separately and fails the workflow if it
changes. Unexpected files also fail closed.

## Auto-merge policy and authentication

`AUTO_MERGE_PYTHON_BUMP` is a repository **Variable** with one supported
auto-merge value:

| Variable value | Behavior |
|---|---|
| unset, empty, or anything other than `yes` | open the verified PR and wait for manual review |
| `yes` | auto-merge verified **patch** bumps only |

There is intentionally no `all` mode. A new minor series such as Python 3.15
must remain a manual-review PR, and a major version such as Python 4 requires a
deliberate migration plan.

The workflow uses `BUMP_PAT` only through GitHub Actions secret references
(`secrets.BUMP_PAT`) for checkout, PR creation, and the optional patch merge.
No token value belongs in the repository, logs, docs, or workflow inputs. If the
secret is missing or invalid, the job fails safely rather than falling back to a
direct push to `main`.

## Safe manual update procedure

1. Confirm the candidate is a final stable CPython release on python.org.
2. Classify the change as patch, minor, or major using the terminology above.
3. Change the exact pin in `ci.yml`, `reddit_monitor.yml`, and
   `twitter_monitor.yml`.
4. Update current documentation (`README.md`, `docs/CI_SMOKE.md`,
   `docs/DEPENDABOT.md`, and this file) without rewriting historical records.
5. Run the compile and offline suites locally when possible, then require CI on
   the PR.
6. For a production rollout, update the separate production repositories through
   their production-only process; do not copy this development documentation or
   historical audit archive into production.
7. After merge, dispatch each monitor once with safe test controls (`dry_run:
   yes` for Reddit; a controlled `test_tweet`/test channel for X) when live
   service behavior needs confirmation.
