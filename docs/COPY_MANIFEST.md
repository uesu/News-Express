# Shared file manifest — News-Express proposal heads

This is a **development-side** review document. It is not a runtime input.
`production_copy_exclude` lists `docs/`, so production copies must not require
this file. Correction handoffs and `NEWS_EXPRESS_UPDATE.md` are development-side
only and must not become required runtime inputs.

Machine-readable SHA-256 values for the **immutable proposal commits** live in
[`proposal_head_hashes.json`](proposal_head_hashes.json). That artifact hashes
file bytes at those commits. It does **not** hash itself, this document, or a
later docs-only commit. A commit cannot embed its own final self-hash.

The runtime file lists live in `.github/maintenance.json`:

* `runtime_files` — files a documentation-free production copy still needs
* `production_copy_exclude` — docs, onboarding, and **caches that must never
  be overwritten**
* `optional_docs` — present in this development tree; omitted in production

Do not blindly copy another instance's state, secrets, or caches. Do not force
Game's runtime layout onto News or vice versa.

## Exact proposal heads reviewed 2026-10-16 (Asia/Manila)

These are the implementation PRs under acceptance, **not** deployed `main`
cache snapshots.

| Role | Repository | PR | Git SHA |
|---|---|---|---|
| News development | `uesu/News-Express` | [#66](https://github.com/uesu/News-Express/pull/66) | `be4bacaa0e4a1688517549c99915d93d0227024e` |
| Reddit production proposal | `uesu/7jkxmy9nvbc` | [#2](https://github.com/uesu/7jkxmy9nvbc/pull/2) | `84356621636607dbd455b60de4d4a7a60c20d3d0` |
| Twitter production proposal | `uesu/wvkhabh2s22` | [#29](https://github.com/uesu/wvkhabh2s22/pull/29) | `2f879fae99147137b4f8635739e0d1115c043cca` |
| Game (independent app) | `uesu/Game-Express` | [#49](https://github.com/uesu/Game-Express/pull/49) | `5837ce4c9eef9ad80bb1d2b8c154652b1836d1de` |

A later docs-only commit on News #66 does not replace the News git SHA above
for helper/engine/lock hashes. If those files change, recompute.

Deployed `main` on the production copies (`3691cc88b2ef…` / `58547a93c866…`)
is a **different** snapshot (live caches, unhashed `requirements.txt`, no
maintenance helpers). It is not a substitute for the proposal-head review.

These News-family proposal heads are **not equivalent copies**. Hash difference
alone is not a defect. Four PRs are **not fully aligned**.

## SHA-256 prefixes (News / Reddit / Twitter)

Computed from file bytes at the git SHAs above (full digests in the JSON
artifact). Game is omitted from this table; see the helper disposition.

| Shared file | News | Reddit | Twitter |
|---|---|---|---|
| `.python-version` | `5abd4dc1efa0` | `5abd4dc1efa0` | `5abd4dc1efa0` |
| `.github/scripts/ci.py` | `171925850552` | `605207595f82` | `495979e1f7d5` |
| `.github/scripts/maintenance.py` | `5f0435c56cd7` | `c06559dcc766` | `3b32723efc87` |
| `.github/scripts/python_version_bump.py` | `913221935f13` | `a3011aba88dc` | `132d47c01045` |
| `.github/scripts/render_run_summary.py` | `97eedb3160cc` | `97eedb3160cc` | `7fe2a96696f9` |
| `.github/scripts/merge_monitor_caches.py` | `0e53a8c1a450` | `0e53a8c1a450` | `0e53a8c1a450` |
| `.github/workflows/maintenance_merge.yml` | `dc7669138d8a` | `dc7669138d8a` | `33a223d81978` |
| `.github/workflows/reddit_monitor.yml` | `a41eb60add7a` | `a41eb60add7a` | `2554d344d348` |
| `.github/workflows/twitter_monitor.yml` | `d1d9b3c3124d` | `d1d9b3c3124d` | `d74f6ad7cdac` |
| `testing area/reddit_main_v3.py` | `b31ec6a46080` | `345d4edf772d` | `d22764b8b86f` |
| `testing area/twitter_v3.py` | `9dfb4841b62d` | `afaeb716a614` | `a631640c7733` |
| `testing area/reddit_proxy.py` | `082aa9a2e4dc` | `06b7894e9dc7` | `c7e02d9531d0` |
| `testing area/twitter_proxy.py` | `ff911daa1289` | `ff911daa1289` | `ff911daa1289` |
| `testing area/reddit_signals.py` | `4b7a77f5bd56` | `4b7a77f5bd56` | `4b7a77f5bd56` |
| `testing area/run_report.py` | `aaa3138a4e95` | `76528e639b58` | *absent* |
| `tests/test_crosspost_video.py` | `ba04e4fc1595` | `259c9f22b4f8` | *absent* |

## Content review (not filename inference)

**Byte-identical across all three News-family proposals (authorized to share):**
`.python-version` (`3.14.8`), `merge_monitor_caches.py`, `twitter_proxy.py`,
`reddit_signals.py`. News and Reddit also share `render_run_summary.py`,
`maintenance_merge.yml`, both monitor workflows, and `.github/dependabot.yml`.

**Authorized repository / profile differences:**

* `.github/maintenance.json` — project identity, check names, `runtime_files`.
  News and Reddit share `project: news-express` and the same mandatory check
  set; Reddit adds `check_producers` / `security_evidence`. Twitter's profile
  is a different schema (`checks` / `risk_rules` / `update_policy`) and is not
  a drop-in News profile.
* Application engines — News vs Game are independent apps. Twitter #29 has a
  **different reporting implementation** (`run_report.py` absent; no engine
  `_close_report` / `RunReport` in `reddit_main_v3.py` / `twitter_v3.py`;
  `render_run_summary.py` SHA-256 `7fe2a96696f9` vs News/Reddit `97eedb3160cc`).
  Do not infer missing coverage from that filename gap.
* `tests/test_crosspost_video.py` is absent on Twitter #29. Crosspost/media
  assertions may live in `tests/test_smoke.py` there. Do not infer either
  equivalence or missing coverage solely from the missing file.
* Package graphs (`requirements.in` / hashed locks) differ by application
  (Game) and by which compiler extra landed in each lock. The pin is shared.

**Required News maintenance / media / report fixes at `be4baca` (this PR):**

* Hash-package association (`requirement_hash_members`,
  `unchanged-version-hash-mutation`) and SHA-bound failed legacy overlay
  (`mandatory-check-not-success`) — present in News `maintenance.py`;
  Reddit's helper has producer/security collectors News does not; Twitter's
  helper is a 17-function different module (`decision_from_fixture`,
  `resolve_check_provenance`).
* Crosspost structured parent + original-post markup, audio-cover skip,
  original media-ID inheritance, round-67 quality, HTTP-200 error body,
  child card snapshot, child dedup keys — News `reddit_main_v3.py` +
  `tests/test_crosspost_video.py`. Reddit's engine has the same named
  resolver/quality helpers; Twitter's engine uses different names
  (`resolve_crosspost_source` count 0) so compare fixtures/results, not
  filenames.
* Reporting: News engines call `_close_report` / `RunReport`. Reddit engines
  import `RunReport` but have no `_close_report`. Twitter engines have
  neither in those files.

**Not authorized as "the same helper":** copying any one `maintenance.py` /
`ci.py` / `python_version_bump.py` over another. They are materially
different implementations of related policy.

## Shared-helper requirement — explicit disposition (unmet)

The master spec requires **identical helpers + a project-specific profile**.
At the four proposal heads above that requirement is **not met**.

This News PR will **not**:

* blindly copy Reddit #2, Twitter #29, or Game #49 helper trees onto News
* force Game's runtime layout onto News, or News's layout onto Game
* call the four PRs fully aligned
* treat a post-acceptance cleanup as if it already satisfied the requirement

**Disposition for this PR:** keep the News helpers that hosted 3.14.8 CI
already exercises (`be4baca` hashes above). Document the SHA-256 and content
differences. Shared-helper identity remains an **open acceptance item** across
the four PRs. Full alignment needs a maintainer choice of one helper source
(or an explicit exception) and a separate exact-head review. Until then,
do **not** claim the helpers are identical.

Game #49 `maintenance.py` is 180 887 bytes (`5e2dfb595cd1…`) vs News 66 524
bytes (`5f0435c56cd7…`) with disjoint function sets. Game `main` still lacks
those helpers (they live on PR #49). That is Game's state, not a News CI
blocker.

## Must remain in every production copy (when copied later)

Both **engines** and **both monitor workflows**, hashed locks, `.python-version`,
and the News helpers listed in `runtime_files`. Copying to production is
maintainer-only and later. Never overwrite caches.

## Must not be copied onto production caches or required at runtime

* Dedup / pending / health JSON in `production_copy_exclude`
* README, AGENTS, PRIVACY/TERMS, and `docs/` (this file included)
* Correction handoffs and `NEWS_EXPRESS_UPDATE.md`

## Current review limitation

This is an exact-head **proposal** difference list plus an unmet shared-helper
disposition. It is not production parity, not four-PR alignment, and not
proof that deployed `main` contains these repairs.
