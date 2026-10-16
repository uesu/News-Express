# Acceptance evidence map — News-Express PR #66

Development-side only (`docs/` is in `production_copy_exclude`). This maps
master-spec / 2026-10-16 handoff items to **actual** tests and hosted artifacts.
It is not a bug-free guarantee, not production parity, and not four-PR alignment.

Local runners use CPython **3.11.2**. The hosted gate is pinned **3.14.8**.
Helper-only fixtures and mocked probes are **not** live GitHub merges, candidate
runs, publications, or Discord posts.

Unchecked media checkboxes in a handoff are not proof that every item lacks
tests; named coverage is in the tables below.

## Current-head hosted CI

News #66 docs/inventory head `fc65483a802e3f627fdb2b1a56d0913fd1ce18d1`:
[run 38855237517](https://github.com/uesu/News-Express/actions/runs/38855237517)
— application, maintenance, lock-consistency, workflow-security,
maintenance-ci all SUCCESS.

Implementation-byte head `be4bacaa0e4a1688517549c99915d93d0227024e` (helpers,
engines, locks unchanged):
[run 38837001161](https://github.com/uesu/News-Express/actions/runs/38837001161).

Prior lock repair `a828015`:
[run 38828287085](https://github.com/uesu/News-Express/actions/runs/38828287085).

A later **docs-only** commit does not replace those runs for unchanged
helpers, engines, and locks. Recheck hosted jobs if those files change.

## N1 — no new reproduced News code blocker

Old red lock status is not carried forward. Independent News probes still fail
closed (`tests/test_maintenance.py`): mixed same-version hash mutation,
unassociated hash-only, extra-index, SHA-bound failed legacy status, COMMENTED
after CHANGES_REQUESTED, forced `3.14.7` `override-unavailable`. Twitter CI
changes are not a News CI fix.

## N2 — proposal-head inventory, not parity

See [`COPY_MANIFEST.md`](COPY_MANIFEST.md) and
[`proposal_head_hashes.json`](proposal_head_hashes.json). Compared heads are
News implementation `be4baca`, Reddit #2 `d123c0d` (supersedes `62a9c30`;
`reddit_proxy.py` / smoke now match News), Twitter #29 `26b84ff` — not
deployed `main`. Shared helpers are **not** identical. The master
identical-helper requirement is **unmet** and **not excepted**; four PRs are
**not fully aligned**. The explicit “unmet” note is inventory, not completion.

## N3 — coverage vs remaining limits

### Runtime and locks (candidate path)

| Requirement | Evidence | Limit |
|---|---|---|
| Exact `.python-version` 3.14.8 | `PinAndLockTests`; hosted setup-python on 38837001161 | Local 3.11.2 is not the gate |
| Hashed runtime + dev graphs | `test_hashed_locks_exist`; hosted lock-consistency recompile | Do not recompile on 3.11.2 |
| `--require-hashes --only-binary=:all:` | `WorkflowContractTests`, `ci.yml` | — |
| Byte-stable regeneration + header normalize | `tests/test_maintenance.py` lock tests; hosted lock-consistency | Compiler header only |
| Pinned compiler in hosted lock job | hosted lock-consistency on 3.14.8 | Not re-executed here as a local compile |
| Same validation registry before/after pin rewrite | `python_version_bump.yml` `--group` counts; `ci.py` | Candidate publisher not run |
| Missing `BUMP_PAT` is a configuration error | bump workflow text | Secret not present in this sandbox |
| No Actions lockfiles | `test_no_actions_lockfile` | — |
| `SKIP_ACTIONLINT` success forbidden | workflow-security job | Not re-run as a skip probe |

`setup-python` artifact `published_at` is **not** the python.org CPython
release date. Missing dates remain deferred.

### Controller / proposer / checks

| Requirement | Evidence | Limit |
|---|---|---|
| Forced pin / downgrade / soak / skip-series | `tests/test_maintenance.py` select/classify | Isolated fixtures, not a live candidate |
| Updater identity + provenance; branch/title not enough | `trusted_updater` / `decide_merge` tests | No live merge |
| SHA-bound required checks; missing/neutral fail closed | `classify_checks` tests | Pagination bound is code, not a live 100-page fetch |
| Failed SHA-bound legacy status blocks | `mandatory-check-not-success` probe | Mocked statuses |
| COMMENTED does not clear CHANGES_REQUESTED | review tests | — |
| Merge controller reads trusted default branch | `test_merge_controller_trusted_checkout` | Workflow text, not an applied merge |
| One final gate `maintenance-ci` | profile + hosted final job | — |

### Reporting

| Scenario | Evidence | Limit |
|---|---|---|
| Missing report ≠ zero activity | `test_missing_report_is_unavailable_not_zero` | — |
| Empty completed run reports real zeros | `test_empty_completed_run_reports_real_zeros_missing_is_unavailable` | — |
| Degraded vs failed vs not-run | `test_degraded_failed_and_not_run_are_distinct` | Report object, not `main()` |
| Local save / commit / push independent | `test_persistence_failure_states_are_independent` | Render-level; workflows set these strings |
| Unhandled close is `failed` | engine `_close_report` tests | Does not run a full `main()` |
| Report write failure does not raise / mask | `test_write_failure_does_not_raise`, engine close-report | — |
| No extra HTTP from wrap_session | `test_wrap_session_counts_existing_http_without_extra_calls` | — |
| Transport vs `host_select` | timeout/429/cancel tests; challenge feed | Not a live outage |

No-activity, source outage, partial delivery, and early exception are covered
at report-object / close-report level with mocked I/O, not by dispatching
monitors.

### Performance

Setup / monitor / reporting durations are fields on `RunReport` (`duration.*`).
This PR does **not** claim faster runs or zero overhead. No timing measurements
were taken.

### Crosspost video (both incident fixtures are IDs only)

| Checklist item | Evidence | Limit |
|---|---|---|
| Structured parent list + ID-only | `test_structured_parent_one_hop`, `test_id_only_structured_parent`, Arctic native path | No live Reddit/OAuth |
| Explicit Original Post markup, no English keyword gate | `test_labeled_original_without_keyword`, `test_html_anchor_original_post` | — |
| Reject foreign / scheme-relative / self / mismatch / malformed / unrelated keyword window | matching `OriginalDiscoveryTests` | — |
| Poster-only proxy does not replace parent video id | `test_poster_only_proxy_does_not_replace_parent_video_id` | Does not range-probe a live muxed URL |
| Motion-first and audio-cover-first og:video | `test_proxy_og_keeps_first_motion_and_skips_later_cover`, `test_proxy_og_prefers_later_motion_video` | Parser-level |
| Audio-cover is not motion | `test_audio_cover_filtered` | — |
| Inherit original media ID from encoded 1080 pairing | `test_encoded_1080_pairing_keeps_original_id_not_child`, both incident fixtures | Decode-for-inspection only |
| Quality: 1080 beats 720; default 720 cannot displace healthy vx; failed keeps base; audio loss keeps vx | `NativeAndQualityTests` | Facts are injected, not probed |
| Compatibility keeps base, no quality HTTP | `test_compatibility_quality_upgrade_keeps_base_without_http`; smoke r67b | — |
| HTTP-200 HTML/JSON error body rejected | `test_http_200_error_body_is_not_video`; smoke r67 | Prefix helper, not a live 200 |
| Video fail keeps remaining images | `test_audio_cover_failure_keeps_proxy_images` | — |
| Child card snapshot (title/byline/body/attribution/buttons/Read Post/5-image gallery/accent/stats/timestamp) | `test_child_card_keeps_identity_with_five_image_gallery` | Built payload, not Discord |
| Child dedup keys; no parent in key | `test_incident_dedup_keys_are_child_not_parent` | Formula of `collect()`, not a live cache write |

Manual Discohook/1080 playback of `22e7ve17smvh1` is **user-observed**, not a
runner-side resolution/audio probe. Bounded heal (round 72) is unchanged.
No historical edit, repost, or cache reset.

Twitter #29 has no standalone `tests/test_crosspost_video.py`. That absence is
not News missing coverage, and is not proof Twitter lacks equivalent smoke
assertions.

### Game codes / News posting baseline

Not re-proven by dispatch. Smoke + signal suites remain the no-post baseline.
This PR does not change fleets, routing, pings, or Game.

## What this is not

Green hosted checks, listed-defect fixes, helper-only tests, and manual card
repairs are not final acceptance, not production parity, not four-PR helper
alignment, and not a zero-undiscovered-bug guarantee.
