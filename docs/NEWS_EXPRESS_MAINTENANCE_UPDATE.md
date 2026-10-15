# News-Express — complete maintenance update specification

**Prepared:** 2026-10-15 (Asia/Manila)

**Target:** `uesu/News-Express`, followed by the maintainer's manual copy to
`uesu/7jkxmy9nvbc` and `uesu/wvkhabh2s22`

**Status:** implementation specification, not an already-applied application
update. The hosted baseline evidence below is real; proposed fixes and new
acceptance tests must still be implemented and rerun on the final PR head.

This is a standalone News-Express plan. It includes the PR title/body, exact
add/modify/remove responsibilities, common automation contract, reporting design,
configuration/doc cleanup, production-copy boundary and acceptance criteria.
The companion Game-Express file is separate; neither requires the other's
application code at runtime. No PR or production change was made for this audit.

## PR title

```text
Maintenance: unify safe updates, freeze runtime dependencies, and make News summaries accurate
```

## PR body

Use this body for the **implementation PR**, not a Markdown-only PR claiming the
code is finished. Update unchecked items only after the corresponding work passes.

```markdown
## Summary
Implement consistent, review-aware maintenance without changing News posting
behavior. Share the maintenance contract with Game-Express while keeping the
applications and the manually deployed production copies independent.

## Scope
- [ ] Add one exact Python pin and generated hashed runtime dependencies.
- [ ] Extract runtime-update policy and CI validation into tested small helpers.
- [ ] Replace separate/self-merge paths with one trusted, fail-closed controller.
- [ ] Make the updater work without README or development docs in production.
- [ ] Replace timestamp-sensitive summary scraping with structured outcomes.
- [ ] Report code revision, real numeric totals and final state-push status.
- [ ] Reconcile active docs, AGENTS, environment examples and ignore rules.
- [ ] Preserve V1/V2/V3 compatibility, fleets, routing, media, dedup and state.
- [ ] Do not add Actions workflow lockfiles or change the external scheduler.

## Evidence already available
- Hosted baseline: https://github.com/uesu/News-Express/actions/runs/38732934814
- News development and both production snapshots passed the existing three
  suites on Python 3.14.8; all tracked files were read and inventoried.
- The audit reproduced the old check-classifier, timestamp-summary and
  documentation-free production updater gaps. Those findings are not fixes.

## Required implementation validation
- [ ] Existing suites pass unchanged, plus new maintenance/reporting/config tests.
- [ ] Exact-head, risk/hold and negative-check fixtures all pass.
- [ ] Clean installs use the frozen graph; lock regeneration is reproducible.
- [ ] Both documentation-free production profiles pass the same validation.
- [ ] Safe hosted checks pass on this actual completed PR head.
- [ ] No Discord test posts, state resets, production dispatches or real test merges.

## Deployment and rollback
Copy only the approved runtime/automation/test manifest to both production
repositories after review. Keep each repository's existing runtime caches and
credentials. Roll back code/workflows/locks together without reverting state.
```

## Reviewed baseline and live evidence

| Repository/profile | Reviewed source commit | Files fully read | Bytes |
|---|---|---:|---:|
| News development | `83a701ab4c8644a9b1ae5e61472dafdf8175b99a` | 72 | 1,609,330 |
| Reddit production | `497c557b2cf19840976e462ed05a7ec65a57cd50` | 28 | 1,129,721 |
| Twitter production | `905e4c96f52be88bbe895d891fba1bead3024cb5` | 28 | 1,112,297 |

[Hosted audit run 38732934814](https://github.com/uesu/News-Express/actions/runs/38732934814)
completed successfully in all four jobs, including Game. Each News profile ran:

```bash
python -m compileall -q "testing area" tests
python tests/test_smoke.py
python tests/test_reddit_signals.py
python tests/test_twitter_media.py
```

All commands exited 0. The Reddit signal suite explicitly reported 96 passes;
the other suites reported `ALL PASS`. These were the current suites, not the
new tests specified below. All used Python **3.14.8** with resolved runtime
packages **aiohttp 3.14.5**, **feedparser 6.0.14**, **python-dotenv 1.2.4**.
PyYAML 6.0.3 was installed for the audit. The runner was GitHub-hosted Ubuntu 24;
image versions differed between jobs, so do not claim an identical machine/IP.

Every tracked file was read and SHA-256 inventoried; Python AST and JSON parsing
reported no errors. Environment/read-site and Markdown-link scans were combined
with focused maintenance, workflow, reporting, configuration and documentation
review. Full file coverage is not a guarantee that every application edge case
has been semantically proven. Historical Markdown placeholders such as `(url)`
were scan candidates, not confirmed broken current navigation.

The first audit launch, run `38732818668`, failed YAML validation before any test
ran because a colon-bearing pip argument needed a block `run` value. The audit
workflow was corrected and locally parsed; the successful run above is the
replacement evidence. This was not a News application test failure.

The audit used no posting credentials and did not dispatch a monitor, merge a
PR, alter settings or push state. It does **not** prove the future maintenance
implementation or an end-to-end production webhook/update/merge cycle.

### Current production consistency

All **24 non-state files** in each 28-file production snapshot match the News
snapshot byte-for-byte. The differing files are expected per-instance cache data;
do not overwrite them to make hashes match. The four cache paths are
`posted_reddit.json`, `posted_tweets.json`, `pending_reddit.json` and
`proxy_health.json`. Matching code and independent state is the desired result.

### Confirmed issues to fix

| Finding | Evidence/meaning | Required correction |
|---|---|---|
| Documentation-dependent runtime bump | Both production copies lack README and three docs that the current rewrite path requires | Runtime pin/profile must not depend on optional docs |
| Incomplete successful-check definition | Extracted current classifier accepted unrelated success, skipped and neutral fixtures as ready | Require the trusted expected successful set and latest-head association |
| Multiple merge paths | Proposer can rely on its pre-PR gates while Dependabot has another merge path | One final controller; ordinary final-head PR CI is mandatory |
| No complete update-risk/hold policy | Green alone is not a safe rule for majors, unknown/mixed groups and maintainer holds | Implement the risk table and fail-closed review handling below |
| Timestamp-sensitive Twitter account totals | Valid timestamp-prefixed feed fixture counted zero account matches | Structured counters rather than anchored awk against formatted logs |
| Misnamed numeric totals | Counting matching “new posts” log lines is not summing posted items | Count actual posted results and distinguish accounts, feeds and entries |
| Floating package graph | Direct range installation resolved versions above the declared minimums | Generate and consume one tested frozen graph |
| Missing-release-date soak bypass | Current selection can proceed without proving a minor release's age | Defer when age is unknown; next-minor migration requires review |

Earlier green weekly bump runs do not clear these findings: the relevant
candidate-validation/proposal/merge branches were skipped when no eligible update
was found. Do not report that as an end-to-end upgrade test.

## News-specific implementation work

### Add

Add all common files in the shared contract below, plus `.python-version`,
`requirements.in`, the generated runtime lock and any required dev-tool inputs/
locks. `requirements.txt` already exists and becomes generated, not a second
human-edited list. Add fixtures under `tests/fixtures/maintenance/` for timestamped
logs, structured reports, no-docs profiles, candidate manifests and fake API
responses. Do not embed actual secrets or live cache contents in fixtures.

The common runtime-proposer adapter is new in News. Its policy must be shared
with Game rather than copying today's large inline workflow program.

### Modify application/workflow code narrowly

| File | Required change |
|---|---|
| `.github/workflows/ci.yml` | Read the exact pin, install the frozen graph, call the common CI adapter; add maintenance/config/report tests and a stable required final gate |
| `.github/workflows/python_version_bump.yml` | Thin selection/validation/publisher stages; remove doc rewrites and self-merge; preserve weekly/manual operation |
| `.github/workflows/reddit_monitor.yml` | Exact pin/frozen install; capture checked-out code SHA; pass internal report path; always-run final summary after existing persistence |
| `.github/workflows/twitter_monitor.yml` | Same integration; remove brittle awk/account/post totals after structured reporting is available |
| `testing area/reddit_main_v3.py` | Bounded outcome counters and exception-safe report emission only; preserve all listing, hold, archive, media, post/edit/retract and dedup decisions |
| `testing area/twitter_v3.py` | Bounded per-account/feed/post counters; report actual successful results instead of parsing timestamped log strings |
| `.github/dependabot.yml` | Routine vs review-required grouping, supported compiled-input regeneration and no Actions-lockfile integration |
| `tests/test_smoke.py` | Keep existing behavior assertions; replace only maintenance topology/version-literal assertions made obsolete by the deliberate design |
| `.env.example` | Reconcile actual readers/defaults, dynamic webhook names, V1/V2-only settings, workflow-only Variables and local-only diagnostics |
| `.gitignore` | Keep existing secret/cache protections; add only narrowly scoped generated report/tool paths as needed |

For legacy engine selections, either instrument the same schema without behavioral
change or render an explicitly labeled `legacy summary unavailable` section with
an accurate workflow outcome. Do not manufacture V3 counters for a V1/V2 run.
Default V3 reporting must be fully implemented and tested.

Retain the current cache-merge helper and all force-add/retry/rebase semantics of
persistence. This PR must not replace `.github/scripts/merge_monitor_caches.py`
with a simplistic last-writer-wins overwrite. The new summary observes its result.

### Remove/replace

- Remove `.github/workflows/dependabot_auto_merge.yml` **after** its legitimate
  triggers and guards are replaced by `maintenance_merge.yml` in the same change.
  Do not leave two controllers competing to merge the same PR.
- Remove the proposer self-merge section, duplicate version-selection/policy
  blocks and mandatory README/doc version rewrites.
- Remove the old Twitter awk counters after the renderer is integrated; retaining
  both creates contradictory totals. Do not remove ordinary useful log lines.
- Remove current-doc suggestions that a skipped/neutral check is a successful
  required test or that a green no-update run proves a completed upgrade.
- Remove obsolete active instructions only after a real reader/wiring audit.
  No whole application engine, test fixture, history file or cache is approved
  for deletion simply because it is large or not the default mode.

### Current documentation cleanup, file by file

| File | Required disposition |
|---|---|
| `README.md` | Concise operating/config/test overview; link the canonical maintenance guide and explain manual production copying; no patch-version rewrite requirement |
| `AGENTS.md` | Update the current topology/test contract, new helpers, no-posting validation, protected behavior and no Actions locks; preserve useful engine constraints |
| `docs/PYTHON_RUNTIME.md` | Exact pin, candidate/soak policy, BUMP_PAT publisher, no self-merge and docless production support |
| `docs/DEPENDABOT.md` | Frozen package updates, risk/group policy, trusted final checks, review holds and truthful decision summaries |
| `docs/CI_SMOKE.md` | Actual CI adapter commands, mandatory vs advisory distinction, negative maintenance fixtures and no-secret/no-posting limits |
| `docs/REPOSITORY_TRACKING.md` | Current deployment boundary and code-vs-state equality; append a dated review instead of claiming every repository is always synchronized |
| `docs/CHANGELOG.md` | Add a dated maintenance entry after implementation with precise changes, preserved behavior and validation evidence; no invented release/round number |
| `docs/REDDIT_VIDEO_QUALITY.md` | Preserve valid V3 quality rules; reconcile links/current wording only if this maintenance change affects them |
| `docs/DISCOHOOK.md` | Preserve supported preview behavior; clearly distinguish generating payload/links from sending a Discord message |
| `docs/REDDIT_VIDEO_MEDIA_REPORT.md` | Preserve dated observations; clarify historical scope only if currently ambiguous |
| `docs/VIDEO_ONLY_QUALITY_POLICY_CONFIRMATION.md` | Preserve the policy confirmation and its historical date; do not claim media behavior changed here |
| `docs/history/**` | Keep factual history, incident/replay records and historical version references; update an index only if a real document link changes |
| `PRIVACY_POLICY.md`, `TERMS_OF_SERVICE.md` | Preserve substantive legal text; no new storage/provider policy invented for a reporting-only change |

`REDDIT_MIRROR` is **V1-only**, not globally unused. `EMBEDEZ_API_KEY` is a V2
setting, not a V3 requirement. Keep those distinctions. OAuth app credentials
were not shown in the supplied inventory: document the normal optional/skipped
path rather than demanding OAuth or forcing JSON probes. Do not drop a valid
variable because GitHub's catch-all secret/variable wiring or dynamic name
construction prevents a simple literal match.

### Required News report behavior

- Prefix timestamps freely; counters must no longer depend on where `[account]`
  appears in a text line. Track configured/attempted/usable **unique accounts**
  separately from HTTP requests, selected-feed entries and posts sent.
- Sum actual numeric outcomes. Three new posts from one account are three posts,
  not one matching log line; repeated fallback attempts do not create new accounts.
- Reddit's no-new-items, optional OAuth skip, ordinary dedup and intentional
  retryable hold are named benign outcomes, not blanket source failures.
- Keep archive/no-recheck, retryable hold, missing/removed/deleted and request
  failure distinct. Reporting must not change those classifications or cache data.
- Emit the final state-persistence footer even when setup/application execution
  fails. Show missing data as unavailable and do not claim a successful push
  because a local JSON save succeeded.

### Production-copy manifest and parity gate

The implementation must produce a deterministic manifest of runtime/maintenance
files with hashes, compared in both production profiles. Include:

- `.python-version`, runtime dependency input/generated lock, and dev-test locks
  only if the deployed CI needs them;
- `.github/maintenance.json`, all common helper scripts, the existing cache merge
  helper, CI/updater/merge/monitor workflows and Dependabot configuration;
- `.env.example`, `.gitignore`, maintained engine scripts and regression tests/
  fixtures required by the deployed CI;
- any explicitly imported new runtime helper, if instrumentation needs one.

**Exclude from copy/overwrite:** every runtime cache/state file, repository
Secrets/Variables, repository settings, development README/AGENTS/legal/history
requirements, this specification and one-off diagnostic probe/audit workflows.
The production updater must not require excluded development docs. Copying code
must never silently reset or share dedup state between the two live repositories.

Test the complete manifest in a clean production-layout fixture with no README
or `docs/` directory. After the maintainer's eventual copy, compare the manifest
hashes, not whole-repository SHAs or cache contents. Both productions should have
the same approved code/automation while retaining their own state and settings.

## Scheduler, credentials and settings: preserve working setup

The supplied screenshots and prior secret/non-secret inventories were received.
The cron-job.org screenshot shows successful dispatch requests, not proof that a
monitor completed successfully. Preserve its headers and payloads, including:
`Accept: application/vnd.github+json`, JSON Content-Type, the existing token auth
scheme and `X-GitHub-Api-Version: 2026-03-10`. That API version is supported and a
read-only request using it succeeded; do not downgrade it.

Keep BUMP_PAT and the existing dispatch/feed/webhook secrets where already used;
never request their values in chat or print the serialized secret dictionary.
The shown fine-grained bump token covers metadata read and contents/PR/workflow
write; do not assume that makes it an Actions-dispatch token. Optional later
repository/expiry narrowing is separate hardening, not a prerequisite or an
emergency rotation based on screenshots that did not show token values.

Classic branch-protection/settings visibility was incomplete (403 responses).
Do not infer absent protection or silently change rules. News's native auto-merge
flag was false when inspected; distinguish that feature from a direct, guarded
merge API call. Do not enable a setting merely to make the proposed design pass.

## Shared maintenance contract — required in this repository

Implement the same policy, helper interfaces and report schema as the sister
project, with a small repository-specific profile. Do not merge the two
applications, force identical monitor workflows, or duplicate large inline
shell/Python programs. Shared helpers should be identical; project profiles
supply the test commands and file lists. Add a drift test for those helpers.

### Non-negotiable boundaries

1. **No GitHub Actions workflow lockfiles.** Do not create
   `.github/workflows/actions.lock`, install `gh-actions-lock`, run its commands,
   or enable a Require lockfile policy. The maintainer explicitly deferred that
   preview feature. Keep Actions pinned to reviewed full 40-character SHAs.
2. Preserve the external cron-job.org monitor schedule, workflow-dispatch input
   names/defaults and `cancel-in-progress: false` on posting workflows. Do not
   add a second monitor scheduler. The separate weekly maintenance schedule is
   permitted and must not run a monitor.
3. Preserve routing, pings, game/account/subreddit selection, filtering,
   deduplication, cache retention, posting/editing, media handling and state
   persistence behavior. Reporting may explain those decisions, not change them.
4. No fleet reorder, mirror removal, new scraper, challenge bypass, new forced
   probe, token forwarding or freshness heuristic in this housekeeping change.
5. No repository setting/token change, deployment or PR creation as part of
   implementing or validating this specification without the maintainer's
   separate action. Normal future scheduled update PRs remain the intended
   function of the approved automation.
6. Do not claim bug-free operation or peak performance from an offline pass.
   Report what was tested, what changed, and what remains untested.

### One runtime pin and a frozen Python package graph

- Add `.python-version`, initially **3.14.8**, the exact interpreter verified in
  the hosted baseline. It is the current runtime source of truth, not a claim
  that it is the newest release available at implementation time.
- Configure all current-runtime setup-python steps to read that file. Keep
  historical version examples in dated archives unchanged. Remove the need to
  rewrite README prose or hard-coded test expectations for every patch bump.
- Move the current human-maintained package ranges to `requirements.in`.
  Generate `requirements.txt` with exact direct/transitive versions and hashes
  using `pip-tools==7.5.3` with `pip==26.1.1` in an isolated, pinned compiler
  environment. Those versions are published and their Python requirements
  include 3.14; compiler compatibility/reproducibility still needs its own test.
  Include the compiler toolchain in the generated dev/tool lock; do not hand-write
  a partial lock.
  Known-good direct versions in the baseline were aiohttp 3.14.5, feedparser
  6.0.14 and python-dotenv 1.2.4. A newly resolved graph must be tested again.
- Use a single generated package-lock format, compatible with the existing pip
  Dependabot ecosystem. CI and monitor runs must install the same committed
  runtime graph with hash verification. A Python package lock is **not** the
  declined Actions lockfile feature.
- Separate test-only tools in `requirements-dev.in` / `requirements-dev.txt`
  when required; constrain their resolution against the runtime graph so test
  dependencies cannot silently replace a runtime dependency. Do not move PyYAML
  into runtime requirements merely because the audit used it for tests.
- Record the actual interpreter, package-lock digest and runner image in the
  summary. Do not opportunistically upgrade runtime packages or pip on every
  monitor run. Cache installation work by OS, exact interpreter and lock digest;
  do not cache a mutable dependency resolution as a substitute for locking.
- Preserve normal security/version update detection. Prove the chosen compiled
  requirements format is regenerated correctly by Dependabot, including hashes
  and transitive dependencies. A stale manifest/lock pair is a failed gate.

### Common files and responsibilities

| File | Responsibility |
|---|---|
| `.github/maintenance.json` | Schema-versioned project profile, mandatory checks, test commands, supported targets, path/risk rules and human-review labels |
| `.github/scripts/maintenance.py` | Testable, mostly pure version selection, update classification, diff validation and decision/report helpers |
| `.github/scripts/python_version_bump.py` | Thin runtime-proposer adapter; retain this familiar entry point, do not duplicate the shared rules |
| `.github/scripts/ci.py` | One explicit validation command registry used by ordinary CI and candidate-runtime validation |
| `.github/scripts/render_run_summary.py` | Versioned JSON-to-Markdown renderer; no source requests, secrets, state mutations or posting |
| `.github/workflows/python_version_bump.yml` | Thin weekly/manual runtime proposer and validation pipeline; no self-merge shortcut |
| `.github/workflows/maintenance_merge.yml` | Trusted, review-aware final decision for Dependabot and approved runtime-proposer PRs |
| `.github/workflows/ci.yml` | Read-only validation plus a stable final mandatory gate |
| `.github/dependabot.yml` | Routine updates grouped separately from major/review-required updates |
| `tests/test_maintenance.py` | Selection, risk, exact-head checks, no-write simulations, production-profile and failure-path tests |
| `tests/test_run_summary.py` | Rendering, counters, redaction, partial-run and persistence-status fixtures |
| `tests/test_configuration_contract.py` | Environment consumers, dynamic names, workflow wiring and active-doc consistency |
| `docs/MAINTENANCE.md` | One current policy and operations guide, linked from existing docs rather than copied in full everywhere |

Do not execute commands obtained from a PR's changed maintenance profile in a
privileged job. The merge controller reads the policy from the trusted default
branch. Application validation remains an unprivileged PR-code job.

#### Validation and interface details

- Give the final aggregate check the stable name `maintenance-ci` in both projects.
  It depends on the application, maintenance/config/reporting, lock-consistency
  and mandatory workflow/security checks. Its `always()` implementation succeeds
  only when each mandatory dependency actually succeeded.
- Keep existing application test runners, and have `ci.py` enforce that every
  `tests/test_*.py` runner is registered/executed. Development and production
  profiles share application/maintenance tests; optional documentation checks
  run only where those docs are shipped. A production-layout test must explicitly
  remove the optional docs to prove the boundary.
- YAML parsing and actionlint are mandatory for workflows. Block automatic
  merging on unresolved dependency advisories or failed/unavailable security
  scans, except a reviewed, scoped, expiring waiver. Make relevant high-confidence
  workflow-security findings blocking. Enforce pinned Ruff on new helper/test
  code; enumerate legacy lint debt separately instead of mass-formatting the
  engines or pretending an advisory scan passed. Pin tool versions as well as
  wrapper Action SHAs and record them in the checks.
- Suggested helper interfaces to implement and document: `ci.py --profile
  development|production`, a side-effect-free maintenance decision mode taking
  fixture JSON, and `render_run_summary.py --report PATH --persistence PATH`.
  The decision mode must never fall back to real GitHub writes when a fixture or
  field is missing. Publishing/merging is a separate, explicitly enabled adapter.
- Compile with the fixed command contract, e.g. `python -m piptools compile
  --generate-hashes --allow-unsafe --resolver=backtracking --strip-extras
  --output-file=requirements.txt requirements.in`. Use a fixed
  `CUSTOM_COMPILE_COMMAND` and normalize only generated nondeterministic metadata,
  not package content/hashes. Constrain the dev input against the runtime lock.
  Install with `python -m pip install --require-hashes --only-binary=:all:
  -r requirements.txt`; apply equivalent frozen behavior if retaining uv as the
  installer. The workflow YAML must use block `run` syntax for such commands.
- Retain reviewed immutable Action references. Do not add floating `latest` tool
  resolution or install audit/formatting tools into each monitor execution.
- CI/validation: `contents: read`, no production secrets, checkout credentials
  not persisted. Controller: only needed contents/PR write and checks/statuses/
  Actions read permissions, no PR-head checkout/execution. Publisher: isolate
  BUMP_PAT to its write step; missing credentials are an explicit configuration
  error, not a fallback to a token whose events silently suppress normal PR CI.
- Default to a reviewed allowed merge method and verify the result. A documented
  fallback may try another enabled method after a method-not-allowed response,
  but never bypass a head/check/review failure or log `merged` without confirmation.

### Update policy

Retain the supplied non-secret Variables `AUTO_MERGE_DEPENDABOT=yes` and
`AUTO_MERGE_PYTHON_BUMP=yes`; give them the same meaning in both projects.
Unset/empty/unknown values must not enable automatic merging. Do not retain an
`all` escape hatch that automatically merges a new Python series.

| Update | Automated treatment |
|---|---|
| Stable Python patch within current X.Y | Propose automatically; auto-eligible with `AUTO_MERGE_PYTHON_BUMP=yes` and all gates successful |
| Python next minor | At most the next minor, after the configured/default 30-day soak and full validation; leave for human review |
| Python major, downgrade or forced override | Human-review path; never routine auto-merge |
| Allowlisted stable package patch/minor within an approved major | Auto-eligible with `AUTO_MERGE_DEPENDABOT=yes` after every changed dependency qualifies |
| Package major, prerelease, ambiguous versioning or breaking-risk 0.x minor | Human review |
| Existing Action patch/minor, same verified source and no runtime/security-policy transition | Auto-eligible after full checks; keep SHA pinning |
| Action major, new Action/source, suspicious/moved reference, runner/runtime/permission/trigger change | Human review |
| Security update | Expedite notification and checks, never bypass validation or human-review rules |
| Maintainer hold / changes requested / draft / missing approval | Do not merge automatically |
| Unknown, missing, red, pending, cancelled or skipped mandatory check | Defer/block; no merge |

For grouped updates, the highest-risk member controls the entire PR. Separate
major updates from routine Dependabot groups; do not hide them with ignore rules.
A green result does not override a human-review requirement. Do not infer a safe
version change from a PR title, branch prefix or editable label alone.

### Runtime proposer algorithm

1. Read the current exact pin from `.python-version`; validate a complete numeric
   `X.Y.Z` version. Parse upstream versions numerically, not lexically.
2. Read the setup-python release manifest with bounded requests; require stable
   releases and the actual supported OS/architecture. A Linux arm64 entry is
   not evidence of an x64 build. Reject malformed/prerelease candidates.
3. Prefer the newest patch in the current series. If none exists, consider only
   the next minor under the human-review/soak policy. No multi-series leap.
4. An unavailable release date cannot silently bypass the soak. Report
   `deferred: release-date-unavailable`. Distinguish this from `up-to-date`.
5. Manual override values still require syntax, installability and risk checks;
   they do not turn an unreviewed migration into an auto-eligible patch.
6. Install the exact candidate in a secret-free job; assert the actual interpreter
   equals it. Validate prebuilt wheels against the committed runtime graph, then
   execute the same CI adapter on the rewritten candidate tree. Do not silently
   compile a missing wheel from source or float to unrelated package upgrades.
7. Only documented runtime files may change. Production without dev documentation
   must work; absent optional docs are not an error. No blanket regex replacements
   in tests, README or historical records.
8. Publish/update one deterministic proposal per candidate, using the existing
   BUMP_PAT only in the trusted publisher. Empty diffs/no new candidate create no
   PR. Never execute candidate dependencies with persisted write credentials.
9. Do not self-merge in the proposer. Let ordinary PR CI and the common controller
   decide on the actual latest PR head. A successful pre-PR test is useful but is
   not a substitute for final-head validation.
10. Report `up-to-date`, `deferred`, `proposed`, `review-required`, `merged` or
    `failed`, with a reason, candidate, source SHA, check outcomes and PR link.

### Trusted merge controller

Use a trusted-base, no-PR-code-execution controller. Trigger reevaluation when
trusted CI completes and when the relevant PR state/labels/reviews change;
verify event association through the API. Avoid an eight-minute polling loop
being the only chance to merge a PR whose checks finish later.

Required gates, all checked again immediately before a merge:

- Expected repository/default target, trusted updater identity and expected
  proposal provenance. A matching branch name alone is not authorization.
- Open, non-draft PR; no maintainer hold or changes-requested review; approval
  requirements satisfied. Human-review classifications stay for the maintainer.
- Structural diff validation: approved version/lock changes only. A change to a
  workflow `run`, trigger, permission, checkout ref or policy is not routine just
  because the filename is a workflow. Allow the generated package hashes, not
  arbitrary source edits mixed into a dependency PR.
- The exact expected CI workflow/job set has completed successfully for the latest
  PR head and its tested base/merge-ref association. Include configured legacy
  commit statuses. Verify trusted check identity, not name alone. Zero checks,
  an unrelated green check, or a skipped/neutral mandatory check is insufficient.
- A stable final gate aggregates all mandatory checks without depending on the
  merge controller itself. No circular dependency; no cancelled/stale-run pass.
- Blocking security/workflow findings are visible to the decision. Truly optional
  advisory results remain explicitly labeled advisory, not silently called clean.
- Refresh the head and mergeability; merge only the validated head, respecting
  repository rules. Verify the API response actually says merged. API failures,
  timeouts, unexpected responses or head changes fail closed with a clear reason.
- Do not force-update main, bypass review, escalate through a fallback credential,
  or treat a missing required test as an optional skipped job.

Use the built-in scoped token for read-only/check/merge duties where supported;
reserve the existing BUMP_PAT for the publisher that changes workflow/runtime
files. No new secret value should be requested from the maintainer in chat.
Run fixtures/no-write decision mode before enabling the real controller.

### Logging and summary schema

Produce a bounded, versioned run-report JSON at an internal path under
`RUNNER_TEMP`, then render it after the persistence step in an `always()` footer.
Use the same schema and renderer in both projects, with project-specific
instrumentation. Do not add a new user-configurable knob for every counter.

Required fields:

- `schema_version`, workflow mode, actual checked-out code SHA captured before
  execution, actual Python version, dependency-lock digest, runner image;
- execution result: `completed`, `degraded`, `failed` or `not-run`;
- configured/attempted/usable targets; request count separately from unique target
  count; feeds parsed separately from successful HTTP responses;
- posted/edited/skipped/held outcomes and bounded, named reason counters;
- hosts actually attempted/selected; HTTP status, challenge/invalid feed,
  timeout/rate-limit and selection cancellation kept distinct;
- local save, commit and remote push: `pushed`, `unchanged`, `failed`, `not-run`;
- setup/monitor/persistence duration separately; actionable warnings and errors.

No new source requests, cold-fallback probes, sleeps, retries, altered concurrency
or changed posting order for reporting. Do not label a quiet account stale just
from its last-post age. Do not label an unavailable listing deleted. Do not treat
race cancellation as a proven dead host. Do not count log lines as posts.

Redact webhook tokens, Authorization, cookie values, token-bearing URLs and
secret values before logging/serialization. Do not dump catch-all environment or
secret blobs. Bound IDs/reason samples and avoid storing complete post bodies.
A missing report after an early failure is `unavailable`, not fake zero activity.
Failure to write optional telemetry must not resend a card or mask the original
application failure. Render once from recorded data; measure overhead rather
than promising an arbitrary “peak performance” number.

### Full-sweep documentation/configuration rules

- Check every active configuration name from its runtime reader through workflow
  wiring, empty-string/default handling, `.env.example` and active docs.
- Treat generated names, aliases and deliberately supported fallback engines as
  real consumers. A literal grep miss is not evidence a setting is unused.
- Remove an obsolete setting from active docs only after proving the consumer is
  gone. Do not delete a repository Secret/Variable through an API in this task.
- Keep retired behavior in dated history; remove stale recommendations from the
  current guide. Do not mass-rewrite historical version numbers, incident records
  or template/example Markdown links.
- Keep README short: purpose, operation, configuration entry point, tests,
  maintenance policy and links. Move detailed policy to the canonical guide,
  not duplicate slightly different copies.
- Update AGENTS with current topology, exact safe test commands, protected behavior,
  common helpers and the explicit no-Actions-lockfiles decision. Replace stale
  “latest round”/version claims only where the document claims to be current.
- Update `.gitignore` narrowly for local secret variants and generated scratch
  reports/caches. Never ignore all JSON, delete tracked state, or untrack caches
  needed by the existing persistence workflow.
- Keep notices, licenses, attribution and valid operational history. Do not
  delete maintained code or legal docs merely because this PR does not execute it.

### Mandatory acceptance tests for the new implementation

Baseline tests alone do not satisfy these unchecked requirements:

- [ ] Existing application suites and golden payloads pass without changing
      expected posting, routing, ping, dedup, media or state behavior.
- [ ] Summary fixtures cover timestamps, repeated feed attempts, real numeric post
      totals, zero activity, absent logs, partial failures and unavailable data.
- [ ] HTTP-200 challenge != usable feed; cancellation != failed host; counts and
      host names are truthful and bounded; no extra network/post calls.
- [ ] State saved locally followed by push failure is reported as push failure.
- [ ] Secret-redaction tests cover raw and encoded token/query values, exception
      messages and catch-all config; report generation failure cannot repost.
- [ ] Numeric patch ordering includes 3.15.9 vs 3.15.10; candidate fixtures cover
      wrong architecture, prereleases, malformed values, missing release dates,
      unavailable wheels, override/downgrade and no-candidate cases.
- [ ] Development and documentation-free production profiles use the same helpers
      without modifying docs/history or requiring missing development files.
- [ ] Mixed-major groups, unknown versions, source identity/permission changes and
      explicit maintainer holds become review-required, even with green tests.
- [ ] Missing/skipped/neutral/unrelated/foreign checks, legacy-status failure,
      delayed checks, API errors, false merged response and changed head block.
- [ ] PR CI, runtime candidate validation and the final gate run the same complete
      application/test command set; adding a test file cannot silently omit it.
- [ ] Dependency generation is reproducible; frozen installs verify hashes and do
      not resolve new runtime versions; Dependabot regenerates supported locks.
- [ ] Workflow YAML parses and passes the chosen pinned validator. SHA pinning,
      least privilege, timeouts, triggers and no-secret PR execution are checked.
- [ ] No Actions lockfile/tool/policy, extra monitor schedule, PR creation during
      validation, production push, state reset or Discord test-card call occurs.
- [ ] Safe hosted validation is rerun on the actual completed PR head. If a check
      fails, fix the cause and rerun; never erase or weaken an assertion to get green.

Run the merge controller against mocked API fixtures and in no-write decision
mode. Do not test automatic merging by merging a real production update. A later
maintainer-approved ordinary update can confirm the deployed path operationally.

## Implementation sequence and completion definition

1. Add the shared policy/CI helpers and negative regression fixtures first. Keep
   application outcomes unchanged while fixing the reproduced maintenance bugs.
2. Generate the runtime/dev locks and exact pin; prove frozen installs on the
   supported runner before replacing the current installation steps.
3. Replace duplicate proposer/merge code atomically. Test decisions without
   writes; do not leave both old and new final controllers active.
4. Integrate bounded reporting and the post-persistence footer. Test failure,
   cancellation, missing-log and redaction paths, not only a successful run.
5. Reconcile all active docs/config examples against real consumers. Preserve
   history, fixtures, source behavior and independent production state.
6. Rerun safe hosted validation on the completed implementation head and report
   exact versions, hashes and results. The pinned historical audit above does
   not automatically validate later code. No checkbox becomes complete merely
   because that baseline was green.

The change is ready only when the implementation's acceptance checks pass, the
maintainer can identify every altered behavior, and no development-only document
is needed by runtime maintenance. A documentation-only change is a delivered
specification, **not** the completed maintenance upgrade.

## Complete tracked-file disposition index

This index accounts for every file in the reviewed source snapshot. New files
are listed in the implementation contract above. `Review wording` is not a
license to rewrite preserved behavior/history; change only a proven stale active
instruction, otherwise retain it. `Preserve/test` means it remains a regression
boundary, not that this audit certifies every possible code path.

| Existing path | Planned disposition |
|---|---|
| `.env.example` | Modify as specified above |
| `.github/dependabot.yml` | Modify as specified above |
| `.github/scripts/merge_monitor_caches.py` | Preserve/test; no unrelated behavior change |
| `.github/workflows/ci.yml` | Modify as specified above |
| `.github/workflows/dependabot_auto_merge.yml` | Remove after unified controller replaces it |
| `.github/workflows/python_version_bump.yml` | Modify as specified above |
| `.github/workflows/reddit_monitor.yml` | Modify as specified above |
| `.github/workflows/twitter_monitor.yml` | Modify as specified above |
| `.gitignore` | Modify as specified above |
| `AGENTS.md` | Modify as specified above |
| `PRIVACY_POLICY.md` | Preserve substantive legal content |
| `README.md` | Modify as specified above |
| `TERMS_OF_SERVICE.md` | Preserve substantive legal content |
| `docs/CHANGELOG.md` | Append implemented-change entry; preserve history |
| `docs/CI_SMOKE.md` | Modify as specified above |
| `docs/DEPENDABOT.md` | Modify as specified above |
| `docs/DISCOHOOK.md` | Review current wording/navigation; retain valid content |
| `docs/PYTHON_RUNTIME.md` | Modify as specified above |
| `docs/REDDIT_VIDEO_MEDIA_REPORT.md` | Review current wording/navigation; retain valid content |
| `docs/REDDIT_VIDEO_QUALITY.md` | Review current wording/navigation; retain valid content |
| `docs/REPOSITORY_TRACKING.md` | Modify as specified above |
| `docs/VIDEO_ONLY_QUALITY_POLICY_CONFIRMATION.md` | Review current wording/navigation; retain valid content |
| `docs/history/CHANGELOG_ARCHIVE.md` | Preserve dated historical record |
| `docs/history/ENGINE_HISTORY.md` | Preserve dated historical record |
| `docs/history/PENDING_CACHE_AUDIT_2026-10-12.md` | Preserve dated historical record |
| `docs/history/README.md` | Preserve dated historical record |
| `docs/history/REPOSITORY_TRACKING_2026-10-01.md` | Preserve dated historical record |
| `docs/history/ROUND_46.md` | Preserve dated historical record |
| `docs/history/ROUND_46B.md` | Preserve dated historical record |
| `docs/history/ROUND_49.md` | Preserve dated historical record |
| `docs/history/ROUND_49_REPLAY_TESTS.md` | Preserve dated historical record |
| `docs/history/ROUND_50.md` | Preserve dated historical record |
| `docs/history/ROUND_51.md` | Preserve dated historical record |
| `docs/history/ROUND_53.md` | Preserve dated historical record |
| `docs/history/ROUND_54.md` | Preserve dated historical record |
| `docs/history/ROUND_55.md` | Preserve dated historical record |
| `docs/history/ROUND_56.md` | Preserve dated historical record |
| `docs/history/ROUND_57.md` | Preserve dated historical record |
| `docs/history/ROUND_59.md` | Preserve dated historical record |
| `docs/history/ROUND_60.md` | Preserve dated historical record |
| `docs/history/ROUND_61.md` | Preserve dated historical record |
| `docs/history/ROUND_61_DEPLOY.md` | Preserve dated historical record |
| `docs/history/ROUND_67.md` | Preserve dated historical record |
| `docs/history/ROUND_68.md` | Preserve dated historical record |
| `docs/history/ROUND_69.md` | Preserve dated historical record |
| `docs/history/ROUND_70.md` | Preserve dated historical record |
| `docs/history/ROUND_71.md` | Preserve dated historical record |
| `docs/history/ROUND_72.md` | Preserve dated historical record |
| `docs/history/ROUND_73.md` | Preserve dated historical record |
| `docs/history/ROUND_74.md` | Preserve dated historical record |
| `docs/history/ROUND_75.md` | Preserve dated historical record |
| `docs/history/ROUND_76.md` | Preserve dated historical record |
| `docs/history/round-15-validation.md` | Preserve dated historical record |
| `pending_reddit.json` | Preserve independent runtime state; never copy/reset |
| `posted_reddit.json` | Preserve independent runtime state; never copy/reset |
| `posted_tweets.json` | Preserve independent runtime state; never copy/reset |
| `proxy_health.json` | Preserve independent runtime state; never copy/reset |
| `requirements.txt` | Modify as specified above |
| `testing area/reddit_main.py` | Preserve/test; no unrelated behavior change |
| `testing area/reddit_main_v2_embedez.py` | Preserve/test; no unrelated behavior change |
| `testing area/reddit_main_v3.py` | Modify as specified above |
| `testing area/reddit_proxy.py` | Preserve/test; no unrelated behavior change |
| `testing area/reddit_signals.py` | Preserve/test; no unrelated behavior change |
| `testing area/twitter_proxy.py` | Preserve/test; no unrelated behavior change |
| `testing area/twitter_v1.py` | Preserve/test; no unrelated behavior change |
| `testing area/twitter_v2_button_outside.py` | Preserve/test; no unrelated behavior change |
| `testing area/twitter_v3.py` | Modify as specified above |
| `testing area/video_diag.py` | Preserve/test; no unrelated behavior change |
| `tests/fixtures/posted_cards.py` | Preserve regression fixture |
| `tests/test_reddit_signals.py` | Preserve/test; no unrelated behavior change |
| `tests/test_smoke.py` | Modify as specified above |
| `tests/test_twitter_media.py` | Preserve/test; no unrelated behavior change |


### Audit provenance and limits

The live audit tooling is `.github/scripts/maintenance_review_audit.py` and
`.github/workflows/maintenance_review.yml` in the News review branch at commit
`2adbe5e7e8e3faf46fc691d7d5a98b6fbc1ed21b`. Its successful check annotations expose
source SHAs, inventory digests, package/runtime versions, command exit codes and
reproduced findings. These one-off diagnostics are **not** part of the production
copy manifest and should not become another scheduled maintenance system.

No source-endpoint health, authenticated token path, future runtime release,
future package graph, real webhook delivery or production merge is certified by
this offline baseline. Previously collected hosted mirror observations remain
dated evidence, not permission to remove or reorder hosts in this update.

API-version reference:
https://docs.github.com/en/rest/about-the-rest-api/api-versions?apiVersion=2026-03-10

Respect the maintainer's decisions: separate project specifications, no PR
created by this review, no Actions lockfiles, no production secrets/settings
changes, and no personal next-step instruction file beyond these specifications.
