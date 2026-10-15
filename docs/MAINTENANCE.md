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

`AUTO_MERGE_DEPENDABOT` and `AUTO_MERGE_PYTHON_BUMP` are exact `yes` switches.
The allowed merge method is squash, with merge as a fallback.

## Runtime proposer

`.github/workflows/python_version_bump.yml` never self-merges. `BUMP_PAT` is
required for publish; missing it is a configuration error, not a
`GITHUB_TOKEN` fallback. Publish runs only when candidate wheels installed
(`wheels==yes`). The rewrite allowlist is `.python-version` only.

## Monitor summaries

V3 engines write `RUN_REPORT_PATH` JSON with real numeric totals, the checked
out SHA, the lock digest, and skip/hold reasons they already computed. The
workflow persist step writes a persistence sidecar. `render_run_summary.py`
prints that report; a missing file is **unavailable**, never a fake zero.
Log-grep counters are not used. Persistence (local save / commit / push) is
reported independently.

## Crosspost video

Child-post identity, routing, and dedup stay on the child. Media may be
fetched from one resolved original (structured parent metadata, labelled
Original Post, or a crosspost-context permalink). Profile aliases
(`/user/…` ↔ `/r/u_…`) are retried when the first route returns stills for a
video post. Audio-cover renderers are not motion video. EmbedEZ/RedditEZ 1080p
quality remains an opportunity after a validated proxy video, not a guess
from a thumbnail.

## Production copy exclude

See `production_copy_exclude` in `.github/maintenance.json`. Caches listed
there must not be overwritten when copying this repo onto a production
checkout.
