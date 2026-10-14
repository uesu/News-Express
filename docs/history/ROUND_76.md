# Round 76 — the runner-clean head + the xcopy.uk verdict

**Status:** Open — this PR
**Scope:** Twitter V3 RSS source order (`RSS_INSTANCES`); offline smoke guards; docs
**Date:** 2026-10-15
**Not in scope:** Reddit (no source-list, comment or guard change); workflows; proxy
services; gates; caches; media paths; token mapping

## What happened

Round 75 seated `xcopy.uk` at 3 on body evidence alone (8/8 monitored handles,
`nitter.cf` parity) and called that seat a *trial ticket, never proof*: the serial
chain only reaches seat 3 when the operator pair has failed, so the production
runner would have to supply the verdict. Game-Express — the sister monitor that runs
the same twelve-member order from the same GitHub Actions runners and probes every
seat on every run — delivered it within the first hour after merge.

**Runs #2662–#2665 (2026-10-14 17:19–17:30 UTC):** `xcopy.uk` returned **HTTP 403 on
all six Game-Express handles, in every run, from four different Azure regions**
(westus, westus3, eastus2, centralus) — 24/24 fetches refused. The same afternoon,
an off-runner probe read a clean body on all eight union handles with `nitter.cf`
parity. A clean body for everyone else plus a flat refusal to GitHub Actions /
Azure datacenter IPs is exactly the `nitter.kareem.one` signature recorded on
2026-10-03, and it is the most thoroughly measured hard refusal in this fleet's
history.

The operator then set this round's ranking rule and directed the head of the chain:

> **No member that blocks GitHub Actions / Azure datacenter IPs (or datacenter IPs
> generally) may sit above one that doesn't.**

> New top four for BOTH monitors: `nitter.cf`, `xitter.cf`, `nitter.meowing.monster`,
> `nitter.miningtcup.me`.

This file is the News-Express side of that decision. The Game-Express side (rotation
#6) is a separate PR in that repository, as always.

## The evidence this round

All probes 2026-10-14/15, bodies read, top tweet ids compared to `nitter.cf` controls
taken the same hour. "Union" = the eight handles the two monitors watch between them
(News-Express: TYPEII_EN, PomPom_HonkaiSR, Wuthering_Waves, HonkaiNA, Ananta_EN;
Game-Express-exclusive: GenshinImpact, honkaistarrail, ZZZ_EN).

| Host | Off-runner body | Runner (GitHub Actions / Azure) evidence | Union coverage (8 handles) |
|---|---|---|---|
| `nitter.cf` | ✓ controls current through Oct 14 10:00 UTC | ✓ 6/6 every run | 8/8 |
| `xitter.cf` | same machine as `nitter.cf` | ✓ answered its whole tenure (GE run #2323) | 8/8 |
| `nitter.meowing.monster` | ✓ GenshinImpact + ZZZ_EN identical top ids (one transient HTTP 500 on GenshinImpact, cleared on retry) | ✓ 6/6 (#2323), 5/6 (#2621); IPv6-listed host on IPv4-only runners → slow | 8/8 (slow) |
| `nitter.miningtcup.me` | token-gated, untestable off-runner | ✓ 6/6 with the token | 8/8 (token) |
| `nitter.freedit.eu` | ✓ GenshinImpact / honkaistarrail / ZZZ_EN identical top ids this round; 5/5 News-Express accounts on Oct 14 | none — and zero refusals anywhere, from any vantage | **8/8** |
| `nitter.gravitywell.xyz` | ✓ honkaistarrail / ZZZ_EN identical top ids; `User "GenshinImpact" not found` (NEW this round) | none | 5/8 (fails GenshinImpact, Wuthering_Waves, HonkaiNA) |
| `tw.eir-nya.gay` | HTTP 429 on every Game-Express-handle probe, retry included (throttle, not block); News-Express bodies clean Oct 14 | HTTP 200 with 0 entries on all 6 handles + NITTER_GRACE losses (GE 2026-10-03 / #2323 era) | 0 delivered from runners |
| `shitter.thepixora.com` | ✓ clean body | ✗ HTTP 403 on all 6 (GE run #2312, Oct 13) three days after 25 ok / 0 fail (Oct 10, runs #1378/#1386) — flapping | 0 while blocked |
| `nitter.kareem.one` | ✓ clean body | ✗ HTTP 403 on all 6 (2026-10-03 04:25) | 3/8 (fails TYPEII_EN, PomPom_HonkaiSR) |
| `xcopy.uk` | ✓ clean body (8/8, Oct 14) | ✗ **HTTP 403 × 24, 4 regions, 4 runs (Oct 14)** | 0 while blocked |
| `nitter.netbub.com` | `__goaway_challenge` wall | ✗ 403 to GitHub runners | — |
| `nitter.jaydenha.uk` | click-to-enter splash | splash for everyone | — |

## How the order follows from the evidence

1. **Seats 1–2 — the operator pair** (`nitter.cf`, `xitter.cf`): the round-40 block,
   byte-identical, as every round.
2. **Seats 3–4 — operator-directed, runner-proven.** `nitter.meowing.monster` (4 → 3) is
   one of only two non-token-gated members with positive runner deliveries;
   `nitter.miningtcup.me` (8 → 4) is proven 6/6 from the hot path with the token and
   is an instant skip without it. For the first time the whole head of the chain
   has delivered from the production runners.
3. **Seats 5–6 — the union-coverage test among the never-refused trials.**
   `nitter.freedit.eu` (6 → 5) is the only host in the fleet with full 8/8 union
   coverage and zero refusals on record anywhere; `nitter.gravitywell.xyz` (9 → 6)
   covers 5/8 with deterministic account-resolution gaps (GenshinImpact newly
   observed alongside Wuthering_Waves and HonkaiNA) that are exactly complementary to
   kareem.one's. Both remain TRIAL seats: no runner evidence yet, and seats 5+ only
   answer once the runner-proven head has failed.
4. **Seat 7 — passes the rule, but has never delivered.** `tw.eir-nya.gay` (5 → 7)
   answers the runners HTTP 200, so it sits above every blocker — but it carries the
   fleet's only measured runner *non-deliveries* (the 2026-10-03 NITTER_GRACE loss,
   then 200-with-0-entries on all six handles) and 429-throttled every
   Game-Express-handle probe this round. It moves up the day a runner log shows a
   real delivery.
5. **Seats 8–10 — the measured runner refusals, freshest-measurement order.**
   `shitter.thepixora.com` (7 → 8) is flapping (403 on Oct 13 after a clean Oct 10),
   `nitter.kareem.one` (10 → 9) is the standing 403 from 2026-10-03, and `xcopy.uk`
   (3 → 10) records this round's verdict. A 403 is a fast fail in a serial chain, and
   each moves back up the day it answers the runners.
6. **Seats 11–12 — the walled tail** (`nitter.netbub.com`, `nitter.jaydenha.uk`):
   unchanged since round 59; jaydenha stays last.

Why the trial design worked exactly as intended: the body evidence bought `xcopy.uk`
the seat, the every-run Game-Express probe cashed it in for a runner verdict within
the hour, and the quorum never depended on it — `nitter.cf` served first-hit
throughout.

## Final Twitter V3 order

| Seat | Host | Round-75 seat | Why |
|---:|---|---:|---|
| 1 | `nitter.cf` | 1 | operator-approved primary |
| 2 | `xitter.cf` | 2 | operator-approved secondary (feed links point back to nitter.cf) |
| 3 | `nitter.meowing.monster` | 4 | operator-directed; runner-proven 6/6 and 5/6; IPv6-slow watch |
| 4 | `nitter.miningtcup.me` | 8 | operator-directed; token-gated, runner-proven 6/6 with the token |
| 5 | `nitter.freedit.eu` | 6 | 8/8 union coverage, zero refusals anywhere; TRIAL |
| 6 | `nitter.gravitywell.xyz` | 9 | 5/8 union coverage, deterministic gaps complementary to kareem; TRIAL |
| 7 | `tw.eir-nya.gay` | 5 | passes the no-block rule; 0 runner deliveries (grace loss, 200-with-0-entries); 429s this round |
| 8 | `shitter.thepixora.com` | 7 | flapping runner 403 (freshest measurement blocked) |
| 9 | `nitter.kareem.one` | 10 | standing runner 403 since 2026-10-03; clean body off-runner |
| 10 | `xcopy.uk` | 3 | **the verdict:** 403 × 24, four Azure regions, four runs |
| 11 | `nitter.netbub.com` | 11 | anti-scrape challenge wall |
| 12 | `nitter.jaydenha.uk` | 12 | click-to-enter interstitial, outdated build; stays last |

Membership: **twelve, unchanged** — the same set as the round-75 v4 order, re-ranked
only. Nothing deleted. The operator pair untouched. Reddit untouched.

## Deliberate non-goals

- Nothing is deleted. `xcopy.uk` is demoted, not removed — it moves back up the day
  it answers the runners, like every blocked member before it.
- No Reddit change: `REDDIT_RSS_INSTANCES`, its round-75 audit comments and the
  round-75 membership guard are unchanged.
- No workflow, proxy service, gate, cache, media path, token mapping or environment
  constant changes. V1/V2 keep their separately reviewed source lists.

## Guards

`tests/test_smoke.py`:

- `test_r76_runner_proven_head_xcopy_verdict_recorded_at_ten` replaces the r75 v4
  named guard and pins every seat of the twelve-member order (plus
  `len == len(set) == 12`).
- The exact-order pin (`_r76_x_expected`) replaces `_r75_x_expected`.
- The r75 v4 relative pin "eir-nya ahead of the token fallback" is updated in place
  (round 76 deliberately reverses it) into the round-76 rules: the runner-proven
  head precedes every member without a runner delivery; no member with a measured
  runner 403 sits above one that has never refused the runners; the token fallback
  precedes gravitywell, then kareem; the walled hosts stay last.
- `test_r75_reddit_rss_instance_membership_unchanged` (the Reddit membership guard)
  is unchanged.

## Housekeeping shipped in the same PR (no behavior change)

A repository-wide pass for stale words and dead names rode along in a second
commit. In `testing area/twitter_v3.py`: the retired round-34 `MAX_CACHE_SIZE = 500`,
the unused `MAX_AGE_SECONDS` and the unused `_env_float` helper are removed (none
was referenced anywhere — engine, tests or workflows); the pre-round-59 fleet
header above `RSS_INSTANCES` is rewritten into the current rules (serial chain,
runner evidence over tracker rows, the round-76 no-datacenter-block rule,
demote-not-delete, guard-in-the-same-commit); the `docs/ROUND_56.md` pointer now
reads `docs/history/ROUND_56.md`; one placeholder-less f-string prefix is dropped.
Outside the engine: `python_version_bump.yml` now runs
`tests/test_twitter_media.py` in both verify steps (it had claimed CI parity since
round 73 without it); README, `docs/CI_SMOKE.md`, `docs/DEPENDABOT.md` and
`docs/PYTHON_RUNTIME.md` name all three suites; the README's "11-instance" line and
round-59 credits order become the round-76 order and rule; `AGENTS.md` gains the
fleet invariant and the engine-before-guard deploy order; `.env.example`'s round-63
note names the checks that actually remain; a duplicate `import tempfile` leaves
`tests/test_smoke.py`. `reddit_main_v3.py` still carries its own retired
`MAX_CACHE_SIZE = 500` (same round-34 note) — left alone on purpose because Reddit
is out of scope this round; a future Reddit round can drop it.

## Validation

```text
python3 tests/test_smoke.py           # SMOKE TEST: ALL PASS
python3 tests/test_reddit_signals.py  # ALL PASS
python3 tests/test_twitter_media.py   # TWITTER MEDIA TEST: ALL PASS
git status                            # no cache jsons staged
```

## Deployment (manual, after merge)

Two files this round, to **both** `uesu/wvkhabh2s22` and `uesu/7jkxmy9nvbc`, in this
order:

1. `testing area/twitter_v3.py` **first** — it carries the new twelve-member order.
2. `tests/test_smoke.py` **second** — it carries the r76 guard.

`testing area/reddit_main_v3.py` is unchanged this round — nothing to upload. No
`docs/`, no workflow files. Engine-before-test is the lesson from the round-75
deploy: the smoke-only commits went red because the guard landed before the engine
file.

**Post-deploy check:** the next monitor runs stay green (`nitter.cf` serves first-hit
as always); the runner verdict for seats 5/6 (freedit, gravitywell) arrives only if
the head ever fails — watch, don't force.
