# Maintenance contract — safe updates, merge control, run summaries

News-Express and Game-Express share this helper layout and a project-specific
`.github/maintenance.json` profile. The applications stay independent; only
the policy helpers are meant to stay identical.

Production copies may omit README/docs. Runtime, CI, the merge controller, and
the runtime proposer must still work. Do not copy development docs into
production unless a task explicitly asks, and **never overwrite production
dedup caches**.

## Pieces

| Path | Role |
|---|---|
| `.python-version` | Exact CPython pin (`3.14.8`) |
| `requirements.txt` / `requirements-dev.txt` | Hashed frozen graphs |
| `.github/maintenance.json` | Project profile (checks, compile commands, identities) |
| `.github/scripts/maintenance.py` | Pure policy + explicit `apply-live` adapter |
| `.github/scripts/python_version_bump.py` | Pin proposer (no merge, no GitHub writes without flags) |
| `.github/scripts/ci.py` | Command registry; every `tests/test_*.py` must be listed |
| `.github/scripts/render_run_summary.py` | Markdown footer from a structured report |
| `.github/workflows/ci.yml` | Hashed install + fail-closed `maintenance-ci` |
| `.github/workflows/maintenance_merge.yml` | Single merge controller |
| `.github/workflows/python_version_bump.yml` | Select / validate / publish a pin PR |

There is **no** GitHub Actions workflow lockfile and no
`dependabot_auto_merge.yml`. Dependabot still opens PRs;
`maintenance_merge.yml` decides.

## Merge controller (fail closed)

The controller checks out **`github.event.repository.default_branch` only**
with `persist-credentials: false`. It never executes PR-head
`maintenance.py` / `maintenance.json`.

`decide` / `--fixture` never talks to GitHub. Live merges require the explicit
`apply-live --apply-live` flag plus `GITHUB_TOKEN`. Missing fixture fields,
skipped/neutral/cancelled checks, pending checks, a changed head SHA, hold
labels, `CHANGES_REQUESTED`, untrusted updaters, and anything other than the
exact repository variable value `yes` all refuse the merge.

Live evidence is fail-closed: review, status, check-run, workflow-run, job,
and commit API failures refuse the merge (they do not become empty lists).
Check runs, statuses, and jobs are paginated; truncation is a failure. Each
required check must come from the trusted CI workflow id/path/run **and** a
matching successful job in that run on the exact head; a same-name job from
another workflow is not enough, a familiar github-actions app/name is not
enough, and a missing SHA or app cannot pass. Legacy Combined Status rows
cannot satisfy a required check, but a SHA-bound pending/failed/error status
for a required context still blocks. Newest *decision* review per user is the
effective state — `COMMENTED` and `PENDING` never clear `CHANGES_REQUESTED`.
Dependabot allowed paths come from the trusted profile, never from the PR's
own file list. Grouped lock updates classify **every** significant
requirements line (pins, extras, markers, index/constraint/VCS/direct-URL
directives, hash-only and unparsed lines) and associate hash edits with their
package block; an unchanged-version hash mutation requires review even when
another pin is a safe patch. The highest-risk member wins, and hash-only or
truncated patches are review-required. File content is
reconciled against snapshot metadata so a routine label cannot hide an
index-url mutation. A Python bump PR must use
the `chore/python-` prefix; `github-actions[bot]` as commit author alone is
not enough (a PAT may open the PR). The live adapter refreshes the snapshot
immediately before merge.

`AUTO_MERGE_DEPENDABOT` and `AUTO_MERGE_PYTHON_BUMP` are exact `yes` switches.
The allowed merge method is squash, with merge as a fallback.

## Runtime proposer

`.github/workflows/python_version_bump.yml` never self-merges. `BUMP_PAT` is
required for publish; missing it is a configuration error, not a
`GITHUB_TOKEN` fallback. Publish runs only when candidate wheels installed
(`wheels==yes`). The rewrite allowlist is `.python-version` only. Next-minor
soak uses an upstream release date (manifest field or a bounded GitHub
release lookup); missing dates defer. The GitHub `published_at` for
`actions/python-versions` is setup-python artifact publication time, not the
CPython python.org release date — a rebuilt archive must not silently
redefine soak age. Forced overrides validate numeric direction, a stable
linux-x64 archive, and review policy; a lower patch is not auto-eligible.
Lock regeneration must be byte-stable after compiler-header normalization
only (`--reuse-hashes --newline=lf --no-emit-index-url`) on the pinned
3.14.8 interpreter; changing an index/constraint/marker/via-comment without
a pin change still fails. The runtime lock is the 3.14.8 resolution
(`typing-extensions` is not frozen; aiohttp/aiosignal only need it on
`python_version < "3.13"`). Pre- and post-rewrite validation runs the full CI registry, including
`lock-consistency` and `workflow-security`. Pinned `actionlint` is required;
download failure or `SKIP_ACTIONLINT=1` is not a green gate.

## Monitor summaries

V3 engines write `RUN_REPORT_PATH` JSON with real numeric totals, the checked
out SHA, the lock digest, and skip/hold reasons they already computed. HTTP
counters wrap the existing session (no extra requests). `host_select` records
a useful feed or media choice, not every HTTP 2xx/3xx. Early-exit and failed
local-save paths still emit a report; an atexit write after an unhandled
failure is `failed`. Report-write errors never mask the application
exception. The workflow persist step writes a persistence sidecar.
`render_run_summary.py` prints that report; a missing file is
**unavailable**, never a fake zero. Log-grep counters are not used.
Persistence (local save / commit / push) is reported independently.

## Crosspost video

Child-post identity, routing, and dedup stay on the child. Media may be
fetched from one resolved original (structured parent metadata, a labelled
Original Post, or a permalink in a crosspost-from / crosspost-of clause). A
`crosspost` keyword plus an unrelated body link is not a parent. Profile aliases
(`/user/…` ↔ `/r/u_…`) are retried when the first route returns stills for a
video post. Audio-cover renderers are not motion video; og consumers skip a
leading audio-cover `og:video` and keep a later motion URL. EmbedEZ/RedditEZ
1080p quality remains an opportunity after a validated proxy video, not a
guess from a thumbnail.

## Production copy exclude

See `production_copy_exclude` in `.github/maintenance.json` and the
development-side [`COPY_MANIFEST.md`](COPY_MANIFEST.md). Caches listed
there must not be overwritten when copying this repo onto a production
checkout. Both engines and both monitor workflows remain `runtime_files`.
The three heads are not equivalent copies; green development checks do not
prove production parity. Game helpers are not byte-identical at the reviewed
heads — see the convergence plan in that manifest. Coverage limits:
[`ACCEPTANCE_COVERAGE.md`](ACCEPTANCE_COVERAGE.md).
