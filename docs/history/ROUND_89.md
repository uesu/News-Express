# Round 89 (2026-10-26) — zizmor-verifiable action pins, runner-image updates, CI annotation hygiene, and dev-only runtime-bump coverage

## Scope and provenance

Follow-up to the sibling Game-Express CI/advisory work (its PR #71). Three of its
four findings had the same shape here; the fourth (Game-Express's feature-5 `beta`
module) has no counterpart in this repository and was deliberately not imported.

Requested scope: keep the development workflow surfaces honest under an online
`zizmor` audit, keep the runner image rolling forward, stop simulated test faults
from annotating CI runs, and keep the CPython bump in lockstep with the dev-only
sync workflow. No engine, provider, gate, schedule, Secret, Variable, dedup cache,
posting behavior or deployment change. Nothing runs live from this repository.

## Findings and corrections

1. **Annotated version comments disable `zizmor`'s pin audit.**
   Every `uses:` was already SHA-pinned (round 57), but the comments read
   `# v7 — SHA-pinned (round 57, immutable supply chain)`. `zizmor`'s
   `ref-version-mismatch` audit only inspects a comment it can parse, so the prose
   after the version silently removed the check. Reproduced with `zizmor 1.31.1`
   (online, `GH_TOKEN` set): an annotated comment reading `# v7.0.2` against the
   `actions/checkout` v7.0.1 commit produced **no** finding, while the bare
   `# v7.0.2` produced the mismatch. Comments are now bare `# vX.Y.Z` at end of
   line; the explanatory notes moved to the lines above. The round-89 smoke guard
   pins that form for every workflow file, so a future "helpful" annotation cannot
   re-hide the audit.

2. **Stale pin targets.** `actions/setup-python` was pinned at
   `5fda3b95a4ea91299a34e894583c3862153e4b97` (`v7`). It is now
   `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` (`v7.1.0`), the release the sibling
   validated. The other pins keep their commits and now carry their exact tags
   (`actions/checkout@3d3c42e5… # v7.0.1`, `actions/github-script@3a2844b7… # v9.0.0`),
   each verified against the repository's own tag objects.
   After the change, online `zizmor` reports the same audit set as before
   (`dangerous-triggers`, `artipacked`, `template-injection`, `dependabot-cooldown`;
   the `pull_request_target` and `${{ job.status }}` findings are the deliberate,
   documented round-87/dependabot designs) and **zero** `ref-version-mismatch`
   findings — now with the audit actually able to fire.

3. **Runner image stays automatic.** All jobs keep `runs-on: ubuntu-latest`
   (round 57-era layout); no image is pinned. The smoke suite now fails if a job
   drops it, so GitHub's runner OS migration keeps rolling forward by itself.

4. **CI annotation hygiene.** GitHub parses `::error::` / `::warning::` /
   `::notice::` / `::group::` / `::endgroup::` from the whole job log, so a test
   that echoes a *simulated* workflow fault still annotates the run. The smoke
   runner now wraps its own stdout in a recording proxy and fails
   (`r89d`) if any such command escapes. Simulated faults must stay inside a
   `subprocess` capture or an explicit `redirect_stdout`. Verified both ways:
   the suite is clean, and a deliberately injected `::error::` line fails with the
   leaked line named. Existing shell-simulation tests already capture their output,
   so no test needed rewriting.

5. **Dev-only workflow coverage in the Python bump.** `.github/workflows/sync_prod.yml`
   carries the same `python-version` pin but was not in the runtime-bump rewrite
   allowlist, so a CPython bump would leave it behind. It is now an *optional*
   allowlist target: rewritten when present (this development repository) and
   skipped with a `::notice::` when absent. That matters because `sync_prod.py`
   copies `python_version_bump.yml` into both production repositories, which never
   carry `sync_prod.yml`. A missing *required* surface still fails the job closed.
   The bump's final `git diff` display and its "unexpected file changed" filter now
   use the same effective target list.

## Guards added (`tests/test_smoke.py`)

- `r89a` — every `uses:` in every workflow is a 40-hex SHA pin with a bare
  `# vX.Y.Z` comment, plus a non-vacuity check over the whole workflow directory.
- `r89b` — every workflow keeps `runs-on: ubuntu-latest`.
- `r89c` — the real "Rewrite the allowlisted current-runtime files" shell is
  extracted and executed against a temporary git checkout three ways: with
  `sync_prod.yml` (pin rewritten), without it (success + skip notice), and with a
  required surface removed (fails closed, pin untouched). The current pin is read
  from `ci.yml`, so the guard never hardcodes a version the bump would rewrite.
- `r89d` — no GitHub Actions workflow command reaches the suite's stdout.

## Verification

- `python3 tests/test_smoke.py` → `SMOKE TEST: ALL PASS` (with the four new guards).
- `python3 tests/test_reddit_signals.py` → `REDDIT SIGNAL TEST: ALL PASS (96 pass)`.
- `python3 tests/test_twitter_media.py` → `TWITTER MEDIA TEST: ALL PASS`.
- Negative control: an injected `::error::` line in a scratch copy of the suite
  fails `r89d` and exits 1.
- `zizmor 1.31.1` online (token present): baseline 68 findings / 0
  `ref-version-mismatch` (audit blind); after 57 findings / 0
  `ref-version-mismatch` with the audit provably active. Deliberately wrong bare
  comment → `ref-version-mismatch` reported.

## Limits

- `zizmor` is not installed in this repository's CI, so the audit evidence above is
  a review-time check, not a committed gate; the committed gate is the `r89a`
  comment-form guard, which keeps the audit usable wherever it does run.
- A dependency/workflow update still waits for attended review (AGENTS.md), and a
  GitHub security hold is not approved by this round.
- These are proposed code and documentation changes; nothing here is evidence of a
  production run.
