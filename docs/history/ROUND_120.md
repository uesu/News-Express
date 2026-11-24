# Round 120 — relay candidates survive delayed Reddit age (2026-11-25)

## Cause

The Reddit monitor run for the supplied `AnantaLeaks/1y3i54e` evidence saw a healthy,
recent relay message, but the Reddit post itself had been created about 32 hours earlier.
The live run had `REDDIT_MONITOR_WINDOW_HOURS` unset, so V3 used its five-hour default.
`collect()` applied `MAX_AGE_SECONDS` to ordinary `_IntakeEntry` relay records as well as
legacy RSS/archive candidates. The relay's message-age health check passed, but this separate
source-post-age check discarded the post before it could enter the delivery pipeline. That
age-filter branch did not emit a per-post reason, which made the quiet-run `0 considered` result
look like the relay had simply not supplied a candidate.

The two clocks are distinct:

- `INTAKE_LOOKBACK_HOURS` measures how far back the Discord reader scans relay **messages**.
- The retired `REDDIT_MONITOR_WINDOW_HOURS` controlled source-post eligibility in the Python
  monitor (and several legacy retention/search horizons).
- Devvit's post-delivery rechecks govern later edit/removal status updates on cards already
  delivered. They remain on their separate five-hour schedule; this round does not change them.

The provided production-variable inventory did not list `REDDIT_MONITOR_WINDOW_HOURS`; the
five-hour source-post cutoff was therefore coming from the code default, not from a configured
value in that inventory.

## Change

- Remove `REDDIT_MONITOR_WINDOW_HOURS` from the V3 source, workflow environment, `.env.example`,
  and active README variable table.
- Relay-primary candidates are no longer rejected because their Reddit `created` timestamp is
  more than five hours old. They still pass through the existing dedup check, current relay
  removal/approval checks, media/liveness policy, and `MAX_POSTS_PER_RUN` cap. Cached posts remain
  skipped; this is not a repost mode.
- Keep the legacy RSS/archive path's source-age horizon fixed at five hours. Rename the constant
  to `LEGACY_MAX_AGE_SECONDS` to make its scope explicit. Keep the legacy pending-cache retention
  and relay message-ID retention windows at their existing five-hour values.
- Leave `INTAKE_LOOKBACK_HOURS`, Devvit's edit/removal recheck schedule, relay update handling,
  deletion behavior, and secrets/production configuration untouched.
- Update README and changelog wording so “no fresh-age floor” is not confused with the removed
  maximum-age gate, and so the intake-message, source-post, and lifecycle clocks are explicit.

An old uncached relay backlog can now be delivered, so the existing per-run flood cap and bounded
posted-ID cache remain important safeguards. The relay history window still limits which relay
messages are read on a given run; this round does not expand that window or cause the relay to
backfill older posts by itself.

## Verification

Offline regression coverage verifies that a relay record 32 hours old remains eligible, a legacy
candidate older than the fixed five-hour fallback horizon remains excluded, and a cached relay key
continues to be deduplicated before age eligibility. The five-hour Devvit relay message-ID retention
and scheduler slack are also pinned unchanged.
