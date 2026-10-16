# Acceptance evidence map — News-Express PR #66

Development-side only (`docs/` is in `production_copy_exclude`). This maps
master-spec / 2026-10-16 handoff items to **actual** tests and hosted artifacts
at the current PR head. It is not a bug-free guarantee and not production parity.

Local runners use CPython **3.11.2**. The hosted gate is pinned **3.14.8**.

## N1 — no new reproduced News code blocker

Hosted CI on `66e5a9c` ([run 38830506391](https://github.com/uesu/News-Express/actions/runs/38830506391)):
application, maintenance, lock-consistency, workflow-security, maintenance-ci
all SUCCESS. Prior lock repair `a828015`
([run 38828287085](https://github.com/uesu/News-Express/actions/runs/38828287085))
also SUCCESS. Old red lock status is not carried forward.

Independent News probes still fail closed (see `tests/test_maintenance.py`):
mixed same-version hash mutation, unassociated hash-only, extra-index,
SHA-bound failed legacy status, COMMENTED after CHANGES_REQUESTED, forced
`3.14.7` `override-unavailable`.

## N2 — copy inventory, not parity

See [`COPY_MANIFEST.md`](COPY_MANIFEST.md). The three News-family heads are not
equivalent. Game helpers are not byte-identical. Production does not yet have
the hashed lock, pin, or maintenance helpers.

## N3 — coverage vs remaining limits

### Runtime and locks

| Requirement | Evidence | Limit |
|---|---|---|
| Exact `.python-version` 3.14.8 | `PinAndLockTests`, hosted setup-python | Local 3.11.2 is not the gate |
| Hashed runtime + dev graphs | `test_hashed_locks_exist`; hosted lock-consistency recompile | Do not recompile on 3.11.2 |
| `--require-hashes --only-binary=:all:` | `WorkflowContractTests`, `ci.yml` | — |
| Byte-stable regeneration + header normalize | `tests/test_maintenance.py` lock tests; hosted lock-consistency | Compiler header only |
| No Actions lockfiles | `test_no_actions_lockfile` | — |
| `SKIP_ACTIONLINT` success forbidden | workflow-security job | Not re-run here as a skip probe |

`setup-python` artifact `published_at` is **not** the python.org CPython
release date. Missing dates remain deferred.

### Proposer / merge / checks

Covered by `tests/test_maintenance.py` (forced pins, soak, identity, provenance,
risk grouping, review/hold labels, SHA-bound checks, legacy non-success overlay,
COMMENTED ignored for decision-affecting state). Live GitHub writes are not
executed. Missing `BUMP_PAT` is documented as a configuration error in
`python_version_bump.yml`.

### Reporting

| Scenario | Evidence | Limit |
|---|---|---|
| Missing report ≠ zero activity | `test_missing_report_is_unavailable_not_zero` | — |
| Empty completed run reports real zeros | `test_empty_completed_run_reports_real_zeros_missing_is_unavailable` | — |
| Local save / commit / push independent | `test_persistence_failure_states_are_independent` | Render-level; workflows set these strings |
| Unhandled close is `failed` | engine `_close_report` tests | Does not run a full `main()` |
| Report write failure does not raise / mask | `test_write_failure_does_not_raise`, engine close-report | — |
| No extra HTTP from wrap_session | `test_wrap_session_counts_existing_http_without_extra_calls` | — |
| Transport vs `host_select` | timeout/429/cancel tests; challenge feed | Not a live outage |

No-activity, source outage, partial delivery, and early exception are covered
at report-object / close-report level with mocked I/O, not by dispatching
monitors.

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

### Game codes / News posting baseline

Not re-proven by dispatch. Smoke + signal suites remain the no-post baseline.
This PR does not change fleets, routing, pings, or Game.

## What this is not

Green hosted checks, listed-defect fixes, helper-only tests, and manual card
repairs are not final acceptance, not production parity, and not a
zero-undiscovered-bug guarantee.
