# Round 91 (2026-10-26) — Production-sync hardening and the CPython 3.14.9 pin

## Provenance

The sibling Game-Express audit (`uesu/8mqzv4k2n7c`,
`polishing and refining/news express update.txt`) filed three findings against this
repository. Findings 1 and 2 are real and were **live** in production; finding 3 (the
pin bump) is folded in so the fix and the pin reach both production repositories in one
sync. Everything here was re-derived and re-tested in this repository — no Game-Express
code was copied wholesale, and nothing from its feature-5 `beta` module applies here.

## Finding 1 — a live red job in BOTH production repositories

`sync_prod.py` copies `.github/workflows/python_version_bump.yml` into
`uesu/7jkxmy9nvbc` and `uesu/wvkhabh2s22`, but it never copies `README.md`, `docs/`, or
`sync_prod.yml`. The bump workflow still listed `README.md`, `docs/PYTHON_RUNTIME.md`,
`docs/CI_SMOKE.md`, and `docs/DEPENDABOT.md` in its **mandatory** `ALLOWLIST`:

```bash
test -f "$file" || { echo "::error::Expected runtime file missing: $file"; exit 1; }
```

Observed evidence (not inference):

| Repository | Run | Step | Result |
|---|---|---|---|
| `uesu/7jkxmy9nvbc` | 40324777183 (12:43:53Z) | *Rewrite the allowlisted current-runtime files* | failure |
| `uesu/wvkhabh2s22` | 12:35:37Z | *Rewrite the allowlisted current-runtime files* | failure |

Reproduced locally against a real clone of `uesu/7jkxmy9nvbc` (`151e556`) by running
that step's exact shell:

```
::error::Expected runtime file missing: README.md      (exit 1)
```

The second half of the same bug was the unguarded `sed -i "s/python-3148/python-3149/"
docs/PYTHON_RUNTIME.md`, which aborts the step under `set -euo pipefail` in a checkout
without `docs/`.

**Fix.** The allowlist is split by where the file exists:

* required — `.github/workflows/{ci,reddit_monitor,twitter_monitor,python_version_bump}.yml`
  and `tests/test_smoke.py` (every checkout has them; a missing one still fails closed)
* optional — `.github/workflows/sync_prod.yml`, `README.md`, `docs/PYTHON_RUNTIME.md`,
  `docs/CI_SMOKE.md`, `docs/DEPENDABOT.md` (rewritten where present, skipped with a
  `::notice::` where absent)

The slug `sed` is guarded with `if [ -f docs/PYTHON_RUNTIME.md ]`. The version examples
in the workflow header were made version-agnostic, and the file itself now carries the
single literal current pin so it is a meaningful allowlist member.

**Why the suite did not catch it.** Round 89's `r89c` helper filled every missing file
with a one-line fixture, so a dev-only file always looked present. That fixture is
removed: absence is now part of the test, and `r91a` asserts the invariant that matters
— every mandatory allowlist path must exist in a checkout produced by `sync_prod.py`.

## Finding 2 — a dev-side sync could downgrade a production pin

`sync_tree()` overwrote `SYNC_WORKFLOW_FILES` byte-for-byte. If production merged a
Python bump (or a Dependabot action bump) before this repository did, the next dev sync
would push the older pin back.

**Fix.** `merge_workflow_pins_bytes(src, dst)` keeps only two things monotonic — the
`python-version:` pin and SHA-pinned `uses:` lines — and takes everything else from the
source, so a dev-side workflow fix still lands. `merge_smoke_python_pin_bytes(...)`
then raises the deployed `tests/test_smoke.py` r39 literal to the deployed `ci.yml` pin,
because the r39 guard fails on a suite/workflow mismatch even when the tree is healthy.
The report also stays truthful: a re-alignment that restores the exact pre-sync file is
not counted as an update, so a second sync is genuinely idempotent.

`PRIVACY_POLICY.md` and `TERMS_OF_SERVICE.md` joined `EXCLUDED_DEV_PATHS` (they were
never copied, but the exclusion is now explicit), and the unused `import json` is gone.

## Finding 3 — CPython 3.14.8 → 3.14.9

Applied with the same rewrite the workflow performs, over the same allowlist:
`ci.yml`, `reddit_monitor.yml`, `twitter_monitor.yml`, `python_version_bump.yml`,
`sync_prod.yml`, `README.md`, `docs/PYTHON_RUNTIME.md` (+ `python-3148` → `python-3149`),
`docs/CI_SMOKE.md`, `docs/DEPENDABOT.md`, `tests/test_smoke.py` (r39 guard).

Verified installable: `actions/python-versions` lists `3.14.9` as stable with Linux
22.04/24.04 x64 builds (release `3.14.9-39619022138`, published 2026-10-21), which is
the manifest `actions/setup-python` resolves.

Two documentation claims were corrected because the blanket rewrite would have made them
false: the README/docs "release date **September 30, 2026**" line is now the verified
runner-image publication date, and the "`3.14.7 -> 3.14.9` is a patch" example is now
`x.y.z -> x.y.(z+1)`. Historical records (`docs/history/`,
`docs/REDDIT_VIDEO_MEDIA_REPORT.md`, dated CHANGELOG entries) are deliberately untouched.

## Verification

| Check | Result |
|---|---|
| `python3 -m compileall -q "testing area" tests .github/scripts` | clean |
| `python3 tests/test_smoke.py` | `SMOKE TEST: ALL PASS` (1141 PASS, 0 FAIL) |
| `python3 tests/test_reddit_signals.py` | `ALL PASS (96 pass)` |
| `python3 tests/test_twitter_media.py` | `ALL PASS` |
| the same three suites in a production-layout checkout produced by `sync_prod.py` (no README/docs) | all pass (1136 PASS) |
| prod-shaped *Rewrite* step in that checkout | exit 0, all five required pins rewritten, five `::notice::` skips |
| panic case eliminated: same step in a production-shaped tree | exit 0 (was exit 1 `Expected runtime file missing: README.md`) |
| deploy path: prod tree pinned `3.14.8` → one `sync_tree` from this branch | 5 files updated; all four workflow pins become `3.14.9`; deployed suite 1136 PASS |
| deploy path: prod tree where production already bumped to `3.14.10` | pins stay `3.14.10`, dev content still lands, only `tests/test_smoke.py` reported (r39 re-aligned), second sync 0 updates, deployed suite 1136 PASS |
| sync into a real `uesu/7jkxmy9nvbc` clone (`151e556`) | 6 files updated (sync_prod.py, 4 workflows, test_smoke.py); zero dev-only files; second sync 0 updates |
| `zizmor 1.31.1` (online, token set), before vs after | byte-identical finding set vs `ae75dfc` — 55 findings, including the pre-existing high `dangerous-triggers` on `dependabot_auto_merge.yml` — and **0** `ref-version-mismatch` |
| YAML parse of every workflow + `dependabot.yml` | ok |

## Limits

- The production runs above were inspected through the GitHub API; their raw log
  archives were not downloadable from this sandbox, so the failure message is proven by
  the recorded failing *step* plus a local re-execution of that step's shell — not by a
  log line quoted from the run.
- The pin bump is validated against the `actions/python-versions` manifest and the
  repository's offline suites; no live monitor run was triggered from here.
- Workflow changes and the engine are attended-merge surfaces (AGENTS.md). A GitHub
  security hold is not approved by this round, and a green PR is not proof of a live run.
- `.github/workflows/` edits reach production through `sync_prod.yml` after this merges;
  confirm the next real `Python version bump (auto)` run and the next monitor tick.
- A hand-edited *partial* production pin state (one workflow bumped, its siblings left
  behind) is out of scope: the bump workflow rewrites every allowlisted workflow in one
  pass, so production pins move as a set. The r39 guard correctly reports such a
  half-bumped tree, and the round-91 merge deliberately does not try to guess it.
