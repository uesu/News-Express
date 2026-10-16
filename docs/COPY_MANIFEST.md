# Shared file manifest — News-Express development vs production copies

This is a **development-side** review document. It is not a runtime input.
`production_copy_exclude` lists `docs/`, so production copies must not require
this file.

The machine-readable lists live in `.github/maintenance.json`:

* `runtime_files` — files a documentation-free production copy still needs
* `production_copy_exclude` — docs, onboarding, and **caches that must never
  be overwritten**
* `optional_docs` — present in this development tree; omitted in production

The three heads (this development repo, `uesu/7jkxmy9nvbc`, `uesu/wvkhabh2s22`)
are **not equivalent copies**. Do not blindly copy either production variant
back into development. Copying to production is maintainer-only and later.

## Must remain in every production copy

Both **engines** and **both monitor workflows** stay present in each production
copy even when that copy only posts one network. Shared helpers
(`maintenance.py`, `ci.py`, `python_version_bump.py`, `render_run_summary.py`)
and the hashed locks / `.python-version` pin go with them.

Game-Express shares helper *semantics* via identical helpers + a project
profile. The applications stay independent; do not force either runtime layout
onto the other.

## Must not be copied onto production caches or required at runtime

* Dedup / pending / health JSON listed in `production_copy_exclude`
* README, AGENTS, PRIVACY/TERMS, and `docs/`
* Correction handoffs and `NEWS_EXPRESS_UPDATE.md` — development-side only

Justified production differences: omitted documentation, independent caches,
and repository-identity / webhook configuration. Unrelated posting behavior
is not an authorized difference.

## Current review limitation

Green tests and green hosted checks on this development head do **not**
establish that the two production copies already contain these repairs.
Parity remains a separate maintainer copy review.
