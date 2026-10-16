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
| News ancestor implementation bytes | `uesu/News-Express` | [#66](https://github.com/uesu/News-Express/pull/66) | `be4bacaa0e4a1688517549c99915d93d0227024e` |
| News N2 Part A candidate | `uesu/News-Express` | [#66](https://github.com/uesu/News-Express/pull/66) | this working tree (a commit cannot embed its own final self-hash) |
| Reddit production proposal | `uesu/7jkxmy9nvbc` | [#2](https://github.com/uesu/7jkxmy9nvbc/pull/2) | `d123c0d7028061771e3b1789dd9414fed82c06f8` |
| Twitter production proposal | `uesu/wvkhabh2s22` | [#29](https://github.com/uesu/wvkhabh2s22/pull/29) | `26b84ff455ac5675476a55fde357dd63387627ad` |
| Game (independent app) | `uesu/Game-Express` | [#49](https://github.com/uesu/Game-Express/pull/49) | `5837ce4c9eef9ad80bb1d2b8c154652b1836d1de` |

Ancestor helper/engine/lock hashes remain `be4baca` until a file changed in
the Part A candidate. This document does not embed its own commit SHA
as those bytes. The candidate is **not** approved for blind adoption.

Reddit `d123c0d` supersedes `62a9c30d624ac9717ad3ce11ab380897b03af379`.
Twitter remains `26b84ff455ac5675476a55fde357dd63387627ad`. If those files
change, recompute.

Deployed `main` on the production copies (`3691cc88b2ef…` / `58547a93c866…`)
is a **different** snapshot (live caches, unhashed `requirements.txt`, no
maintenance helpers). It is not a substitute for the proposal-head review.

These News-family proposal heads are **not equivalent copies**. Hash difference
alone is not a defect. Four PRs are **not fully aligned**.

## SHA-256 prefixes (News / Reddit / Twitter)

Computed from file bytes at the git SHAs above (full digests in the JSON
artifact). Game is omitted from this table; see the helper disposition.

| Shared file | News ancestor `be4baca` | News candidate | Reddit `d123c0d` | Twitter `26b84ff` |
|---|---|---|---|---|
| `.python-version` | `5abd4dc1efa0` | `5abd4dc1efa0` | `5abd4dc1efa0` | `5abd4dc1efa0` |
| `.github/scripts/ci.py` | `171925850552` | `e25144fff3e6` | `605207595f82` | `3fe705cc1f02` |
| `.github/scripts/maintenance.py` | `5f0435c56cd7` | `cce2cdbd41b9` | `ed7dd1ef5e52` | `766548226b01` |
| `.github/scripts/maintenance_common.py` | *absent* | `4e9c57ad337b` | *absent* | *absent* |
| `.github/scripts/python_version_bump.py` | `913221935f13` | `dcdd28c0c314` | `a3011aba88dc` | `01f087f4f568` |
| `.github/scripts/render_run_summary.py` | `97eedb3160cc` | `97eedb3160cc` | `97eedb3160cc` | `7fe2a96696f9` |
| `.github/scripts/merge_monitor_caches.py` | `0e53a8c1a450` | `0e53a8c1a450` | `0e53a8c1a450` | `0e53a8c1a450` |
| `.github/workflows/ci.yml` | `4b043c1fc6be` | `4b043c1fc6be` | `4b043c1fc6be` | `8b30011dc7ec` |
| `.github/workflows/maintenance_merge.yml` | `dc7669138d8a` | `dc7669138d8a` | `dc7669138d8a` | `1911ab367463` |
| `.github/workflows/reddit_monitor.yml` | `a41eb60add7a` | `a41eb60add7a` | `a41eb60add7a` | `2554d344d348` |
| `.github/workflows/twitter_monitor.yml` | `d1d9b3c3124d` | `d1d9b3c3124d` | `d1d9b3c3124d` | `d74f6ad7cdac` |
| `testing area/reddit_main_v3.py` | `b31ec6a46080` | `b31ec6a46080` | `345d4edf772d` | `d22764b8b86f` |
| `testing area/twitter_v3.py` | `9dfb4841b62d` | `9dfb4841b62d` | `afaeb716a614` | `a631640c7733` |
| `testing area/reddit_proxy.py` | `082aa9a2e4dc` | `082aa9a2e4dc` | `082aa9a2e4dc` | `c7e02d9531d0` |
| `testing area/twitter_proxy.py` | `ff911daa1289` | `ff911daa1289` | `ff911daa1289` | `ff911daa1289` |
| `testing area/reddit_signals.py` | `4b7a77f5bd56` | `4b7a77f5bd56` | `4b7a77f5bd56` | `4b7a77f5bd56` |
| `testing area/run_report.py` | `aaa3138a4e95` | `aaa3138a4e95` | `76528e639b58` | *absent* |
| `tests/test_crosspost_video.py` | `ba04e4fc1595` | `ba04e4fc1595` | `7fde63ae8d31` | *absent* |
| `tests/test_smoke.py` | `0eb1dd9eaf2c` | `0eb1dd9eaf2c` | `0eb1dd9eaf2c` | `6f6d1f1a6b22` |

**Delta vs `62a9c30`:** Reddit media files **did change**. `testing area/reddit_proxy.py`
(`06b7894e9dc7` → `082aa9a2e4dc`) and `tests/test_smoke.py` are now
**byte-identical to News #66** (`_MULTI_OG_KEYS` / `_og_values` so a leading
audio-cover `og:video` cannot hide a later motion candidate). `ci.yml` also
matches News (`4b043c1fc6be`). `tests/test_crosspost_video.py` moved
(`259c9f22b4f8` → `7fde63ae8d31`) and is still not News-identical. Reddit
`maintenance.py` / engines / locks are unchanged from `62a9c30`. Twitter
`26b84ff` is unchanged; its `reddit_proxy.py` remains `c7e02d9531d0` (no
`_MULTI_OG_KEYS`). Filename absence on Twitter is not a News defect. Unchanged News
engine/lock bytes are still `be4baca`; helper adapters plus
`maintenance_common.py` are the Part A candidate.

## Content review (not filename inference)

**Byte-identical across all three News-family proposals (authorized to share):**
`.python-version` (`3.14.8`), `merge_monitor_caches.py`, `twitter_proxy.py`,
`reddit_signals.py`. News and Reddit also share `reddit_proxy.py`,
`tests/test_smoke.py`, `ci.yml`, `render_run_summary.py`,
`maintenance_merge.yml`, both monitor workflows, `.github/dependabot.yml`,
and the twitter-media / reddit-signals test files.

**Authorized repository / profile differences:**

* `.github/maintenance.json` — project identity, check names, `runtime_files`.
  News and Reddit share `project: news-express` and the same mandatory check
  set. News now also carries `check_producers` / `security_evidence` /
  `publication_evidence` / `compiler` (profile seam). Twitter's profile
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
  Reddit's helper (`ed7dd1ef5e52`, 56 functions) has producer/security
  collectors plus check-run URL binding / alert-state validation News does
  not; Twitter's helper (`766548226b01`, 18 functions) is a different
  module (`decision_from_fixture`, `resolve_check_provenance`).
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
At the four proposal heads above that requirement is **not met**. Recording
that fact is inventory, **not** completion of the requirement.
No maintainer-approved exception has been granted. The requirement is **not**
waived and is **not** moved past acceptance.

This News PR now contains a News-local common-helper **candidate**
(`.github/scripts/maintenance_common.py` plus a profile seam in
`.github/maintenance.json`). The candidate is **not** approved for blind
adoption and does **not** prove Game / Reddit / Twitter compatibility.
Copying Game, Reddit, or Twitter helper trees onto News would overwrite
completed News safety (hash-package association, SHA-bound legacy overlay)
or force another application's layout. This repository cannot rewrite the
other three PRs. N2 closes only after byte-identical common files at all
four final heads plus each repo's real CI/adapter/no-post baselines.

This News PR will **not**:

* blindly copy Reddit #2, Twitter #29, or Game #49 helper trees onto News
* force Game's runtime layout onto News, or News's layout onto Game
* call the four PRs fully aligned
* treat a post-acceptance cleanup as if it already satisfied the requirement

**Disposition for this PR:** News Part A candidate is in tree. Shared-helper
identity remains an **open acceptance item** across the four PRs. Full
alignment needs maintainer selection plus Game #49 / Reddit #2 / Twitter #29
integration on their own branches, then an exact-head review. Until then,
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
