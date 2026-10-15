# Game-Express — complete maintenance update specification

**Prepared:** 2026-10-15 (Asia/Manila)

**Target:** `uesu/Game-Express`

**Status:** implementation specification, not an already-applied application
update. The hosted baseline evidence below is real; proposed fixes and new
acceptance tests must still be implemented and rerun on the final PR head.

This is a standalone Game-Express plan, including the PR title/body, complete
add/modify/remove responsibilities, shared automation contract, logging design,
configuration/doc cleanup and acceptance criteria. It intentionally keeps the
maintenance structure aligned with News-Express without importing its runtime
code or forcing its monitor layout onto Game. No PR, deployment or production
state change was made for this audit.

## PR title

```text
Maintenance: unify safe updates, pin the Game runtime, and report source and persistence outcomes accurately
```

## PR body

Use this body for the **implementation PR**, not a Markdown-only PR claiming the
code is finished. Update unchecked items only after the corresponding work passes.

```markdown
## Summary
Implement consistent, review-aware maintenance without changing Game-Express
cards, source selection, timing, state, routing or pings. Use the same maintenance
contract as News-Express while keeping the applications independent.

## Scope
- [ ] Replace the floating Python series with one tested exact runtime pin.
- [ ] Generate hashed runtime dependencies and use them in CI and production.
- [ ] Fix numeric version selection, architecture checks and candidate policy.
- [ ] Extract tested maintenance helpers and one shared CI command adapter.
- [ ] Move all final merge decisions to one trusted, fail-closed controller.
- [ ] Separate HTTP success, parsed/usable feeds, selected hosts and cancellations.
- [ ] Report the checked-out code SHA and actual final state-push result.
- [ ] Reconcile README, AGENTS, environment examples and all active guides.
- [ ] Preserve source fleets, schedules, cards, fan-out, codes, media and dedup.
- [ ] Do not add Actions workflow lockfiles or change the external scheduler.

## Evidence already available
- Hosted baseline: https://github.com/uesu/News-Express/actions/runs/38732934814
- The fixed Game snapshot passed compile, validate, three test suites and offline
  preview generation on Python 3.14.8. All 127 tracked files were inventoried.
- Numeric patch ordering and wrong-architecture selection gaps were reproduced;
  the audit confirms existing behavior, not that the proposed repairs are done.

## Required implementation validation
- [ ] Existing tests/golden payloads pass plus maintenance/report/config fixtures.
- [ ] Runtime and dependency selection, negative checks and review holds pass.
- [ ] Source telemetry is truthful and adds no network requests or posting.
- [ ] Failed final push cannot be summarized as successful persistence.
- [ ] Lock regeneration/frozen installation and the final CI gate are verified.
- [ ] Safe hosted checks pass on this actual completed PR head.
- [ ] No webhook check/test-card call, live run, state reset or real test merge.

## Deployment and rollback
Keep workflow_dispatch and cron-job.org unchanged. Roll back application,
workflows, runtime pin and dependency lock together if necessary, preserving
state/state.json and repository secrets/settings. Never replay posts to test a
maintenance rollback.
```

## Reviewed baseline and live evidence

- Repository: `uesu/Game-Express`.
- Source commit: `e6bb42ab26fa0a8f7601b4200a1e1f784c7a431f`.
- Coverage: **127 files**, **1,391,380 bytes**, every tracked file read and hashed.
- [Hosted audit run 38732934814](https://github.com/uesu/News-Express/actions/runs/38732934814):
  all four repository jobs succeeded; Game's commands all exited 0:

```bash
python -m compileall -q gamexpress tests .github/scripts
python -m gamexpress validate
python tests/test_smoke.py
python tests/test_schedule_epithet_and_settled.py
python tests/test_gachawiki_placeholder.py
python -m gamexpress preview --out /tmp/maintenance-audit-previews
```

The preview command used sample/payload generation, not a webhook. The audit did
not run `run`, `test-card` or `check-webhooks`. No post/ping/production state push
was used as a diagnostic.

The current `3.14` series request resolved to **3.14.8**. Runtime packages resolved
to **aiohttp 3.14.5**, **feedparser 6.0.14**, **python-dotenv 1.2.4**; audit-only
PyYAML was 6.0.3. The runner was GitHub-hosted Ubuntu 24, image `20261012.334.1`.
This proves those current combinations passed the listed tests, not that a
floating series/range always resolves to the same interpreter/package graph.

Python AST and JSON parsing reported no errors. Environment/read-site and
Markdown-link scans covered the complete tree, accompanied by focused workflow,
maintenance, reporting, configuration and documentation review. A single scanned
Markdown link candidate was a historical changelog placeholder, not proof of a
broken current link. File coverage does not mean all future behavioral edge
cases are proven or that unused code can safely be deleted by grep alone.

The first audit launch, run `38732818668`, failed YAML validation before tests
because a colon-bearing pip argument needed a block `run` value. It was corrected
and parsed locally; the successful run above replaces that failed launch. This
was not a Game application failure.

This baseline did not execute the future implementation or an actual updater PR/
merge. Earlier weekly green runs with skipped upgrade/proposal/merge stages are
also not evidence of that end-to-end path.

### Confirmed issues to fix

| Finding | Evidence/meaning | Required correction |
|---|---|---|
| Lexical patch comparison | Current helper selected 3.15.9 over 3.15.10 in the fixture | Numeric version tuples, stable-only validation |
| Incomplete platform qualification | Arm64-only Linux candidate passed selection for an x64 workflow | Require the actual OS/architecture before proposing |
| Inconsistent candidate policy | Floating series, no equivalent next-minor/soak contract | Exact pin, current-series patch first, reviewed next minor with known age |
| Split final merge responsibility | Runtime proposer and Dependabot-in-CI have separate decision paths | One trusted final controller with final-head PR checks |
| Weak merge/result policy | Required `test` alone does not establish all risk/security gates; merge response needs verification | Full expected-set/risk/hold policy and explicit merged result check |
| Advisory vs blocking ambiguity | pip-audit/actionlint/zizmor/ruff paths are not all blocking today | Clearly define mandatory findings and make the final gate reflect them |
| HTTP `ok` is not usable RSS | Transport success can be followed by invalid/challenge/non-feed content | Track HTTP, parsing and selected-feed outcomes separately |
| Summary precedes remote persistence | `runner.write_summary` runs before the workflow's git-push step | Always-run final footer after persistence, including failure paths |
| Stale runtime-update prose | Docs describe built-in-token/no-normal-CI behavior while workflow uses BUMP_PAT | Describe the actual proposer/controller/CI architecture consistently |

Explicitly elevated workflow permissions for Dependabot are supported by GitHub;
do not “fix” that by asserting they are inherently impossible. The issue is the
complete trust, validation and merge contract, not a blanket token myth.

## Game-specific implementation work

### Add

Add the common files specified below, `.python-version`, dependency inputs/
generated locks and maintenance/report/config tests. The existing
`.github/scripts/python_version_bump.py` becomes a thin adapter, not a second
independent policy implementation. Add offline fixtures under
`tests/fixtures/maintenance/` for versions/platforms, synthetic check/status/review
API responses and source/report outcomes. Do not copy actual state or secrets.

### Modify application/workflow code narrowly

| File | Required change |
|---|---|
| `.github/workflows/ci.yml` | Exact pin/frozen install, common CI adapter, explicit blocking/advisory split and stable final gate; remove embedded auto-merge job after replacement |
| `.github/workflows/python_version_bump.yml` | Small selection/secret-free validation/trusted publication stages; no self-merge path |
| `.github/scripts/python_version_bump.py` | Delegate numeric/architecture/soak/risk policy to the shared helper; preserve a clear CLI and no-write test mode |
| `.github/workflows/monitor.yml` | Exact pin/frozen dependencies, actual code SHA captured before execution, report path and `always()` final persistence footer; preserve current dispatch/schedule/state behavior |
| `.github/dependabot.yml` | Compatible generated package-lock updates; separate routine from major/review-required groups; no Actions-lock integration |
| `.github/zizmor.yml` | Review narrowly justified suppressions against the new workflow topology; do not blanket-disable findings to get green |
| `gamexpress/http.py` | Keep transport counters honest; add typed outcome recording/redaction without changing requests, retries, cache or concurrency |
| `gamexpress/sources/twitter.py` | Record parsed/usable/selected outcomes at the parse/selection layer, where HTTP success alone is insufficient; no host reorder or new probes |
| `gamexpress/runner.py` | Bounded structured result report and reliable exception-path emission; stop presenting a pre-push summary as final persistence success |
| `gamexpress/__init__.py` | If build identity is emitted here, prefer the captured checked-out code SHA; preserve local fallback/version behavior |
| `.env.example` | Match real dynamic readers/defaults and new auto-merge semantics; distinguish posting test mode from genuinely safe preview/dry-run |
| `.gitignore` | Add `.env.*` with `!.env.example` and narrow report/scratch patterns; preserve tracked state and existing preview/temp protections |
| `ruff.toml` | Keep target-version consistent with the approved runtime series, not independently floating; only change settings required by the new helpers |
| `tests/test_smoke.py` | Preserve domain assertions; adjust maintenance-topology assumptions only when the deliberate design changes them |

The shared report schema does not justify a new global configuration framework.
Use the existing configuration readers unless a concrete stale-consumer bug is
proven; dynamic webhook, role and emoji resolution must remain compatible.

### Remove/replace

- Remove the old Dependabot auto-merge job from `ci.yml` once
  `maintenance_merge.yml` replaces it. Do not keep duplicate final controllers.
- Remove self-merge decisions from the runtime proposer and the old lexical
  selector/any-Linux-platform shortcut, replacing them with tested shared logic.
- Remove a floating `3.14` runtime setup wherever it controls production/current
  CI. Preserve references that are explicitly historical or describe a series.
- Remove current instructions claiming the built-in token is the proposer token,
  that normal PR CI need not run, or that `all` is a safe general merge policy.
- Remove misleading labels that equate request-level HTTP `ok` with a healthy
  feed/host. Retain useful transport counts, correctly named.
- Do not remove any scraper, dormant/prepared game, fallback host, fixture,
  placeholder-handling rule, dynamic env alias or historical report merely to
  reduce file count. No source-domain deletion is authorized by this audit.

### Current documentation cleanup, file by file

| File | Required disposition |
|---|---|
| `README.md` | Concise setup/features/config/reliability/test overview; link canonical maintenance guide; explain exact pins and safe versus posting commands |
| `AGENTS.md` | Current test/topology contract and helper interfaces; preserve card/schedule/code invariants; no Actions locks and no live-posting validation |
| `docs/PYTHON_VERSION.md` | Exact pin, numeric/platform selection, candidate/soak policy, BUMP_PAT publisher, normal PR CI and trusted final merge controller |
| `docs/DEPENDABOT.md` | Routine/review groups, frozen package graph, expected checks/holds, no security bypass and truthful merge-result reporting |
| `docs/CONFIGURATION.md` | Canonical env reader/default/wiring table, dynamic names/aliases and `yes` patch-only auto-merge meaning; no unsupported setting deletion |
| `docs/TESTING.md` | Same CI command adapter, existing suites, new failure-path tests, offline preview and explicit warnings for commands that send messages |
| `docs/SECURITY.md` | Least privilege, secret-free validation, redaction and trusted controller; correct token semantics without asking for new values |
| `docs/SCHEDULER.md` | Preserve cron-job.org dispatch, input defaults and valid API version; distinguish request accepted from monitor completed |
| `docs/PROD-REPO-SETUP.md` | Exact runtime/lock/helper deployment manifest and state/secret preservation; do not require development-only docs in runtime workflows |
| `docs/ROLLOUT.md` | Acceptance gates, code/lock/workflow rollback together, no state rewind and no test-card deployment verification |
| `docs/TROUBLESHOOTING.md` | New status/reason taxonomy; transport versus usable-feed and local-save versus pushed-state diagnosis |
| `docs/SOURCES.md` | Preserve source order/policy; clarify fallback/selection/transport labels without claiming every host is currently healthy |
| `docs/ACCURACY.md` | Preserve announcement/evidence and timestamp rules; maintenance reporting must not weaken them |
| `docs/TIMESTAMP-PATTERNS.md` | Preserve parsing patterns and evidence boundaries; update navigation only if needed |
| `docs/BANNER_DATABASE.md` | Preserve source/data/schema contract and placeholders; no banner-source migration in this PR |
| `docs/CREDITS.md` | Keep attribution and valid links; do not erase a source's credit because it was not selected in one run |
| `docs/README.md` | Update navigation to canonical maintenance/testing/config guides without repeating policy blocks |
| `docs/changelog/CHANGELOG.md` | Add a dated implemented-change entry with real test evidence and preserved behavior; no invented product release number |
| `docs/changelog/README.md` | Keep current/archive navigation accurate |
| `docs/changelog/CHANGELOG_ARCHIVE.md` | Preserve historical facts/version/token behavior as history, not current instructions |
| `PRIVACY_POLICY.md`, `TERMS_OF_SERVICE.md` | Preserve substantive legal text; no unsupported new privacy commitments |

### Environment inventory and dynamic names

The supplied secret/non-secret inventories and both screenshots were received;
do not ask the maintainer to re-enter tokens. The configuration audit must follow
`Config.webhook`/mirror/ping resolution and the generated `EMOJI_{...}` reader.
These examples lack a full literal occurrence in some source scans but are valid
dynamic names, **not deletion candidates**:

- `DISCORD_WEBHOOK_SCHEDULE_WUWA`;
- `DISCORD_WEBHOOK_SCHEDULE_MIRROR` and `_MIRROR_ZZZ`;
- `PING_SCHEDULE_GENSHIN`;
- `EMOJI_YOUTUBE`, `EMOJI_TWITCH`, `EMOJI_SOURCE`, `EMOJI_REDEEM`.

Preserve short game aliases, per-game > feature > catch-all routing, mirror
fan-out behavior and silent mirror copies. Keep `NO_PING`, `FORCE_WEBHOOK` and
supported test/local settings accurately documented; do not execute them as a
live diagnostic. `TEST_MODE` does not mean “cannot send”: preview generation is
safe, whereas test-card/webhook-check commands can send.

No `NITTER_INSTANCES` override was shown in the supplied Game inventory. Preserve
the built-in fleet and the optional override capability; do not invent an
existing override or populate one based on one hosted probe result.

### Required Game report behavior

- Show HTTP results as request outcomes, not a count of healthy mirrors. An
  example `Nitter ok: 18` cannot mean 18 usable feeds or 18 distinct good hosts.
- Record parse-valid, usable-for-target, selected, rate-limited, timed-out,
  challenge/non-feed and cancelled-after-selection separately, at the appropriate
  HTTP and parser layers. Count unique hosts separately from total requests.
- Show which hosts were actually used; label lower-priority unused hosts
  `not-needed`, not tested-good/tested-bad. Do not probe them just to fill a table.
- Preserve benign no-new-items, silent seed, disabled feature, pending official
  evidence, future/placeholder banner and unchanged-card outcomes.
- Keep local state save and remote git push separate. The workflow footer must
  reflect a push conflict/failure even if `runner.write_summary` ran successfully.
- Capture the actual checked-out code SHA before execution, not simply the event
  SHA or a later state-only commit. Expose it in logs and the summary without
  changing Discord card payloads or announcement matching.

### Protected domain areas

Preserve `schedule.py`, cards/codeposting/Discord payload generation, models,
media, state, time/text parsing, prepared-game defaults, source priority and all
current config JSON semantics. Reporting instrumentation in `http.py`, the X
source and `runner.py` must not alter call order or interpretation. Existing
schema/golden-payload/settled-epithet/gachawiki tests are regression guardrails,
not candidates to rewrite to accept unrelated changed behavior.

Do not overwrite `state/state.json` with a development, sample or test state.
Preserve `state/.gitkeep` and ignore only appropriate temporary/corrupt backups.
Rollback reverts code, automation and dependency graph together, not posted IDs.

## Scheduler, credentials and settings: preserve working setup

Keep the existing cron-job.org dispatch job, headers and payload. In particular,
`X-GitHub-Api-Version: 2026-03-10` is supported and a read-only request using it
succeeded. Keep the existing authentication scheme, Accept and JSON Content-Type;
no speculative API downgrade or extra built-in monitor schedule is needed.
A successful dispatch request is not a successful application run.

Retain the existing BUMP_PAT for the trusted runtime publisher and keep normal
CI secret-free. The shown fine-grained token has metadata read plus contents/PR/
workflow write; that does not establish Actions-dispatch permission. Keep the
working dispatch token and role/webhook secrets, and never log their values.
Later limiting token repository access/expiry is optional separate hardening,
not a required rotation because permission metadata appeared in a screenshot.

Do not change repository rules to make a merge succeed. Some protection/settings
reads returned 403, which is unknown visibility, not evidence that protection is
absent. Validate exact permissions and rules when the maintainer reviews the
implementation, rather than silently granting broader rights.

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
| `.github/scripts/python_version_bump.py` | Modify as specified above |
| `.github/workflows/ci.yml` | Modify as specified above |
| `.github/workflows/monitor.yml` | Modify as specified above |
| `.github/workflows/python_version_bump.yml` | Modify as specified above |
| `.github/zizmor.yml` | Modify as specified above |
| `.gitignore` | Modify as specified above |
| `AGENTS.md` | Modify as specified above |
| `PRIVACY_POLICY.md` | Preserve substantive legal content |
| `README.md` | Modify as specified above |
| `TERMS_OF_SERVICE.md` | Preserve substantive legal content |
| `config/games.json` | Preserve configuration data and semantics |
| `config/overrides.json` | Preserve configuration data and semantics |
| `config/program_announcements.json` | Preserve configuration data and semantics |
| `docs/ACCURACY.md` | Review current wording/navigation; retain valid content |
| `docs/BANNER_DATABASE.md` | Review current wording/navigation; retain valid content |
| `docs/CONFIGURATION.md` | Modify as specified above |
| `docs/CREDITS.md` | Review current wording/navigation; retain valid content |
| `docs/DEPENDABOT.md` | Modify as specified above |
| `docs/PROD-REPO-SETUP.md` | Modify as specified above |
| `docs/PYTHON_VERSION.md` | Modify as specified above |
| `docs/README.md` | Modify as specified above |
| `docs/ROLLOUT.md` | Modify as specified above |
| `docs/SCHEDULER.md` | Modify as specified above |
| `docs/SECURITY.md` | Modify as specified above |
| `docs/SOURCES.md` | Modify as specified above |
| `docs/TESTING.md` | Modify as specified above |
| `docs/TIMESTAMP-PATTERNS.md` | Review current wording/navigation; retain valid content |
| `docs/TROUBLESHOOTING.md` | Modify as specified above |
| `docs/changelog/CHANGELOG.md` | Append implemented-change entry; preserve history |
| `docs/changelog/CHANGELOG_ARCHIVE.md` | Preserve dated historical record |
| `docs/changelog/README.md` | Review current wording/navigation; retain valid content |
| `gamexpress/__init__.py` | Modify as specified above |
| `gamexpress/__main__.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/cards.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/codeposter.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/config.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/discord.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/http.py` | Modify as specified above |
| `gamexpress/media.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/models.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/preview_html.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/runner.py` | Modify as specified above |
| `gamexpress/samples.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/schedule.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/sources/__init__.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/sources/banner_search.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/sources/bannerfeed.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/sources/calendarfeed.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/sources/codes.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/sources/countdown.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/sources/gachawiki.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/sources/hoyolab.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/sources/kuro.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/sources/launcher.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/sources/newspage.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/sources/twitter.py` | Modify as specified above |
| `gamexpress/state.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/textutil.py` | Preserve/test; no unrelated behavior change |
| `gamexpress/timeparse.py` | Preserve/test; no unrelated behavior change |
| `requirements.txt` | Modify as specified above |
| `ruff.toml` | Modify as specified above |
| `state/.gitkeep` | Preserve/test; no unrelated behavior change |
| `state/state.json` | Preserve independent runtime state; never copy/reset |
| `tests/fixtures/bannerfeed_hub_trimmed.json` | Preserve regression fixture |
| `tests/fixtures/codehub_live_trimmed.json` | Preserve regression fixture |
| `tests/fixtures/codehub_trimmed.json` | Preserve regression fixture |
| `tests/fixtures/countdown_gachacountdown_gi.html` | Preserve regression fixture |
| `tests/fixtures/countdown_gengamer_gi_livestream.html` | Preserve regression fixture |
| `tests/fixtures/ennead_genshin_trimmed.json` | Preserve regression fixture |
| `tests/fixtures/ennead_starrail_trimmed.json` | Preserve regression fixture |
| `tests/fixtures/fandom_gi_live_active_codes.json` | Preserve regression fixture |
| `tests/fixtures/fandom_gi_live_trimmed.json` | Preserve regression fixture |
| `tests/fixtures/fandom_hsr_SYNTHETIC.json` | Preserve regression fixture |
| `tests/fixtures/fandom_hsr_live_trimmed.json` | Preserve regression fixture |
| `tests/fixtures/fandom_ww_live_trimmed.json` | Preserve regression fixture |
| `tests/fixtures/fandom_ww_table_SYNTHETIC.json` | Preserve regression fixture |
| `tests/fixtures/fx_genshin_7_1_program.json` | Preserve regression fixture |
| `tests/fixtures/fx_genshin_luna2_program.json` | Preserve regression fixture |
| `tests/fixtures/fx_starrail_4_5_program.json` | Preserve regression fixture |
| `tests/fixtures/fx_starrail_4_6_program.json` | Preserve regression fixture |
| `tests/fixtures/fx_wuwa_3_7_broadcast.json` | Preserve regression fixture |
| `tests/fixtures/fx_zzz_2_5_program.json` | Preserve regression fixture |
| `tests/fixtures/fx_zzz_3_2_program.json` | Preserve regression fixture |
| `tests/fixtures/fx_zzz_3_3_channels_phase1.json` | Preserve regression fixture |
| `tests/fixtures/fx_zzz_3_3_channels_phase2.json` | Preserve regression fixture |
| `tests/fixtures/gachawiki/banner_genshin_surging_ballad.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/banner_genshin_unannounced.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/banner_genshin_warm_winds.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/banner_starrail_pearl.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/banner_wuwa_tonight.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/banner_zzz_bloodmoon.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/banner_zzz_cindernight.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/version_genshin_7_1.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/version_starrail_4_6.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/version_wuwa_3_7.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/version_zzz_3_1.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/version_zzz_3_2.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/version_zzz_3_3.wiki` | Preserve regression fixture |
| `tests/fixtures/gachawiki/version_zzz_3_3_early.wiki` | Preserve regression fixture |
| `tests/fixtures/golden/schedule_genshin.json` | Preserve regression fixture |
| `tests/fixtures/golden/schedule_starrail.json` | Preserve regression fixture |
| `tests/fixtures/golden/schedule_wuwa.json` | Preserve regression fixture |
| `tests/fixtures/golden/schedule_zzz.json` | Preserve regression fixture |
| `tests/fixtures/hoyolab_genshin_46604275_full.json` | Preserve regression fixture |
| `tests/fixtures/hoyolab_genshin_list_update_details.json` | Preserve regression fixture |
| `tests/fixtures/hoyolab_material_empty.json` | Preserve regression fixture |
| `tests/fixtures/hoyolab_material_live_SYNTHETIC.json` | Preserve regression fixture |
| `tests/fixtures/hoyolab_starrail_46814308_full.json` | Preserve regression fixture |
| `tests/fixtures/hoyolab_starrail_newslist_program.json` | Preserve regression fixture |
| `tests/fixtures/hoyolab_zzz_46604530_full.json` | Preserve regression fixture |
| `tests/fixtures/hoyolab_zzz_46863847_full.json` | Preserve regression fixture |
| `tests/fixtures/hoyoplay_branches_trimmed.json` | Preserve regression fixture |
| `tests/fixtures/humbao_genshin.txt` | Preserve regression fixture |
| `tests/fixtures/kuro_launcher_index_trimmed.json` | Preserve regression fixture |
| `tests/fixtures/newspage_hsr_article.html` | Preserve regression fixture |
| `tests/fixtures/newspage_hsr_news.html` | Preserve regression fixture |
| `tests/fixtures/ogc_genshin_trimmed.json` | Preserve regression fixture |
| `tests/fixtures/ogc_starrail_trimmed.json` | Preserve regression fixture |
| `tests/fixtures/ogc_wuwa.json` | Preserve regression fixture |
| `tests/fixtures/seria_nap.json` | Preserve regression fixture |
| `tests/fixtures/wuthering_gg_SYNTHETIC.html` | Preserve regression fixture |
| `tests/fixtures/ww_articles_latest.xml` | Preserve regression fixture |
| `tests/test_gachawiki_placeholder.py` | Preserve/test; no unrelated behavior change |
| `tests/test_schedule_epithet_and_settled.py` | Preserve/test; no unrelated behavior change |
| `tests/test_smoke.py` | Modify as specified above |


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
