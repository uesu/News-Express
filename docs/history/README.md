# History archive

Everything dated lives here, so the [main README](../../README.md) and the
topic guides in [`docs/`](../) stay focused on the current shipped behavior.

| File | Contents |
|---|---|
| [`CHANGELOG_ARCHIVE.md`](CHANGELOG_ARCHIVE.md) | Full dated changelog, rounds 1–62 (newest first) |
| [`ENGINE_HISTORY.md`](ENGINE_HISTORY.md) | Round-by-round engine behavior notes, moved verbatim out of the README (2026-10-05) |
| [`REPOSITORY_TRACKING_2026-10-01.md`](REPOSITORY_TRACKING_2026-10-01.md) | File/config/policy inventory and audit record — a dated snapshot of baseline `6ff4270`, written before the round-63 simplification |
| `ROUND_*.md`, `round-15-validation.md` | Decision records per incident (what broke, why, the fix, the guards) |

Rounds 63+ are summarized in [`docs/CHANGELOG.md`](../CHANGELOG.md) (moved out
of the README on 2026-10-06; the README's Changelog section is now a short
pointer to that file and to this archive).
Moved here on 2026-10-05 (README restructure); stale deployment artifacts of
already-merged rounds (`round_46b.patch`, `bump_3.14.8.patch` — superseded by
the automated `python_version_bump.yml` workflow — and the copy-paste PR
packages for rounds 42–45) were deleted in the same pass.
