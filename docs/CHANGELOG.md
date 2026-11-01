# Changelog

## Unreleased — Devvit relay: Biome no longer formats Markdown (2026-11-01, no engine change)

- The first Dependabot PR opened by the new npm block (#101: `@biomejs/biome` 2.5.15 → 2.6.4,
  `@types/node` 24.19.1 → 26.6.6) failed the new `devvit` CI job: Biome 2.6 formats Markdown
  and wanted to rewrite the generic `readme.md` table. `biome.jsonc` now excludes `**/*.md`
  (`npm test` verified green with both the current and the bumped versions). Dependabot PRs
  stay PR-only; `#101` is rebased onto this change and merges only after review.

## Unreleased — sync follow-up: production never inherits the devvit CI job or npm Dependabot entry (2026-11-01, no engine change)

- **Observed right after PR #100 merged:** `sync_prod.yml` also copies `.github/workflows/ci.yml`
  and `.github/dependabot.yml` (both are in `sync_prod.py`'s allowlist), so `7jkxmy9nvbc@7d0ece0`
  and `wvkhabh2s22@8b6ea84` received the new `devvit` CI job and the `/devvit/gaming-express`
  npm Dependabot entry although neither repository has a `devvit/` folder. Left alone, the job
  would fail on every cache auto-commit in production and Dependabot would report a permanently
  failing npm run.
- **Fix:** `ci.yml` `devvit` job is guarded with `if: github.repository == 'uesu/News-Express'`
  (the same guard `sync_prod.yml` uses) — skipped, not red, in production.
  `sync_prod.py` gains `filter_dependabot_bytes()`: `.github/dependabot.yml` is copied minus any
  `updates:` entry whose `directory` does not exist in the destination checkout (pip and
  github-actions entries at `/` are untouched; result byte-stable across runs). Module docstring
  guarantee 7 documents it. The next sync (this merge) repairs both production repositories.
- **Guards:** four new `r87 sync_prod:` checks — dev file carries the npm entry; the synced
  production copy drops it and keeps pip + actions; the filter is byte-for-byte identity when
  every directory exists; the production `ci.yml` carries the repository guard on the `devvit`
  job. Python suites ALL PASS. `testing area/` untouched; `tests/test_smoke.py` and
  `.github/scripts/sync_prod.py` are the only synced files that change.

## Unreleased — Devvit relay 0.0.3: pause switch, official accounts, Game-Express targets, CI (2026-11-01, no engine change)

- **Defect (live, 14:39–15:11 PHT):** `npx devvit settings set relayEnabled` → `false` did not
  pause the relay. The CLI stores the typed text, so the setting arrived as the string
  `"false"`; `enabledRaw !== false` stayed true and both ZZZ posts kept being re-sent (and two
  new ones, `1xkwfsz`/`1xkwk61`, were relayed correctly within 1–2 min). Fix: `parseEnabled()`
  treats `false`, `"false"`, `"0"`, `"no"`, `"off"`, `"paused"` as paused; anything unset or
  unrecognised stays enabled. Status toast now shows `relay on` / `relay PAUSED`.
- **Official publisher accounts:** new global setting `officialUsers` (comma list, default
  `genshinimpact,HonkaiStarRail,ZZZ_Official,HonkaiNexusAnima,AnantaOfficial`) polled with
  `reddit.getPostsByUser({sort:'new'})`. Records from an account feed carry the subreddit the
  post was actually made in (`u_<account>` for profile posts) — the spelling Game-Express's
  `RedditClient.items()` already filters on (`allowed_subs` = `u_<acc>` + game subreddits).
  Bootstrap key `boot:u/<account>`; a post seen in both an account feed and a subreddit
  listing is relayed once (`uniqueById`).
- **Game-Express targets in the defaults:** `subreddits` now also lists `Genshin_Impact,
  HonkaiStarRail,ZZZ_Official,WutheringWaves,HonkaiNexusAnima,AnantaOfficial`
  (`config/games.json` → `reddit.subreddits` in `uesu/Game-Express`, whose Special-Program
  fallback and community code corroboration ride the same RSS/redlib/Arctic chain that
  Reddit retires on 2026-11-13 / 2027-01-12). 12 + 5 calls per 2-min poll ≈ 8.5 req/min. The
  poll line becomes `poll: 12 subs, 5 users, N fetched, N sent, N seen, N failed, N bootstrapped`.
- `devvit.json`: `dev.subreddit = gaming_express_dev` so `devvit upload` from a fresh zip no
  longer announces a new playtest subreddit. Validated against `config-file.v1.json` (0 errors).
- **Directory page:** `devvit/gaming-express/readme.md` reduced to a generic description with
  no repository names or links (Reddit renders it on the unpublished app page). All operator
  documentation moved to the new **`docs/DEVVIT_SETUP.md`** (zip route in Command Prompt,
  expected outputs, settings commands incl. the full target lists, troubleshooting table with
  the `"Create" failed … fetch failed` upload error, data handling, clean uninstall, version
  history, roadmap for the News-Express and Game-Express intake readers).
- **Keeping it updated:** `.github/dependabot.yml` gains an `npm` block for
  `/devvit/gaming-express` (weekly, grouped, `deps(devvit)` prefix, labels `dependencies` +
  `devvit`); `ci.yml` gains a `devvit` job (`actions/setup-node@v7.1.0` SHA-pinned with a bare
  version comment per r89, Node from `.nvmrc`, `npm ci && npm test`) so a dependency bump must
  typecheck, lint, test and bundle before it can merge. Unit tests 12 → 16 (`parseUsers`,
  settings defaults + `dev.subreddit` guard, `parseEnabled` text forms, `uniqueById`).
- Nothing under `testing area/` or `tests/` changed; `sync_prod.yml` copies nothing from
  this entry; both production repositories are untouched. Python suites ALL PASS.

## Unreleased — Devvit relay 0.0.2: one post per post (2026-11-01, no engine change)

- **Defect (first live run, `r/GamingExpressRelay`, 14:21–14:27 PHT):** the same post
  `Zenlesszonezeroleaks_/1xkvvda` was relayed to `#reddit-intake` on every 2-minute poll
  (`poll: 6 subs, 150 fetched, 1 sent, 149 seen`) with rising score/comments. Cause: Reddit's
  listing ids are `t3_<id>`; bootstrap and the seen-lookup keyed on that, but the post-send
  marker was written under the bare `<id>` from the relayed record, so it never matched.
- **Fix:** `bareId()` normalises every Redis key (`seenKey`, `failKey`); the lookup also reads
  the v0.0.1 spelling (`legacySeenKey`, `seen:t3_<id>`) so upgrading never replays the 149
  bootstrapped posts. New unit test `redis keys: listing id (t3_x) and record id (x) map to
  the same marker` (12 tests). Record format, cadence, webhook body and settings unchanged.
- Deployment is manual on the owner's PC: zip → `npm ci` → `npm test` → `npx devvit upload`
  → `npx devvit install GamingExpressRelay` (upgrades the existing install to the new
  version). Nothing under `testing area/` or `tests/` changed; prod repos untouched.

## Unreleased — Devvit relay: `devvit upload` schema fix (2026-11-01, no engine change)

- `devvit/gaming-express/devvit.json`: the secret `intakeWebhook` setting no longer declares
  `defaultValue: ""`. Reddit's `config-file.v1.json` forbids `isSecret: true` together with
  `defaultValue`, so the first real `npx devvit upload` (owner's PC, Node 26.13.0, npm 11.20)
  failed with `settings.global.intakeWebhook is not exactly one from <GlobalStringSetting>…`.
  Validated the whole file against the schema shipped in `@devvit/shared-types@0.15.1`
  (0 errors after the change). New unit test `devvit.json: secret settings carry no
  defaultValue` (11 tests total) fails on the old file. Nothing under `testing area/` or
  `tests/` changed; prod repos are untouched by this entry.
- Context: PR #97 (Round 99 + relay app + survival investigation) merged to `main` on
  2026-11-01 04:10Z; `sync_prod.yml` deployed `0612504` to `7jkxmy9nvbc` (`2a4ab8a`) and
  `wvkhabh2s22` (`ca37b4a`); first live run on the new engine (`Reddit Feed Monitor #12070`)
  was clean.

## Unreleased — Round 99: megathread format corrections + REDLIB-REACH says why (2026-10-31)

### Card formatting (live `HonkaiStarRail_leaks/1xkgd9m`, applies to every post)

- **Escaped spoiler openers stay literal.** `\>!spoiler tagged text here!<` (the author
  *showing* the syntax) no longer becomes a broken `>\||…||` Discord spoiler that swallowed
  the next line; the plain-Markdown path now renders it `>!spoiler tagged text here!<`,
  exactly as the HTML path always did. Real `>!x!<` spoilers still become `||x||`.
- **Reddit quotes get Discord's space.** `>Spoiler Topic` → `> Spoiler Topic` (Reddit does
  not need the space, Discord does); `>>nested` flattens to one level like the HTML path.
- **Consecutive quote paragraphs join into one quote block** at the card-build choke point
  (`_format_quote_blocks`, every body source): `> Spoiler Topic` / `> >!…!<` / `> >!…!<`
  render as one bar instead of three bars with unquoted gaps.
- **One-column Markdown tables render.** `|Previous Megathreads|` / `|:-|` / `|[Latest
  Megathread](…) …|` / `| [All Previous Megathreads](…)|` used to reach the card as raw pipe
  lines (the detector required two cells). They now render as a titled list — heading line,
  then each row on its own line with blank lines between — and the same table with blank
  lines between its boundary-piped rows (Reddit's rich-text export) reads as one table.
  Prose with a pipe, a lone `|x|` line, and every round-66/71 malformed shape are still
  byte-identical; multi-column tables keep the round-71 row blocks. Links, URLs, wording and
  media are never altered.

### `REDLIB-REACH: 0/26` explained, and made self-explaining

- Investigated upstream: Reddit has answered anonymous thread JSON with a 403 since
  2026-10-20 (redlib#591) — every stock Redlib **post page** is an error page, which the
  round-83c detection correctly counts as `0/1` — and started blocking anonymous listings
  around 2026-10-29; the official instance list fell from 11 to 2–3 hosts. **v0.40.0
  (2026-10-22) is still the latest release and contains no post-page fix** (the fixes are
  unmerged PRs #603/#599 and forks). Not an engine or fleet defect; no fleet change
  (`redlib.cow.rip` stays deliberately excluded, `redlib.privadency.com` already seated).
- New log line, zero requests: `REDLIB-REACH-WHY: error-page:failed to parse page json
  data ×22, http-403 ×3, timeout ×1` follows `REDLIB-REACH:` whenever a probe missed.
  Non-200s, non-HTML, challenge splashes, error pages, timeouts and exceptions were all
  silently discarded before. The `REDLIB-REACH:` line, the run record and the workflow
  summary are unchanged.

See [Round 99](history/ROUND_99.md) for the screenshot/log provenance, the approved payload,
the upstream timeline and limits.

## Unreleased — Round 98b: the liveness evidence-source line stops contradicting itself (2026-10-30)

### Summary fix (output only — no engine behaviour changes)

- Run **#11658** printed:
  ```
  - Unverified (posted): 0
    - evidence source: arctic-lookup: 8
  ```
  `liveness_probe_by_source` counts **every** verdict (live / removed / unverified) by
  the evidence it used, but the summary nested it under the *unverified* counter — so the
  block read "0 unverified" directly above "8 sources". The three posts in that block had
  in fact been **held on positive evidence** and then released by the round-98 override.
- It is now its own top-level line: `- Evidence source (all verdicts): arctic-lookup: 8`.
- Nothing else changes: no delivery path, no cache, no gate. `Write monitor run summary`
  is 14,720 characters (guard 16,000, GitHub cap 21,000), and the smoke suite asserts the
  misleading nesting cannot come back.

## Unreleased — Round 98: stale archive snapshots no longer strand live posts (2026-10-30)

### Two holds that outlived their evidence

- **The archive's "removed" verdict is only a snapshot.** Six `r/HonkaiStarRail_leaks`
  "Official" posts (Fun with Aha, Affinitive Eidolon, Star Lotto, the 4.7 program brief,
  4.7 bonuses, 4.7 trailer) and one Genshin post sat in `pending_reddit.json` as
  `liveness_removed` for 2–4 h **while reddit.com's own listing carried them** — they
  were captured in the mod queue, approved later, and the archived row still said
  `removed_by_category`. New rule: a snapshot `removed` verdict is overridden when BOTH
  (a) the post is in **Reddit's own feed** this run (the combined feed, or a reddit.com
  per-subreddit feed — never a redlib/eddrit proxy and never the archive) and (b) it has
  been listed there for **3 consecutive runs** (`STALE_SNAPSHOT_TICKS`, ~15 min at the
  5-minute cron). A removed post leaves reddit's own listing within minutes, so it
  cannot reach the streak; one run without the post resets the count. **Live post-JSON
  evidence is never overridden** (`post-json` is a live read; only `arctic-entry` /
  `arctic-lookup` snapshots qualify).
- **A held post that no source lists any more was never re-read.** `HonkaiStarRail_leaks_1xjdkwf`
  froze at `last_checked` 12:10Z because it had dropped out of both the feed and the
  archive sweep; nothing in the pipeline ever looked at it again. New pass: up to
  `RECLAIM_MAX_PER_RUN` (5) held posts per run that nothing has listed are re-read from
  the archive in **one batched `ids=` request**, oldest first, only for retryable
  reasons (`liveness_removed`, `liveness_unverified`, `not_live`, `pending approval`,
  `sources_down`) and only inside the 48 h window. A clean record is re-admitted into
  the **existing** pipeline (dedup, both liveness gates, fresh hold, flood cap); a still
  removed record just gets `last_checked` refreshed. Archive errors are a no-op — a post
  is never posted on a guess, and `removal_notice` holds are never reclaimed (they
  return only via RSS).
- Cost: **one** extra archive request per run, and only when a reclaim candidate exists
  (typically 1–2 keys). Both decisions are visible in the summary —
  `Stale-snapshot overrides: N` with the keys, and `Held posts re-probed: N` with
  `re-admitted / still removed` plus one line per probe.
- **Edge cases closed before merge** (each has a check): a record with no usable
  timestamp is never re-admitted and never writes a bogus `published_ts`; a future
  timestamp is clamped so the fresh-age floor cannot hold a post forever; a record whose
  own subreddit disagrees with the pending key is never re-admitted (no wrong-channel
  post); a held key for a subreddit that is no longer tracked is skipped before it costs
  an archive request or a "no webhook" ERROR line; the summary skips malformed entries
  and truncates long text.
- `AGENTS.md` size table updated (largest step script 14.5 KB). Smoke suite gains eight
  checks that **execute** both new pure functions (streak reset, native-only listing, no
  post-JSON override, reclaim selection/limit) **and five that run the real `main()`**
  with the network mocked (reclaim → delivered, override at streak 3 → delivered, streak
  1 → still held, still-removed reclaim → held with the clock refreshed, `removal_notice`
  → never reclaimed and no archive request).
- Three real bugs were caught before merge: `num()` called without its `tail` argument
  in the summary (the step would have exited 1), `native_keys` initialised only in the
  feed branch (TEST POST mode → `UnboundLocalError`), and the reclaim pass placed *after*
  the "no candidates" early return (a quiet tick would have skipped exactly the holds it
  exists to rescue).

## Unreleased — Round 97c: the summary step is a third smaller (2026-10-30)

### Hardening after the 21,000-character outage

- **The `Write monitor run summary` script is now 14,079 characters** (was 21,058 at
  the failure, 19,622 after the first fix). The 21,000 cap that rejected the whole
  workflow in prod #11568 is now 6.9 KB away, and the smoke suite fails above
  16,000.
- What was removed, and what was kept:
  - dropped: duplicate feed-fallback triple (the `- Feed fallback:` line carries it),
    the legacy `Selected media provider` / `Quality upgrades accepted` /
    `Validated base retained` branches that only ran on pre-round-21 records, the
    duplicated `Subreddits represented` + `Combined subreddits covered` pair, and the
    long inline comment blocks;
  - kept, unchanged in wording: every coverage line (feed per subreddit, missing subs,
    archive per subreddit with posts/empty/failed/circuit open), delivered posts with
    latency, known-pending keys, held keys with evidence, waiting keys with age and
    floor, the effective-settings line, REDLIB-REACH with its warning, dedup pressure.
- Shared helpers (`load`, `v`, `dstr`, `line`, `num`) replace repeated inline
  formatting, so future additions are one line each.
- `AGENTS.md` gains a **HARD LIMIT** section: the 21,000-character rule, how the guard
  enforces it, why YAML parsing and CI cannot detect it, and the rule that engine-known
  text is formatted in the engine, not pasted into the workflow.

## Unreleased — Round 97b: keep the summary step under GitHub's script cap (2026-10-30)

### Regression fix (prod Reddit monitor)

- **Round 97 broke prod load, and the smoke suite could not see it.** Its ~2.5 KB
  of summary formatting pushed the `Write monitor run summary` step's `run:`
  script to **21,058 characters**; GitHub refuses any step script over
  **21,000**, so the *entire* workflow became unloadable — prod run **#11568**
  (2026-10-30 08:40Z, `3b4b518`) failed with
  `Invalid workflow file … (Line: 302, Col: 14): Exceeded max expression length 21000`,
  and no job was even created. `yaml.safe_load` and the offline suite both
  passed: the limit lives only in GitHub's loader.
- **The settings line is now built by the engine** (`_settings_line()`), and the
  workflow prints it with two lines. The greeting-style formatting lived in the
  workflow only because the value was not known there; the engine always knew it.
  The summary step is back to **19,622** characters (main was 18,549).
- **Guard**: the smoke suite now fails if *any* `run:` script in either workflow
  exceeds **20,000** characters — a 1,000-character margin under GitHub's cap —
  so this class of breakage can never reach production again.

## Unreleased — Round 97: the summary states the settings it ran with (2026-10-30)

### Observability only (no delivery decision changes, no extra requests)

- **The effective settings are printed, not inferred.** Run #11563 (`08:15Z`)
  ran with `FRESH_HOLD_SECONDS: 60` from the operator Variable and reported
  `2 fresh-hold`, but the effective floor (the code default is 30 s) was only
  visible in the runner's own env dump. The engine now records the values it
  resolved and the summary prints one plain line:

  `**Settings:** fresh hold 60 s · recheck 300 s · window 48 h · flood cap 25 · dedup 250/sub (10000 total) · liveness probe on (lenient, budget 10)`

  A disabled floor/probe reads `fresh hold off (0 s)` / `liveness probe off`
  rather than a bare zero.
- **Posts waiting on that floor are named**, with the age and the floor that
  held them (up to 10, then `… N more waiting post(s) not shown`):

  `- waiting: WutheringWavesLeaks_1xj9k2p — 41.3 s old (floor 60 s)`

  Before this, `Fresh-age hold: 2` was a count with no names — the same gap
  round 96c closed for liveness holds.
- `_effective_settings()` reads module globals at call time, so a renamed
  constant yields one `unavailable` value instead of an exception; records
  written by earlier rounds render exactly as before.

## Unreleased — Round 96c: the Reddit summary names the posts it held (2026-10-30)

### Observability only (no delivery decision changes, no extra requests)

- **A hold is now a key and an evidence string, not a count.** Run #11548
  (`07:00Z`) printed `Liveness not verified: 1` and
  `Known-rejected archive candidates: 5`; the one post it refused —
  `AnantaLeaks_1xj8et0`, "One of the Apartments you can get in Ananta",
  removed by the moderators — could be identified only from the Actions log
  line `[AnantaLeaks_1xj8et0] post not verified live (...) — skipping`. The
  summary now prints, for each held post (up to 10, then
  `… N more held post(s) not shown`):
  `- held: AnantaLeaks_1xj8et0 — 'removal_notice' (live-source, source=arctic): live source vxreddit still shows a removal notice (whole-body marker)`
- **Suppressed known-pending keys are named too**, with a bounded tail:
  `- keys: Genshin_Impact_Leaks_1xhnc6b, … … 3 more`.
- Both lists live in the existing run-result record (`hold_keys`,
  `known_pending_keys`), so the artifact carries the same names the summary
  prints; each list is capped at 10 entries in the engine, so a flood run
  cannot grow the record.
- Records written by earlier rounds (no `hold_keys` / `known_pending_keys`)
  render exactly as before.
- The recorder takes the run-stats dict and a field name, so a missing or
  renamed field degrades to "no names in the summary" instead of raising inside
  the loop that posts: observability can never cost a delivery. Cost is
  0.19 µs per call and at most ~2.4 KB on a worst-case run-result record.

## Unreleased — Round 96b: the Twitter summary names accounts, posts and refusals (2026-10-30)

### Observability (workflow summary only; no engine change, no extra requests)

- **Which account failed is now a name, not a count.** The summary lists every
  account with its outcome — `Ananta_EN: ok via nitter.cf — 17 entries`,
  `PomPom_HonkaiSR: FAILED — no working nitter instance this run`,
  `Wuthering_Waves: empty feed (0 entries)` — bounded to 12 lines, host only
  (no path or query), sorted.
- **Delivered keys are listed** (up to 10, with `… N more not shown`) instead of a
  bare "posts delivered: 3", plus a `… more` note when truncated.
- **Refused backlog entries are named with their age**
  (`TYPEII_EN_2115271059188613499 — 46.1 h old`, up to 5), so the 46/94/257-hour
  backlog of run #12043 is verifiable from the summary alone.
- **Log truncation is called out**: when the number of `V3 Posted` / `STALE-SKIP`
  lines disagrees with the engine's authoritative `V3 SUMMARY` line, the summary
  says so and tells the reader to trust the engine value.

## Unreleased — Round 96: the Reddit run summary proves coverage without the log (2026-10-30)

### Observability (no delivery-path change, no extra requests)

- **A quiet subreddit is now a stated fact, not an inference.** Run #11533
  (`05:45Z`) fetched 100 combined-feed entries covering **5 of 6** subreddits;
  `HonkaiNexusAnimaLeaks` had no entry (it takes ~2 contributions a week) and the
  archive legitimately returned nothing for it. That was provable **only** by the
  *absence* of an `Arctic Shift search unavailable` line in the Actions log — which
  nobody can check later without the log. The summary now prints:
  - `Feed entries by subreddit: …` and
    `Subreddits missing from the combined feed: HonkaiNexusAnimaLeaks`,
  - `Archive coverage: 5 subreddit(s) without RSS news tried — 4 with posts,
    1 empty (nothing inside the posting window), 0 failed, 0 skipped (circuit open)`
    plus a `by subreddit: … =empty` breakdown,
  - a **WARNING** line whenever an archive lookup *failed* or hit the circuit
    breaker, so "unconfirmed" can never read as "nothing to post".
- **Delivered posts are listed, not just counted**:
  `Genshin_Impact_Leaks_1xj77do — video/native-dash, 1 item(s), LATENCY 2.8 min`
  (with `held as '<reason>'` when a hold preceded it and the Discord message id).
- **FULL MODE availability is in the summary**: `FULL MODE post-JSON probe: http_403: 1`
  and *"native mode this run"* — the `post JSON HTTP 403 — native mode` line used to
  exist only in the log.
- New run-record fields: `feed_subreddits_with_entries`, `feed_subreddits_missing`,
  `arctic_by_sub` (`posts`/`empty`/`failed`/`circuit_open`), `arctic_subreddits_*`
  counters, `delivered_posts`, `json_probe_by_status`. All are additive: a round-95
  record still renders unchanged.

### Engine logging

- `[arctic <sub>] no posts in the last 48 h — nothing to recover from the archive`
  is emitted on an empty archive answer, so an *attempted but empty* lookup no longer
  looks like a subreddit that was never tried.

## Unreleased — Round 95d: the round-95c guard crash in production CI (2026-10-30)

### Fix

- **A documentation check crashed both production CIs after the round-95 merge.**
  `uesu/7jkxmy9nvbc` run #332 and `uesu/wvkhabh2s22` run #417 both failed at the same line:
  `tests/test_smoke.py` opened `README.md` unguarded. `README.md` is **dev-only** —
  `sync_prod.py` deliberately keeps it out of both production repositories — so the check
  raised `FileNotFoundError` in a tree where every engine, workflow and test assertion had
  already passed. Nothing in delivery was affected (the monitors run on their 5-minute cron,
  not on CI), but the safety gate was red.
- **Fixed by skipping the check when the documentation is absent**, exactly like the
  round-90 credits check does: a production checkout now asserts the round's knob is still
  wired and skips the README knob table instead of crashing.
- **New self-audit (`r95d`) so this class of bug cannot return:** the suite parses its own
  syntax tree and fails, by name and line, if any read of `README.md`, `AGENTS.md`,
  `.env.example` or `docs/**` sits outside an existence guard or a `try/except`. It resolves
  simple path aliases too (`p = .../README.md; open(p)`), which is the shape of the bug.
  The audit itself is self-tested four ways (literal, guarded, variable, `try/except`).

### Proof

| Tree | Before | After |
| --- | --- | --- |
| dev (`README.md` present) | 1238 PASS | **1240 PASS**, 0 FAIL |
| production-shaped (no `README.md`, no `docs/`, no `sync_prod.yml`) | `FileNotFoundError` | **1235 PASS**, 0 FAIL |
| production-shaped + mutated to the pre-fix unguarded read | — | **FAIL r95d** naming the exact line, then the old crash |

## Unreleased — Round 95c: stale-backlog guard, one-tick re-check wait, agent-readable Twitter summary (2026-10-30)

### Correctness

- **A degraded nitter fleet can no longer turn an old backlog into "new" posts.**
  Run #12043 (`2026-10-30T00:55Z`) had four mirrors return 502 and one 429 while every
  account still reported `feed OK`, and `TYPEII_EN` posted three tweets that were 46 h,
  94 h and 257 h old. Those three keys were **never** in `posted_tweets.json` before that
  run (checked across all 100 commits that touch the file), so they were first-time posts
  of an old backlog, not duplicates: the dedup cache only protects keys it already holds.
  New `TWITTER_MAX_AGE_HOURS` (default **24**, `0` = off) refuses any feed entry older than
  the floor, logged as `STALE-SKIP`, **before** the tweet-data fetch — so a stale feed costs
  zero requests. Age is judged by **two witnesses** — for an own tweet the **tweet id**
  (immutable, so a mirror that re-stamps an old entry or mangles the date cannot smuggle
  it through); for a repost the feed date, so reposting an older tweet still posts. Ages are
  read as **UTC** (`calendar.timegm`), so a local UTC+8 machine cannot shift the floor.
  Unknown age still posts (fail-open) and `TEST_TWEET_ID` is exempt. No delivery-path change, no added
  request on a normal run. See `docs/history/ROUND_95C.md`.

### Timing

- **`PENDING_RECHECK_SECONDS` default `1800` → `300`** (one 5-minute cron tick). A post held
  for a transient reason was waiting up to 30 min for its re-probe while the workflow ran
  every 5 min, so an approved post could sit missing for 25 extra minutes. At 300 s the hold
  is re-checked on the next run. Removed/deleted posts are still never re-checked
  (`_NO_RECHECK_REASONS`), and the extra work is bounded by the round-95 probe budget;
  `PENDING_RECHECK_SECONDS=1800` restores the old wait.

### Observability

- The Twitter engine now prints one machine-readable state line
  (`V3 SUMMARY: posted=… dedup_skipped=… stale_skipped=… cache_missing=… cache_keys=…
  max_age_hours=…`) and the workflow summary renders it under **Dedup / backlog state**,
  with a stale-backlog count, an explicit `engine: unavailable` when the line is missing,
  and a re-post warning when the dedup cache could not be persisted. Workflow logs are not
  readable by later agents; the step summary now carries the state.

### Tests

- 12 new guards (stale floor and fail-open paths, guard ordering before the fetch,
  `TEST_TWEET_ID` exemption, summary rendering with and without the state line, cache-failure
  warning); the round-30/32 throttle guards were retargeted to the 300 s default.

## Unreleased — Round 95: independent pre-delivery liveness probe + Reddit summary pressure reporting (2026-10-30)

### Correctness

- **A delivered post must now survive an independent liveness check, not just a proxy
  answer.** The round-20/32/93 gate is satisfied by any proxy response on the RSS path, and
  a proxy serves a removed post's pre-removal title, body and media (live 2026-10-29:
  `1xijfzb` auto-removed 6 s after submission, delivered 4.6 min later; `1xifykm` removed
  by an AutoModerator karma rule; `1xifc1c` still awaiting moderator approval at delivery).
  `candidate_liveness_verdict()` reads an **independent record** — the FULL-MODE post JSON
  or the archive row already in hand (**0 requests**), else ONE Arctic lookup by id
  (`/api/posts/ids`, 8 s cap) — and maps `removed_by_category`: `automod_filtered` →
  `pending approval`, any other non-empty value → `removed by moderators/filters`, plus the
  existing title/body markers. A clean existing record is positive proof of life.
- **Lenient by default, strict by Variable.** `liveness_hold_decision()` holds only on
  positive evidence unless `REDDIT_LIVENESS_STRICT=1`, so in the default mode this change
  cannot withhold a live post (an unverifiable post posts exactly as before). Holds are
  written to `pending_reddit.json` — never to the dedup cache — and retried. The hold reason
  is `liveness_removed` / `liveness_unverified`, both **outside** `_NO_RECHECK_REASONS`:
  the archive record is a snapshot, so a removal it reports may since have been reversed, and
  reusing the never-re-check vocabulary would have turned a stale snapshot into a permanent
  hold (the round-34 shape). Held posts are re-probed every 30 min and post as soon as the
  record is clean.
- **Bounded cost.** `LIVENESS_PROBE_BUDGET` (10 lookups/run), `LIVENESS_PROBE_TIMEOUT`
  (8 s), nothing in DRY RUN or TEST POST mode, nothing on a run with no candidates, and an
  isolated failure counter so a liveness lookup can never disable the media/archive paths.
- **`verify_archive_post_live()` no longer claims `live via redlib`** when the answer came
  from the combined RSS feed: it now says `live via redlib/rss fallback`. The 2026-10-29
  logs printed `live via redlib` while `REDLIB-REACH` was `0/26`.

### Observability

- **Reddit run summary gains a `### Liveness` block**: probe enabled/disabled,
  lenient/strict, verified live, held as removed/queued (by reason), unverified (posted),
  evidence source (`post-json` / `arctic-entry` / `arctic-lookup`) and skipped — so a held
  post is explainable from the summary without the Actions log.
- **Dedup-cache pressure is reported**: `- Dedup cache: N key(s), M dropped at the cap this
  run (hot: <sub>=<n>)`. Saturation and evictions were log-only warnings before.
- **`REDLIB-REACH` is printed once**: the engine stores the line with its prefix, so the
  summary used to render `Instances (REDLIB-REACH): REDLIB-REACH: 0/26 …`.
- **All-mirrors-down warning**: when the run probed ≥1 mirror and none answered, the summary
  says page-based checks were unavailable instead of leaving a bare `0/26`.

### Notes

- No Redlib page probe was added: the 2026-10-29 logs show **0/26 instances answering in
  every run**, so it would be dormant exactly when needed. The round-93 classifiers remain
  available for the day the fleet recovers.
- Verified offline: smoke 1215 (was 1189), signals 103, Twitter media ALL PASS,
  compileall clean, workflows parse (Reddit still 7 steps), zizmor identical to base,
  10/10 mutations caught. See `docs/history/ROUND_95.md`.

## Unreleased — Round 94: Twitter run diagnostics, run-result presence, opt-in 350 MiB cap (2026-10-28)

### Observability

- **Twitter run summary gains a *Diagnostics* block** with fixed-category counts of
  Discord delivery errors, FxTwitter fetch errors, unresolved media-heal lines,
  media-heal edit errors and dedup-guard errors. The block states that these are
  matching **log lines, not unique posts**, and prints
  `diagnostic coverage: unavailable (empty or missing log)` when the captured log is
  empty or missing — a run that produced no log is not five zeros and is not healthy.
  Only counts are printed, never log content.
- **Reddit run summary reports the run-result record itself**: `read`, `missing`,
  `invalid shape`, or `unreadable or malformed` (`**Run-result record:** …`). The
  status is a closed vocabulary, so a malformed or wrong-shaped
  `reddit_run_result.json` is distinguishable from a clean empty run, and the record's
  contents are never echoed.
- **An absent `TWITTER_CACHE_RESULT` now reads `not-reached`** instead of `failed`: a
  cache read that never ran (the monitor step failed before the persist step) is not a
  cache failure. Matches the wording the Reddit summary already used.

### Opt-in 350 MiB video cap (X)

`TWITTER_HIGH_VIDEO_LIMIT` raises `VIDEO_SIZE_LIMIT` from the proven 256 MiB to 350 MiB
in **both** X engines (V3 and the V2 alternative). It is deliberately strict opt-in:
only `1`/`true`/`yes`/`on` (case- and space-insensitive) select 350 MiB — unset, empty,
`0`, `false`, `off`, `350` and any other value keep 256 MiB, so a typo cannot raise a
live posting limit. `twitter_monitor.yml` maps it from a repository **Variable**, so the
effective cap does not move until a maintainer sets it. No other cap exists behind it
(`GALLERY_VIDEO_LIMIT` is still off, and the constant now has a single source of truth).

### Guards

- `r94` (smoke, 6 contracts): the empty-but-existing log (`tee` creates the file before
  the monitor writes a line) reports `unavailable` rather than zero counts; every
  diagnostic category still matches a real engine log line; the Variable is mapped in
  the Twitter workflow only; unset keeps 256 MiB with the gallery sub-cap off; the cap
  has one source of truth; and the Reddit run-result status is a closed vocabulary whose
  line never carries record content.
- `test_twitter_media.py`: both engines at the 256/257/350/351 MiB selection boundaries
  (real media selection through mocked sizes, not just parsing), plus the default and
  opt-in parsing cases.

See [Round 94](history/ROUND_94.md) for the control runs and limits.

## Round 93: removed link-spam liveness, Redlib removal comments (2026-10-28)

### Liveness (the leak this round closes)

Production run `#10864` posted `Genshin_Impact_Leaks_1xh7jl3` ("Daily Free PSN Codes"
by `u/Chef-Goat` → external spam URL) **after Reddit had already removed it**
(AutoModerator karma threshold, then the spam filter):

* it never appeared in the live RSS feed and entered only through `_ArcticEntry`
  (`feed_ok=False`);
* `vxreddit` answered HTTP 200 with its generic `vxReddit` shell and no media, and
  `redditez` returned "No data";
* upstream **Embeddit ignores `removed_by_category` on removed non-self link posts**:
  HTTP 200, pre-removal title, the external link as `body`, `media=[]`;
* `verify_archive_post_live` trusted that media-less stub and returned
  `(True, "live via embeddit")`.

The fix is in the classifier, not in a new gate:

* a **media-less `embeddit` answer never vouches for an archive-only candidate by
  itself**. Redlib corroborates instead, and the corroboration now reads the removal
  shapes a 2026 removed post actually leaves: Redlib's
  `[removed] — [view removed post](…)` placeholder body, Reddit's
  `[ Removed by Reddit on account of … ]` policy banner, and an **official removal
  comment** (`AutoModerator` / `*-ModTeam`) on the post page.
* a silently spam-filtered external link (no removal marker anywhere) is caught when
  Redlib's `<a id="post_url">` points at an external non-Reddit URL that contradicts
  the title **and** vxReddit answered with its placeholder — i.e. Reddit served the
  page but the content moved, which is what a filter does.
* `live_removal_reason` (the retraction path) uses the same three signals and stops at
  the first parsed page instead of walking all 28 mirrors.
* `base_from_redlib_page` keeps hyphens inside usernames, so `u/Chef-Goat` is no
  longer truncated to `Chef`.

### Not changed (deliberately)

Live RSS posts (`feed_ok=True`) and archive posts whose `embeddit` answer carries media
are verified immediately, with **zero** extra requests — unchanged. Routine
AutoModerator stickies, future-tense warnings, quoted text and non-moderator replies
never classify as removals. `REDDIT_RSS_INSTANCES` (28), `PROXY_SERVICES`,
`DISCOHOOK_PREVIEW`, inline/CMAF video resolution and crosspost hydration are
untouched, and `verify_archive_post_live` keeps its exact 4-parameter signature.

### Guards

* `r93` (smoke, 11 contracts) — the exact `1xh7jl3` replay (archive candidate +
  media-less embeddit stub + AutoModerator removal comment → rejected, fast mirrors
  probed first, stops at the first parsed page), live-RSS and media-bearing-archive
  paths verified with zero Redlib probes, the silent external-spam case, the routine
  sticky case, the vxReddit-outage case, `live_removal_reason` behaviour, the
  hyphenated username, the placeholder recorder, and engine↔signals classifier parity.
* `r93` (signals, 8 unit guards) — the three removal shapes, the benign shapes that
  must stay clean, and the external-URL helpers.

See [Round 93](history/ROUND_93.md) for the reproduction, the per-hunk control runs,
and the limits.

## Round 92: Redlib fleet 25 → 28, inline rich-text video, crosspost media, request savings (2026-10-27)

### Reddit media

- **Inline rich-text video** (`/link/<post>/video/<id>/player`) is now first-class: a post
  whose only media is an inline player (`1xgnbtu` → `1xgncao`, `media=None`) resolves the
  video instead of rendering text, and a post that pairs photos with a video keeps **both**
  (photo `MediaGallery` + video `MediaGallery`). Several videos in one post resolve in
  document order, and every candidate video ID is probed **at most once per post** — a dead
  or 404 video is not retried by the supplement pass.
- **`extract_vreddit_id`** additionally parses `/link/<post>/video/<id>/player` and defers to
  the supplement pass when the post also carries inline photos, so mixed posts are not
  half-resolved at base time.
- **`_drop_gallery_media_lines`** now strips resolved video URL lines (bare and
  self-labelled `/player` / `v.redd.it` / embed-mirror forms) while keeping real captions,
  prose, and *unresolved* fallback links.

### Crossposts

- A crosspost whose parent is known only by ID (`t3_<id>` without a path) is hydrated
  before resolution, so **crossposts from unmonitored subreddits** recover the original's
  media — single image, single GIF, rich-text photo/GIF sets, and video — plus the
  `🔁 Crosspost of [<Subreddit>](…)` attribution. `arctic_media_items` (ordered gallery →
  rich-text `media_metadata` → single `i.redd.it` destination) backs that, and
  `_arctic_media_hint` now unwraps the original.

### Request savings

- `enrich_gallery_redlib` probes the 10 verified post-page-capable mirrors first (Wave 1)
  and only falls back to the remaining 18 in fleet order (Wave 2) when Wave 1 misses: up to
  10 requests instead of 28 per post, **0 coverage loss** — the waves are a partition of the
  fleet and a Wave-2-only mirror still resolves (both guarded).

### Pre-merge hardening (`r92b`)

- **No duplicate video tile.** A `vxreddit`/`embedez` permalink-shaped mp4
  (`…/comments/<id>/<slug>/redditvideo.mp4`) carries no `v.redd.it/<id>`, so the inline-video
  supplement pass used to re-probe it and add a second tile. An opaque video now consumes one
  slot, both in `resolve_post_media` and in `_drop_gallery_media_lines` (bounded: one opaque
  video removes at most one body line, so an unresolved fallback link survives).
- **No `/vid/` false positives.** `INLINE_REDDIT_VIDEO_RE` and `REDDIL_PLAYER_VIDEO_RE` are
  boundary-anchored, so third-party URLs (`video.twimg.com/…/pu/vid/1280x720/…`,
  `example.com/foo/vid/…`) are no longer read as Reddit video IDs.
- **Source-silent CMAF-only videos** resolve: `v.redd.it/<id>/CMAF_{720,480,360,240}.mp4` is
  appended after the DASH ladder, so a video whose `fallback_url` is `None` and whose DASH
  renditions 404 still lands instead of dropping to thumbnail-only.
- **Loop-flagged `RedditVideo`** (`isGif: true` with no `s.gif`) is treated as video, while
  `AnimatedImage` with `s.gif` stays a GIF.
- **Harness fix with teeth:** round 92's case-1 proxy mock returned a tuple, which
  `resolve_post_media` treats as "no proxy result" — the case passed without ever exercising the
  proxy branch. It is a dict again, and the guard now asserts the fixture shape (control run:
  the tuple fails the check).

### Guards

- `r92b` — the five edge cases above, plus the bounded-stripping rule.
- `r92` — fleet order/`28`-member shape, `PROXY_SERVICES` unchanged, the retro-locked
  `DISCOHOOK_PREVIEW` default, inline-video parsing, `arctic_video_info` mixed-video
  deferral, media-line dropping, the full `1xgnbtu → 1xgncao` card contract, Wave-1 savings
  and Wave-2 coverage, the three external-crosspost media classes, mixed photo+video
  galleries, and the dead-video single-probe rule.

See [Round 92](history/ROUND_92.md) for provenance, the divergence from the sibling patch,
and limits.

## Unreleased — Round 91: production-sync hardening + CPython 3.14.9 (2026-10-26)

### Production sync (both live repos)

- **Fixed a live production failure.** `uesu/7jkxmy9nvbc` and `uesu/wvkhabh2s22`
  were failing every `Python version bump (auto)` run at *Rewrite the allowlisted
  current-runtime files* with `::error::Expected runtime file missing: README.md`:
  `sync_prod.py` copies `python_version_bump.yml` into both production repos but
  never copies `README.md` or `docs/*`, which sat in the mandatory allowlist. The
  allowlist is now split into **required** surfaces (present in every checkout)
  and **optional** dev-only ones (rewritten where present, skipped with a
  `::notice::` where absent), and the `docs/PYTHON_RUNTIME.md` slug `sed` is
  guarded.
- **No more pin downgrades.** `.github/scripts/sync_prod.py` merges workflow files
  monotonically instead of overwriting them: a `python-version:` pin or SHA-pinned
  `uses:` that production already advanced is preserved, so a dev-side sync can no
  longer undo a production Dependabot/Python bump. The deployed
  `tests/test_smoke.py` r39 pin is re-aligned to the deployed `ci.yml` afterwards.
- Dev-only root markdown (`PRIVACY_POLICY.md`, `TERMS_OF_SERVICE.md`) joins the
  exclusion list, and the unused `import json` is gone.

### Runtime

- CPython pin `3.14.8` → `3.14.9` across the allowlisted runtime surfaces (the
  `actions/python-versions` Linux x64 build published 2026-10-21). Documentation
  now states the runner-image publication date instead of a CPython release date
  this repository cannot verify, and version examples are version-agnostic so the
  automated rewrite cannot turn them into nonsense.

### Guards

- `r91a` — every **mandatory** allowlist path must exist in a real production
  checkout; every **optional** one must genuinely be absent there.
- `r91b` — newer production pins survive a dev-side sync, dev-side workflow
  content still lands, the deployed r39 guard re-aligns, and the merged tree is
  idempotent.
- `r91c` — dev-only root markdown is excluded and never synced.
- `r89c` — reworked: it now runs the real rewrite shell in **both** layouts and no
  longer invents fixtures for missing files (that fixture is exactly why the
  production failure went unseen).

See [Round 91](history/ROUND_91.md) for the reproduction, evidence and limits.

## Unreleased — Round 90: multi-page indicator, proxy stats for text posts, formatting preservation (2026-10-26)

### Reddit delivery

- Long posts now say where you are: the main card ends `… • 📜 Page 1/N` and every
  continuation ends `-# 📜 Page n/N`. Single-page cards are byte-identical to before
  (no `Page 1/1`), and the printed page count is settled by a bounded fixed-point
  loop so it always matches the number of continuation messages actually sent.
- Text-only posts keep the `💬`/`👍` counts a proxy already observed (the `else`
  branch now reuses the same text/stats helper), and `fetch_proxy_post` backfills
  stats from a sibling wave responder instead of dropping them. Counts are never
  forced or fabricated: no source, no counts.
- Formatting survives delivery: HTML `<strong>`/`<b>`, inline CSS bold spans,
  `<h1>`–`<h6>`, `<i>`/`<em>`, `<del>`/`<s>`/`<strike>`, Markdown `####`–`######`
  subheadings (rendered as `**bold**`) and native `>!spoiler!<` (rendered as
  `||spoiler||`) outside code spans. JSON `selftext` is cleaned with a
  paragraph-preserving helper whose HTML detection is tag-agnostic — a narrow tag
  list leaked raw `<pre>`, `<code>` and inline-styled `<span>` markup into cards.
- Splits close and reopen fenced code blocks and inline `**`/`||`/`~~` emphasis
  across page boundaries inside the character budget; `~~…~~` and inline code are
  now protected spans.

See [Round 90](history/ROUND_90.md) for provenance, the corrected HTML router,
fuzz/parity evidence and limits.

## Unreleased — Round 89: zizmor-verifiable pins, CI annotation hygiene (2026-10-26)

### Development surfaces (no runtime/live change)

- Make every workflow action pin auditable by online `zizmor` again: version
  comments are bare `# vX.Y.Z` (prose on the line above), `actions/setup-python`
  moves to `v7.1.0` (`6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`), and
  `actions/checkout` / `actions/github-script` keep their commits with exact
  `v7.0.1` / `v9.0.0` tags. `runs-on: ubuntu-latest` stays everywhere so runner
  OS updates roll forward automatically.
- Fail the smoke suite (`r89d`) if the suite's own stdout ever emits a GitHub
  Actions workflow command (`::error::`, `::warning::`, `::notice::`, `::group::`,
  `::endgroup::`), so simulated faults cannot annotate a green run.
- Cover the dev-only `.github/workflows/sync_prod.yml` Python pin in the runtime
  bump when the file is present and skip it with a notice when it is absent (both
  production repositories receive the bump workflow but never `sync_prod.yml`);
  a missing required surface still fails closed.

See [Round 89](history/ROUND_89.md) for the reproduction, guards and limits.

## Unreleased — Round 88: full Reddit text and Twitter recovery (2026-10-25)

### Integration and final edge checks

- Integrate the complete sibling handoff for full Reddit text and queued Twitter GET revalidation.
- Persist multipart main-card ambiguity before POST, retain delayed-completion evidence for a full retention window, and reject malformed nested continuation progress before resuming.
- Report cache-load failure as incomplete, count resumed progress as saved local state, and bound Twitter revalidation GETs to 15 seconds. Exhausted recovery logs describe observed metadata without asserting Discord refused the asset.
- Retry proven pre-send connector failures without reconciliation; keep uncertain-response holds.
- Add interruption/rejection/restart/retention regressions and refresh local compatibility/CPU benchmark evidence in the PR. Existing deployment remains gated on a reviewed merge.

### Round 88: continuation and Twitter recovery handoff

- Reconcile setup/privacy/tracking documentation with the tested full-body and pre-edit revalidation enhancements. Correct stale three-page and retraction-only cache instructions; ignore atomic-save scratch files. No engine, provider, media-heal, schedule, Secret or Variable changes in this documentation follow-up.
- Preserve earlier history and record the authorized cap replacement, compatibility evidence, request/storage costs and recovery limits in [Round 88](history/ROUND_88.md).

### Retain dedup evidence after the last continuation

- Recover main-card dedup from completed continuation records as well as partial ones. A crash after the last page save but before the ordinary dedup save must not repost a completed card. Recovered keys count as newly saved keys for retention and persistence checks.
- Add an offline restart regression exercising the actual main loop, saved message IDs, missing dedup file and a repeated feed entry; it failed before the repair.

### Complete Reddit body continuations

- Remove the 16,000-character ingestion cap and three-continuation cap. Deliver all retrieved text in content-driven pages, keeping main-card media, stats and buttons intact. This intentionally supersedes Round 66’s cap.
- Persist continuation payloads, confirmed page IDs and next index independently of retraction. Resume explicit rate-limit rejections after Retry-After; stop at the first failure and hold uncertain outcomes for reconciliation instead of skipping or duplicating pages. Keep webhook credentials out of state.
- Cover part five, 40k-plus text, ten-plus pages, unbroken tokens, all message IDs, disk round-trip retry, and ambiguous-response holds offline. No production backfill or cache reset.

### Revalidate Twitter media before recovery edits

- Re-read queued Discord messages after the existing recovery delay and before each PATCH. Skip edits when no eligible unresolved media remains; stop on 401/403/404. Transient revalidation failures retain the existing bounded recovery.
- Preserve video-only defaults, identical PATCH payloads, four-attempt ceiling, proxy priority and GIF conversion. Healthy posts never enter this path; each queued attempt adds at most one GET.
- Offline media tests cover resolved-during-wait, still-unresolved, unavailable revalidation, and deleted/inaccessible messages. No production messages or caches are modified by testing.

## Unreleased — attended workflow updates (2026-10-18)

- Keep eligible package-only Dependabot auto-merge; require attended merges for
  workflow-path updates, including renamed/deleted files. Fetch all PR file pages.
- Continue Python detection/validation/publication but remove Python auto-merging;
  the legacy AUTO_MERGE_PYTHON_BUMP variable is no longer consulted.
- Preserve News exact pins, current validation and new-minor soak period.
- GitHub security approval can still be required; check real live execution
  after an attended update. No posting/state/scheduler or dependency-range change.

## Unreleased — application-only scope (2026-10-17)

- Improve existing summary output in place; no new reporting module or runtime
  file. Keep unmeasured values unavailable and preserve real cache-push status.
- Clarify privacy/terms disclosures for retained logs/summaries and repository
  access; preserve attribution and warranty provisions.
- Recover crosspost motion media from validated one-hop originals; reuse
  completed archive lookups (including misses/errors) and embedded parent data.
- Correct timestamp-prefixed Twitter feed counters in the existing workflow.
- Leave dependency/Python/Dependabot/update automation and posting/state rules
  unchanged. Proposed code, not a claim of production deployment.

Current, in-progress release notes for News-Express. This file covers
**round 63 onward** (2026-10-05 and later) — the state after "The Great
Simplification" rewrote the Reddit engine's delivery pipeline.

For everything before that, see the historical archive:

* [`docs/history/CHANGELOG_ARCHIVE.md`](history/CHANGELOG_ARCHIVE.md) — full dated changelog, rounds 1–62
* [`docs/history/ENGINE_HISTORY.md`](history/ENGINE_HISTORY.md) — detailed round-by-round engine notes
* [`docs/history/`](history/) — decision records per incident (`ROUND_*.md`) and other dated snapshots

Entries below are newest first. As this file grows, older entries may be
moved into `docs/history/` and replaced here with a pointer — they are never
rewritten when that happens, only relocated.

## Unreleased / current

* **2026-10-24 — Round 87: Automated dev → prod repository sync (`.github/workflows/sync_prod.yml` + `.github/scripts/sync_prod.py` → `uesu/7jkxmy9nvbc` & `uesu/wvkhabh2s22`).**

  - **Automated atomic multi-repo sync:** Runs `compileall` and all three offline suites (`test_smoke.py`, `test_reddit_signals.py`, `test_twitter_media.py`) on every push to `main` (and on manual `workflow_dispatch`) before atomically syncing `testing area/`, `tests/`, `.github/scripts/`, `.github/workflows/{ci,dependabot_auto_merge,python_version_bump,reddit_monitor,twitter_monitor}.yml`, `.github/dependabot.yml`, `.gitignore`, and `requirements.txt` to both `uesu/7jkxmy9nvbc` (Reddit prod) and `uesu/wvkhabh2s22` (Twitter prod) in a single commit per repo — eliminating the Round-75 "smoke guard landed before engine" manual upload race.
  - **Strict live cache protection & concurrent monitor retry:** Never creates, overwrites, stages, or deletes `posted_reddit.json`, `pending_reddit.json`, `proxy_health.json`, `posted_tweets.json`, or `posted_messages.json`; excludes dev-only docs (`docs/`, `README.md`, `AGENTS.md`, `.env.example`) and `sync_prod.yml` itself from production; retries with `git fetch` + `reset --hard FETCH_HEAD` if a 5-minute monitor cache commit lands mid-push; and falls back to non-workflow sync with a clear warning if the token (`secrets.PROD_SYNC_PAT || secrets.BUMP_PAT`) lacks `workflow` scope.

* **2026-10-24 — Round 86: Reddit fleet expansion (23 → 25), `REDLIB-REACH:` Step Summary, and 6 production log fixes (`#9626`, `#9651`, `#9659`, `#9662`, `#9669`, `#9677`).**

  - **Reddit fleet expansion (`23 → 25`):** Appends `https://redlib.reallyaweso.me` (`[23]`, live-verified `200 OK` on `/r/<sub>/new`, `/user/<acct>`, and `/r/<sub>/comments/<id>/`) and `https://redlib.ducks.party` (`[24]`, `v0.40.0` `200 OK` `/r/<sub>/new` listing with inline gallery carousels) at the tail of `REDDIT_RSS_INSTANCES`, preserving indices `0..22` with zero deletions.
  - **Step Summary instance telemetry (`REDLIB-REACH:`):** Records `redlib_reach`, `redlib_reach_answered`, `redlib_reach_probed`, and `redlib_instances_configured` in `reddit_run_result.json` and surfaces `- Instances (REDLIB-REACH): ...` under `### Providers and media` in `.github/workflows/reddit_monitor.yml` `$GITHUB_STEP_SUMMARY` with `monitor.log` fallback and zero network calls.
  - **Flood-cap ordering fix (`#9651`):** Moves `known-pending` (`_pending_throttle_skip`) and stateless `FRESH_HOLD_SECONDS` filtering ahead of `cap_new_posts(new_posts, MAX_POSTS_PER_RUN)` so suppressed archive ghosts no longer inflate `len(new_posts)` and falsely trigger `POST FLOOD GUARD` drops.
  - **Duplicate proxy wave & gallery enrichment skip on archive video posts (`#9662`):** `fetch_proxy_post_memo(..., need_video=True)` now reuses an already-cached `(id, path, False)` liveness probe when it holds a motion video (`_proxy_result_has_motion_video`), and `resolve_post_media()` gates `enrich_gallery_redlib` on `not (has_video or arctic_is_video or base.get("vred_id") or base.get("redgifs_url"))`.
  - **Exact `reddit.com` host check & error-shell detection:** `_is_direct_reddit_host()` checks exact `reddit.com`/`www.reddit.com`/`old.reddit.com` hostnames so `[17] https://safereddit.com` is no longer skipped by substring matching (`"reddit.com" in instance`), and `_is_redlib_error_page()` detects backend-issue, clearnet-retired, rate-limit, and `__goaway_challenge` shells.
  - **Accurate provider attribution & tie-break logging (`#9626`, `#9659`, `#9669`, `#9677`):** `resolve_post_media()` tracks `media_provider` (`vxreddit`, `embeddit`, `redditez`, `arctic`, `redlib`, `native`, `full`) and `proxy_media_used`, logs `card media via arctic` on the `arctic_items` gallery branch, eliminates `provider=unknown` / `| native |` misattribution on proxy-resolved image cards, and logs `tied ... preferring higher-priority <service>` on equal-count priority tie-breaks in `reddit_proxy.py`.

* **2026-10-23 — Round 82: Reddit fleet expansion (19 → 23, Game-Express PR #63 parity).**

  Adopt Game-Express PR #63 `fabbe4c` live-verified 2026-10-23 Redlib fleet: `19 → 23` entries with **zero hosts deleted** (keep `redlib.nohost.network` + `redlib.kylrth.com` which Game-Express excludes as traps/Azure-gated). **Round 83b fix:** preserve R78 19-member order exactly (`www`/`old`/`miningtcup`/`catsarch`/`privacyredirect`/`snoo`/…/`nadeko` 0-18) and **append** 4 new hosts at tail (19-22: `mint.lgbt`, `jeremyh.xyz`, `jeikobu.net`, `vanillax.me`) so they do not affect prior 19 priority — PR #76 had moved `mint.lgbt` to head and `www`/`old` to Tier 3, causing `REDLIB-REACH 11/23` with `catsarch`/`snoo`/`miningtcup`/`nohost`/`idevicehacked` `0/1` → `redlib gallery enrichment failed (all instances)` → every post `archived counts` with `media=text|native|0` (observed #9560/#9563 `HonkaiStarRail_leaks` `1xd8ofn`/`1xd8vra`, ZZZ `1xd8ppc`). Appended tail restores media (`catsarch` etc. priority unchanged) while keeping new hosts for redundancy (R78 order verbatim; `privacyredirect` stays at #4). **Savings/calls unchanged:** concurrent first-win `_fetch_new_listing` (8 s) + combined RSS `1 req/run` + `REDDIT_FEED_TOKEN` memoization `≤1 JSON req/run` — Tier 3 tail 0 hits while Tier 1 healthy. Tests: `R78 19 preserved 0-18`, `r82 23-member appended tail` + `no-deletion` 19→23, `SMOKE TEST: ALL PASS`.

* **2026-10-23 — Round 80: emoji outside link (Discord forward fidelity).**

  AnantaLeaks `1xd1tks` `"You'll never guess where the game starts😂"` posted as `### […😂](url)` — renders in-channel but Forward shows raw `([https://…/… ) *by` leak (Discord Components V2 `### [title](url)` strict). Trailing emoji now outside the markdown link: `### [clean](url) 😂` for **all future posts** (every sub, every title) via `_split_trailing_emoji80` (`unicodedata So/Sk` + `ZWJ/VS/skin-tone/flag` sequences, `clean.rstrip()`); empty-title guard keeps `😂`-only titles inside. Original HTML/JSON/sources untouched, presentation-only, 0 extra req, no perf loss. `compileall OK`, `SMOKE TEST: ALL PASS` (emoji helper unit + full suite).

* **2026-10-23 — Round 79: token-powered JSON-first instant fallback.**

  JSON-first: `REDDIT_FEED_TOKEN` on `auto` (default) now powers `www.reddit.com/comments/{id}.json?limit=25&raw_json=1&{feed_q}` FIRST (host/path-agnostic `format_reddit_feed_query`, `BROWSER_HEADERS`), instant 1-request fallback to combined `.rss` on datacenter 403. Stagger capped `min(FEEDTOKEN_JSON_STAGGER,2)` for token tier vs `65 s` anonymous, 403 remembered per run (`_feedtoken_json_failed`), ≤1 JSON req/run (first new post only, memoized). No Secret/Variable change needed (`auto` valid token = enabled, empty/invalid = OFF per r31, `force`/`off` unchanged); header `1b` wording updated from stale Round-31-only to Round 79.


  Tests: `r31 auto without app OFF` preserved, R25 extraction intact, `SMOKE TEST: ALL PASS`.

* **2026-10-22 — Fleet refresh: 16-member Twitter + 19-member Reddit fleets + docs cleanup.**

  Twitter V3 expanded from 12 to 16 (Round 77 2026-10-22): Teapawt operator expansion adds `teapaw.org`, `teapawt.net`, `teapawt.org` (same 4cuck/teapawt 0.19.0 stack as `nitter.cf`/`xitter.cf`, verified same SOCKS5 exit + `fetch_page` top-id parity), plus `nitter.mie.foundation` from Codeberg shitter wiki (verified RSS top-id parity) — both placed as trials per runner-evidence rule (no datacenter-block host above a non-blocking one). Reddit V3 refreshed to 19-member `REDDIT_RSS_INSTANCES` (same code already on `main`): 8 verified dual-path hosts (`catsarch`, `privacyredirect`, `snoo.habedieeh.re`, `tiekoetter.com`, `nohost.network`, `privadency 1/2`, `idevicehacked`) + 5 listing-only reserves (`artemislena`, `awy.one`, `kylrth.com`, `freedit.eu`, `utilibre.org`) + 3 tail restores (`privadency.com`, `safereddit.com`, `nadeko.net`) kept at tail per live prod #9283 2026-10-22 03:35 UTC `REDLIB-REACH 4/9` partial/timeout-still-works verdict. Docs fully cleaned: README resilient-feeds count, Nitter credits order (16), Redlib credits (19, refreshed 2026-10-22), PRIVACY/TERMS Redlib instance lists, AGENTS invariant, plus earlier 2026-10-21 pristine removal consistency (PRIVACY/TERMS/CI_SMOKE). Historical snapshots under `docs/history/` intentionally preserved verbatim per header.

* **2026-10-21 — Reddit delivery cleanup: pristine-listing removal, accurate completion/persistence reporting, secret-redacted diagnostics.**

  Remove the mandatory pristine listing-confirmation dependency (`LISTING_CONFIRM` parsing, cache, `_fresh`/`no-cache` headers, gate branches, workflow wiring, docs/tests) per the approved handoff. The `FRESH_HOLD_SECONDS` floor (default 30 s, stateless) and posted-post deduplication are preserved. Useful pending suppression with bounded timed retries (48 h expiry, source-provenance `rss`/`arctic`), provenance-aware RSS reconsideration (still subject to removal checks; archive/media presence not proof of visibility) and bounded transient retry are retained.

  Reddit logs now use stage-accurate aggregated `INFO` (considered/entering/delivered/known-pending/retry-backoff/fresh-hold/etc., removal/liveness at `INFO` with conditional wording) with per-candidate `DEBUG`; the misleading “Found X new Reddit posts” wording is removed. The Actions run summary is derived from a stable local `reddit_run_result.json` record (inline YAML Python, validates JSON object, handles missing/malformed/wrong-shape as `unavailable`, no scraping or extra network calls):

  - Completion is `completed` true only after required work including persistence; `normal`/`no-candidate`/`dry-run` completed vs `failed`/`interrupted` incomplete (not by JSON write/`finally`), dry-run explicitly labelled (`skipped_dry_run`), no claim of live delivery/persistence for dry-run; failures during or before required persistence are `incomplete` with `not-reached` (only never-started) vs `failed` distinction (preparation/copying/recovery-reset/staging/commit/push failures all `failed`, entered defaults to `failed`, confirmed no-change `unchanged`, confirmed `saved`), and `finally` does not overwrite success.
  - Local persistence (`unchanged`/`saved`/`failed`/`not-reached`/`skipped_dry_run`, preparation `git config`/`git add`/`cp`, copying `mktemp`/`cp`, recovery `fetch`/`reset`/`merge`/`staging`/`commit`, and push failures all `failed`) and repository persistence (same set, observed commit/push, `unchanged` vs `saved` distinct, dry-run explicit; local save not conflated with repository push) are reported separately and not conflated; the real workflow persistence shell is syntax-checked with `bash -n` and mocked for `unchanged`/`successful push`/`recovered push`/`copying`/`recovery-reset`/`staging`/`commit`/`push` `CACHE_RESULT` in tests (no copied test-only shell).
  - Error messages are sanitized and bounded (webhook URLs, `token=` query, `Authorization:[^\n]*`/`Bearer` redacted to `[REDACTED]`, bounded 500 chars, exception type/operation/category preserved, safe diagnostics retained; no leak in JSON/summary/logs; delivery decisions unchanged; original exception remains observable).
  - Provider/media diagnostics are retained locally without extra network requests, distinguishing zero vs unavailable and reported separately when observed: proxy warmup `ok`/`disabled`/`failed`/`unavailable` with service map, video quality mode `balanced` default (`highest`/`compatibility`), media resolved via provider, final media endpoint/hosting category, final card media kind and tile count, optional quality candidate result, whether validated base was retained, terminal media fallback (proxy→native, distinct from feed fallback `ok`/`partial`/`all_failed`/`not_attempted` and quality fallback), heal queued/edit-performed/skipped-after-revalidation; neither warmup, HTTP validation, player controls nor “chain complete” proves audio inclusion and Embeddit remains video-only; per-candidate logs remain supporting evidence. Production baselines #8982 (`1xbbdbs` direct video retained after EmbedEZ failure (HTTP 400, `quality_candidate_unavailable`), 1 tile, 3 buttons, `8ace078`), #8988 (`1xbby22` vxReddit image retained after Redlib enrichment failure (not terminal fallback, provenance preserved), `caa7421`) and #8989 (`1xbc1mn` vxReddit 720p retained after EmbedEZ failure (HTTP 400, `quality_candidate_unavailable`), heal queued then skipped after revalidation cleared, `60fb8f7`) are recorded as successful baselines, not defects requiring audio/muxing/provider rewrite or repost/edit (new counters not emitted by historical runs; expected new reporting for equivalent mocked scenarios).

  Documentation, `.env.example`, `AGENTS.md`, `README` and `docs/REPOSITORY_TRACKING.md` updated; `reddit_run_result.json` remains reporting-only, ignored per-run (not delivery state, not cache-merge input, not Twitter state); historical audits preserved. Tests moved into existing suites (no standalone formatter/cleanup-test file) and verify normal/no-candidate/dry-run/failure paths, unchanged-vs-saved, secret-redaction, provider diagnostics and summary-generation without network.

* **2026-10-20 — Plain-text profile crosspost attribution.**

  The `🔁 Crosspost of u/<name> Profile` line for profile crossposts
  (`/user/`, `/u/`, `/r/u_<name>/` permalinks) is now plain text — the
  user-profile Markdown hyperlink is removed from this branch only. The
  username and `Profile` wording stay; subreddit crosspost links, Read Post
  destinations, crosspost resolution, source selection, media, statistics
  and delivery/rate-limit behavior are unchanged. Future deliveries only —
  no edits to already-posted Discord messages and no state reset.

* **2026-10-19 — Table/continuation documentation housekeeping.**
  Align README, `.env.example` comments and the CI guide with the merged generic
  HTML/Markdown table renderer and removal of generated continuation labels.
  Keep supported-shape limitations explicit. No runtime, workflow, settings,
  cache, schedule or delivery changes; no new Variable or live test required.

* **2026-10-19 — Remove generated Reddit continuation labels.**

  Follow-up body messages now start directly with the remaining source text,
  without the bot-added `(continued)` heading or a leading newline. Keep
  the same accent, message count cap, 3800-character component limit,
  safe Markdown splitting and overflow tail. Source-authored wording is
  unchanged. Future deliveries only; no edits or reposts of existing messages.

* **2026-10-19 — Reddit HTML table preservation (future posts).**

  Run #8358 delivered WutheringWavesLeaks `1x9geq7`, but its RSS HTML
  table became a flat list before the Markdown-only formatter could run.
  Preserve innermost rectangular HTML tables with TH headers before tag
  stripping and render them as bold row headings plus `- Column: value`
  bullets, using the same formatter as Markdown tables across subreddits.
  Decode entities, preserve literal dates, wording, links and pipes; leave
  unsupported spans, layout tables and malformed widths to existing cleanup
  rather than infer missing structure. No network, gates, state, media,
  continuation limits or historical messages are changed. Regression input
  for `1x9geq7` is a screenshot transcription, not a fetched raw capture.
  Deploy the engine file after review; do not reset or replace production
  caches. Already-flattened upstream text cannot safely be reconstructed.

* **2026-10-15 — Round 76: the runner-clean head + the xcopy.uk verdict.**
  `xcopy.uk`'s round-75 seat-3 trial ended with a measured runner refusal:
  Game-Express's first four post-merge runs (#2662–#2665, 2026-10-14
  17:19–17:30 UTC) got HTTP 403 on all six handles, every run, from four
  Azure regions (westus, westus3, eastus2, centralus) — 24/24 fetches
  refused — while an off-runner probe the same afternoon read a clean 8/8
  body with `nitter.cf` parity: the `nitter.kareem.one` signature. The
  operator set this round's ranking rule — **no member that blocks GitHub
  Actions / Azure datacenter IPs (or datacenter IPs generally) sits above one
  that doesn't** — and directed the head for both monitors: the operator pair,
  then `nitter.meowing.monster` (4 → 3) and the token-gated
  `nitter.miningtcup.me` (8 → 4), making the chain head entirely runner-proven
  for the first time. The probe round ranked the rest on union coverage (all
  eight handles both monitors watch): `nitter.freedit.eu` 5 (8/8, zero
  refusals anywhere), `nitter.gravitywell.xyz` 6 (5/8; `GenshinImpact` gap
  newly observed alongside Wuthering_Waves/HonkaiNA), `tw.eir-nya.gay` 7
  (passes the rule but holds the only measured runner non-deliveries and
  429-throttled every GE-handle probe), then the measured runner refusals:
  thepixora 8 (flapping 403), kareem 9 (standing 403), **xcopy 10 — demoted,
  not deleted**. The walled tail stays last. Membership stays twelve; the
  operator pair untouched; Reddit untouched. The smoke suite pins the new
  exact order; the r75 "eir-nya ahead of the token fallback" relative guard is
  updated in place into the round-76 rules. See
  [`docs/history/ROUND_76.md`](history/ROUND_76.md).

* **2026-10-15 — Housekeeping (same PR as round 76): stale words and dead
  constants.** No behavior change. `twitter_v3.py` drops three never-referenced
  leftovers — the retired round-34 `MAX_CACHE_SIZE = 500`, an unused
  `MAX_AGE_SECONDS` and the unused `_env_float` twin (the float reader lives
  in `reddit_proxy.py`, where it is used) — rewrites the pre-round-59 fleet
  header above `RSS_INSTANCES` into the current serial-chain / runner-evidence
  / demote-not-delete rules, and fixes the `docs/ROUND_56.md` →
  `docs/history/ROUND_56.md` pointer. Everything that still described two
  offline suites now names all three: `python_version_bump.yml` runs
  `tests/test_twitter_media.py` in both of its verify steps (it had claimed
  parity with CI since round 73 without it), and `README.md`,
  `docs/CI_SMOKE.md`, `docs/DEPENDABOT.md` and `docs/PYTHON_RUNTIME.md` say
  so. The README's "11-instance" fleet line and its round-59 credits order are
  replaced by the twelve-member round-76 order and ranking rule, the
  troubleshooting entry no longer sends you to the retired tracker method, and
  `docs/REPOSITORY_TRACKING.md` joins the docs index. `AGENTS.md` gains the
  fleet invariant (operator pair, no-datacenter-block rule, demote-not-delete,
  engine-before-guard deploy order) and lists every current topic guide;
  `.env.example`'s round-63 note names the checks that actually remain. A
  duplicate `import tempfile` leaves `tests/test_smoke.py`. On operator
  request the pass also dropped the identical retired `MAX_CACHE_SIZE = 500`
  from `reddit_main_v3.py` (cosmetic; no behavior change, no guard depends on
  it) and corrected the displayed text of six `docs/history/` links that
  still read `docs/ROUND_NN.md` after the 2026-10-05 move (targets were
  already correct).

* **2026-10-14 — Round 75: Twitter RSS fleet re-ranked + Redlib RSS audit record.**
  The initial `nitter.meowing.monster` demotion was reversed the same day
  after the host revived around 13:35 UTC (d420 healthy from 13:45; version
  `2026.10.12-f97b733`; 5/6 handles served from IPv4 runners). The earlier
  production precheck saw no meowing delivery, but the serial chain had
  stopped at an earlier serving host and had not tested its recovery. The
  operator directed `xcopy.uk` to seat 3 after an 8/8 full-coverage parity
  test against `nitter.cf`; the probe round ranked meowing 4, `tw.eir-nya.gay`
  5, `nitter.freedit.eu` 6, thepixora 7 (recent runner-403 watch), token
  fallback miningtcup 8, `nitter.gravitywell.xyz` 9 and `nitter.kareem.one`
  10. The fill-in sweep grows the fleet from ten to twelve: freedit.eu (5/5
  current bodies, no runner history) and gravitywell.xyz (3/5, complementary
  gaps to kareem.one) enter as trials; `nitter.pp.ua` is excluded as a
  thepixora feed alias. The operator pair remains in seats 1–2; the two
  challenge/interstitial hosts remain at the tail and nothing is deleted.
  Reddit V3 remains comments-only: all six Redlib `.rss` candidates returned
  the same upstream Reddit 400, the HTML `/new` listing remains usable, and
  list membership/order plus native-first behavior and round-64 checks are
  unchanged. The smoke guard pins the final 12-member Twitter order and
  unchanged Reddit membership. No workflows, proxies, gates or media paths
  changed. See [`docs/history/ROUND_75.md`](history/ROUND_75.md).

* **2026-10-13 — Round 74: Reddit cold Discord video-proxy healing.** Reddit
  V3 now recognizes the observed cold-proxy response: a video tile has a
  Discord `proxy_url`, but does not yet have both positive dimensions and a
  `video/*` content type. The existing explicit non-positive-dimension signal
  remains supported; sparse metadata without a proxy attempt is still unknown
  and is not queued. Initial delivery, selected provider/URL, and the delayed
  revalidation path are unchanged: after the default six-second wait, one
  Discord GET skips the edit if the proxy has resolved, otherwise at most one
  identical PATCH is sent. Healthy videos, photos, provider selection and
  Twitter behavior are unaffected. Focused offline regression checks cover
  cold, sparse-without-proxy, healthy, image-only, resolved-during-wait and
  still-cold cases. See [`docs/history/ROUND_74.md`](history/ROUND_74.md).

* **2026-10-13 — Round 73: Twitter mixed-media order + GIF fallback quality.**
  Two X (Twitter) V3 media-presentation fixes. (1) The gallery now follows the
  tweet's **canonical order**: FxEmbed/FxTwitter's `media.all` (its own
  `extended_entities` order — verified in the FxEmbed processor, not inferred)
  is read instead of photos-after-videos, so a mixed post keeps the observed
  live order `JPG → GIF 1 → GIF 2 → GIF 3` and GIFs/videos keep their
  chronological order relative to each other. Photo-only and video-only posts
  with valid media URLs preserve their previous order and output (entries
  without a usable URL are safely omitted instead of becoming empty tiles, the
  one deliberate difference for malformed payloads), providers without
  `media.all` (vxtwitter, twitterez) keep the legacy videos-then-photos order,
  and ordering costs no request and mutates no payload. (2) GIF fallback
  selection now classes every converter answer by its **actual returned
  content type** — an `image/webp`/`image/gif` animated answer wins, a `.gif`
  URL that answers `video/mp4` is rejected, and the extension is never
  trusted. An AVIF answer is remembered but never preferred: the **original
  mp4 always outranks it** (an AVIF can preview as a static frame in Discord's
  gallery while still animating when opened), and the AVIF is used exactly
  once per GIF as a last resort — a GIF whose mp4 is oversized, has no
  playable variant, and has no animated WebP/GIF rendition. The chain is
  probed **once per GIF** (`probe_gif_candidates`, ≤ 4 HEADs) and an AVIF it
  remembered is reused rather than re-discovered, so the last-resort path
  adds at most the 2 AVIF-route HEADs and never repeats the four candidates;
  the chosen AVIF's real source is logged as `<source>-avif`; if that is down
  too, the round-11 thumbnail + "Watch on X" fallback stands.
  The evidence-based heal contract is unchanged: healthy media posts
  immediately with no delay, no revalidation and no edit, only media Discord
  explicitly reports as unresolved and in scope enters the in-memory queue
  (one identical bounded PATCH after the posting loop), a provider fallback
  alone never triggers a heal, and no new Variable is wired. New focused suite
  `tests/test_twitter_media.py` (offline, wired into CI) covers canonical
  ordering, the chain and its content-type rules, mp4-vs-AVIF priority, the
  direct-mp4 fallback, the single-probe performance contract and the heal
  contract; the round-11/47/56/70 smoke guards pass unchanged. See
  [`docs/history/ROUND_73.md`](history/ROUND_73.md).

* **2026-10-12 — Round 72 follow-up: explicit-evidence + revalidated Reddit
  proxy-video heal.** The shipped round-72 pass inferred "unresolved" from
  missing metadata, so Discord's sparse-but-healthy create responses could
  re-edit a card that already rendered. Two corrections to the same one-card
  path: (1) a repair is queued only on explicit evidence — a returned
  `width`/`height` `<= 0`; omitted fields, `null`, non-numeric values and an
  empty `content_type` are unknown, not failure (empty type alone is no longer
  evidence); (2) the queued edit re-reads the delivered message
  (`GET …?with_components=true`) and PATCHes the identical payload only when
  one of the EXACT URLs the create response queued is still explicitly
  unresolved — a healthy or sparse revalidation means no edit, an unrelated
  video component in the same message can never trigger a PATCH, and a failed
  revalidation fails closed. Initially healthy videos are never flagged (no
  edit, no delay, no revalidation); a flagged candidate always spends one
  revalidation read, and no PATCH when it has rendered by then. Video classification
  stays provider-agnostic (video-rendition URL or Discord's `video/...` type,
  no proxy hostname list); native Reddit media and ordinary posts are still
  untouched, repairs stay bounded to one concurrent edit, and both Variables
  keep their defaults and workflow wiring. The round-72 smoke section grows
  from 24 to 59 guards, including the 2026-10-12 production regression and the
  URL-specific revalidation end-to-end through `main()`. See
  [`docs/history/ROUND_72.md`](history/ROUND_72.md).

* **2026-10-12 — Documentation/configuration audit: retain Reddit operational pending state.**
  Canonical `main` and both production repositories still run Reddit V3 code
  that reads and writes `pending_reddit.json`; the empty object is not evidence
  that the active cache is obsolete. Current docs now distinguish those
  operational rechecks from the stateless round-64 fresh-age/listing checks,
  clarify Twitter V3's response-based in-memory media-heal queue, document
  `MEDIA_HEAL_SCOPE`, and mark Round 72 shipped in merged PR #59. No runtime,
  workflow persistence, cache contents, or production repository was changed.

* **2026-10-12 — Round 72: Reddit proxy-video cold-start media heal.**
  Discord may initially show a 0×0 or failed tile for a video that becomes
  playable shortly afterward. Video cards request a message ID (`wait=true`)
  so the returned gallery metadata can identify unresolved video tiles.
  Only unresolved non-native videos get one identical same-message webhook
  edit after delivery and a bounded default 6-second delay; healthy videos
  get no edit. Detection covers future providers without a hostname list
  (refined by the follow-up entry below: a tile is covered when Discord
  returns a video type or the URL exposes a recognized video rendition, so an
  untyped extensionless URL is deliberately left untouched).
  Native media is not edited; ordinary cards, provider selection, YouTube and
  dedup behavior remain unchanged. `PROXY_VIDEO_HEAL=0` disables it;
  `PROXY_VIDEO_HEAL_DELAY` adjusts the delay (0–60 seconds). See
  [`docs/history/ROUND_72.md`](history/ROUND_72.md).

* **2026-10-11 — Round 71: Reddit Markdown-table readability.**
  The active Reddit V3 formatter now renders a detected Markdown table as
  compact, grouped row blocks — a plain label line (`Patch 3.7`) followed by
  one `- <column>: <value>` bullet per populated column, a blank line between
  rows, HTML entities decoded (`&amp;` → `&`), and a blank line before a
  `Q1:`-style FAQ question that follows text. This **supersedes the round-66
  rendering** (per-row `**bold-label**` bullets), which read as a wall of bold
  on mobile. Detection is unchanged: header row + a well-formed separator of
  the same width + a full run of data rows; malformed/glued tables and
  ordinary prose containing a pipe stay byte-identical, and nothing is
  date-converted (the card's 🕐 stays the only timestamp). The transform is
  local and linear in body length, runs at the single card-build choke point
  (RSS, FULL MODE, Arctic and proxy bodies all render identically), and adds
  no provider, proxy, media, cache, retry or Discord request; existing
  Components V2 text budgets still bound the output. Reddit media handling,
  provider fallback, cache behavior, continuation components, buttons and
  YouTube previews are unchanged, as is the round-67 no-content-decision
  policy. Review fix (PR #58): a following pipe line only counts as a table
  continuation when it has real table-row boundaries (leading/trailing `|`),
  so ordinary pipe prose (`Suoming | 5\* Electro Sword`) can no longer
  suppress formatting of the valid table above it — while mismatched
  boundary rows and glued tables still stay byte-identical. 16 new smoke
  guards (846/846; 96/96 signals). See
  [`docs/history/ROUND_71.md`](history/ROUND_71.md).

* **2026-10-11 — Round 70: bounded Twitter video media heal (4 attempts).**
  The default Twitter media-heal re-edit count rises from 2 to 4 for
  unresolved video tiles, hard-capped at 4 (`MEDIA_HEAL_ATTEMPTS`). The 45-second
  delay, immediate exit on resolved media, video-only scope, and 256 MiB
  preflight cap are unchanged. This does not add automatic 4K-to-lower-quality
  switching or cross-run healing. See
  [`docs/history/ROUND_70.md`](history/ROUND_70.md).

* **2026-10-08 — Round 69: Reddit provider-order docs + Arctic outage reasons.**
  The README and the Reddit V3 module comments now describe the live proxy
  priority/tie-break order (`vxreddit → redditez → Embeddit rewrite`), dispatched
  as bounded concurrent waves rather than a serial chain. The stale V3 header
  that said EmbedEZ was absent from the quality path is corrected: EmbedEZ is an
  optional, validated 1080p candidate. The Arctic Shift search diagnostic now
  logs the exception class name when `str(exception)` is empty
  (`Arctic Shift search unavailable: TimeoutError`). HTTP messages such as
  `HTTP 422` and descriptive exception text are unchanged. Offline smoke
  coverage was added for blank-exception Arctic failures. No provider order,
  request, retry, timeout, probe, cache, posting, scheduling, quality-selection,
  or image/GIF/gallery/non-video behavior changed. See
  [`docs/history/ROUND_69.md`](history/ROUND_69.md).

* **2026-10-08 — Round 68: Reddit video-quality fallback diagnostics (logging only).**
  The optional EmbedEZ quality path now logs `candidate=embedez` separately
  from the dynamically identified retained-base provider, with an explicit
  fallback reason when the candidate is unavailable or is not accepted as a
  superior validated result. It keeps the stable `retaining validated base`
  phrase used by the existing local workflow-summary counter. The retained
  base provider is labeled dynamically (`vxreddit`, `embedez` for
  EmbedEZ/RedditEZ, `embeddit`, `native-dash`, or conservatively `unknown`
  for unrecognized hosts). The accepted-upgrade message and
  candidate-selection logic are unchanged.
  No provider order, reliability fallback, request/probe, timeout, quality
  budget, cache, deduplication, posting, Discord payload, scheduling, retry,
  or image/GIF/gallery/non-video behavior changed. URL text is not quality
  evidence; unprobed dimensions/audio stay unverified/unknown. The summary
  remains local-log-only and its fallback-notice count is not a complete
  quality-decision count. See
  [`docs/REDDIT_VIDEO_QUALITY.md`](REDDIT_VIDEO_QUALITY.md) and
  [`docs/history/ROUND_68.md`](history/ROUND_68.md).

* **2026-10-07 — Round 67: content-gate removal + video quality selection.**
  **Part 1 — complete removal of the content-advisory gate.** The Reddit
  engine no longer reads, classifies, holds, caches or logs any
  content-advisory metadata: the gate, its four repository Variables, the
  batched archive lookup, the Redlib badge reader, the crosspost-source
  checks, the allowlist and the fail-closed "unknown metadata" hold are gone
  from `reddit_main_v3.py`, `reddit_signals.py`, `reddit_monitor.yml`,
  `.env.example`, the tests and the current docs. A case-insensitive search
  for the removed names returns nothing in any active file; the truthful
  record of the removal — every removed name and behavior — lives in
  [`docs/history/ROUND_67.md`](history/ROUND_67.md). The remaining
  protections are unchanged: dedup cache, `FRESH_HOLD_SECONDS`, the pristine
  `/new` listing confirmation, the pending-recheck throttle, archive
  liveness, media handling and the opt-in retraction seatbelt. No cache,
  webhook, secret, proxy-order, image, GIF, photo or gallery behavior
  changed. **Part 2 — video quality selection.** `resolve_video_url` is now
  quality-aware and fully bounded: EmbedEZ 1080p and vxreddit are attempted
  together (vxreddit started first — it stays the winner path and the
  immediate fallback), a validated EmbedEZ 1080p result may replace it,
  EmbedEZ 720p is only tried when vxreddit itself is unusable, and the
  durable `v.redd.it` DASH ladder is the reliability floor before the
  thumbnail + Read Post button. Every candidate is validated (status,
  content type, HTML/JSON error body, 256 MiB limit, candidate timeout, and
  real MP4 dimensions + audio-track evidence read from the byte prefix) —
  a URL containing "1080" is never proof of quality, and signed/expiring
  `packaged-media.redd.it` URLs are never card media and are never
  persisted. New `REDDIT_VIDEO_QUALITY` Variable: `balanced` (default),
  `compatibility` (the pre-round-67 ladder, byte-order identical — the
  zero-code rollback) and `highest`. Strict budgets keep latency bounded:
  8 s quality window (15 s in `highest`), 20 s per proxy candidate, 10 s per
  native candidate, 40 s per post, 180 s of quality attempts per run.
  The opportunity covers every path that can put a Reddit video in a card —
  including the **proxy-delivered** video (the default configuration): there
  the round-49 wave's validated mux is the held base and one bounded EmbedEZ
  1080p candidate may replace it only against the base's own probe facts,
  while `compatibility` keeps that video verbatim with zero extra requests.
  Images, GIFs, photos and ordinary galleries make no quality requests at
  all. The module header of `testing area/reddit_proxy.py` was also
  corrected (comment-only) to describe the round-49 wave dispatch and the
  vxreddit-first tie-break accurately, and the confirmed acceptance policy
  is committed as `docs/VIDEO_ONLY_QUALITY_POLICY_CONFIRMATION.md`.
  Evidence and the manual canary checklist:
  [`docs/REDDIT_VIDEO_MEDIA_REPORT.md`](REDDIT_VIDEO_MEDIA_REPORT.md) and
  [`docs/REDDIT_VIDEO_QUALITY.md`](REDDIT_VIDEO_QUALITY.md). **Part 3** — the
  manual media test report is committed as the round's evidence base.

* **2026-10-06 — Python automation documentation sanitation.** Current docs
  now spell out CPython 3.14.8, patch/minor/major terminology, wheels-only
  runtime bump validation, the 30-day new-minor soak, `AUTO_MERGE_PYTHON_BUMP=yes`
  as patch-only, `BUMP_PAT` as a secret reference only, the explicit runtime
  rewrite allowlist, and the absence of any direct-to-main fallback. Dependency
  docs now match the grouped Dependabot configuration, and production scope is
  clarified: News-Express development docs/history are not copied into the
  separate production repositories. Historical 3.14.7 records remain historical.
* **2026-10-06 — Docs: changelog moved under `docs/`.** Current release notes
  moved out of the README and into this file; the README's Changelog section
  is now a short pointer to `docs/CHANGELOG.md` (current) and `docs/history/`
  (archive), matching the structure used by Game-Express. No entries were
  rewritten — only relocated — and historical dates/versions in
  `docs/history/` were left untouched.
* **2026-10-05 — Docs: stale-gate sweep.** The current docs no longer
  describe gates that round 63 deleted. `AGENTS.md` drops the
  `mod_queue_reason` fixture invariant (the function no longer exists) and
  rewrites the duplicate-media landmine as history — the rule that survives
  is "do not reintroduce any media-fingerprint gate". `docs/CI_SMOKE.md`
  drops the removed `page_is_post_page` page-identity check and its
  shell-page scenario, stops calling the smoke suite's gate list a "queue"
  gate, and re-attributes the listing fixtures to the round-64 pristine
  listing confirmation and the round-44 retraction seatbelt — the checks
  the suites actually run today. The Privacy Policy and Terms of Service
  keep the same `/new` listing disclosures but credit them to those two
  consumers instead of the removed mod-queue gate (effective dates
  bumped). The 2026-10-01 audit record moved to
  [`docs/history/REPOSITORY_TRACKING_2026-10-01.md`](history/REPOSITORY_TRACKING_2026-10-01.md)
  with a historical-snapshot banner, and every reference was repointed. No
  engine, workflow, or test changes.
* **2026-10-05 — Round 66: long-post continuations + table rendering + stale env cleanup.**
  A post body that no longer fits the card's text budget is no longer
  truncated: the main card keeps the first chunk (identical layout —
  header, gallery, stats, buttons) and the remainder is delivered as up to
  3 follow-up messages — text-only Components V2 containers, same accent
  color, each opening with a small `-# (continued)` heading; beyond the
  cap the last message ends with `… full post on Reddit`. Retraction
  covers every part: continuation message IDs are recorded alongside the
  main card's, so the tombstone/delete pass hits them all. Every split —
  the main budget AND continuation boundaries — lands on a safe point
  (paragraph break → line break → space) and never inside a link, bare
  URL, `||spoiler||`, or bold/italic marker pair, fixing the live 1wxfuj5
  card that was cut mid-link (`[Set](https://…` rendered broken). Markdown
  tables — which Discord does not render — now convert to per-row
  `**bold-label**` bullets (the first header composes with the first cell:
  `**Patch 3.8**` + `- **Drip Market:** October 9/10, 2026` + …, matching
  the hand-checked example); malformed or ambiguous tables stay
  byte-identical and nothing is date-converted (the card's posted-time 🕐
  stays the only timestamp). `reddit_monitor.yml` env list cleanup: 11 mappings for gates
  removed in round 63 (settle windows, duplicate-media/repost/mod-queue
  gates, listing outage racing, approval recheck) are dropped, and the
  round-64 `FRESH_HOLD_SECONDS`/`LISTING_CONFIRM` are wired; round-61
  deploy steps untouched.
* **2026-10-05 — Docs: history folder.** All dated records now live in
  [`docs/history/`](history/) — the changelog archive (rounds 1–62),
  the engine round notes, and every `ROUND_*.md` decision record — with a
  short index. `docs/` keeps only the current topic guides. Stale deployment
  artifacts of already-merged rounds were deleted (`round_46b.patch`,
  `bump_3.14.8.patch` — superseded by the automated
  `python_version_bump.yml` workflow — and the copy-paste PR packages for
  rounds 42–45). Every cross-reference was repointed and link-checked.
* **2026-10-05 — Round 65: body entity hygiene.** Live 1wxvl13: a card built
  from the Arctic Shift backup path showed literal `&gt;` — Arctic (like
  Reddit's API) serves selftext HTML-escaped, and only the JSON path
  unescaped it. Every body path now HTML-unescapes exactly once
  (double-unescape explicitly tested against), and empty-blockquote artifact
  lines (a line that is only `>`) are dropped. Quoted content, and all other
  paths, are byte-identical.
* **2026-10-05 — Round 64: Pristine Listing Protocol.** A post now delivers
  only when a cache-busted, pristine read of the subreddit's /new listing
  proves it is live on the subreddit at that moment (unique `_fresh`
  cache-buster + no-cache request headers on every listing read — no stale
  CDN/cache view can linger). Not there → skipped, never blocked: it posts
  instantly on the tick it first appears. Plus a stateless
  `FRESH_HOLD_SECONDS=30` floor computed from the post's own timestamp — no
  trackers, no pending entries, no inference. `LISTING_CONFIRM=0` restores
  round-63 behavior. Dedup, the round-42/45 fail-closed content-advisory gate
  (REMOVED in round 67 — see
  [`docs/history/ROUND_67.md`](history/ROUND_67.md)), and the retraction
  seatbelt were unchanged at the time.
* **2026-10-05 — Round 63: The Great Simplification.** The Reddit engine is
  reduced to three protections: the dedup cache, the round-42/45 fail-closed
  content-advisory gate (polished: over_18 + thumbnail marker + subreddit
  flag + page markers on every data path; that gate was itself REMOVED in
  round 67 — see
  [`docs/history/ROUND_67.md`](history/ROUND_67.md)), and the opt-in
  retraction seatbelt (edit/delete/off — all three verified by tests).
  Removed: settle window, mod-queue gate,
  dup-media gate, repost gate, page-identity check, listing health guards
  and all their Variables. Posts now deliver as-is at cron speed.
* **2026-10-05 — Docs: README restructure.** The README was rebuilt around
  the current shipped behavior (hero + badges, features, setup, config,
  delivery pipeline, testing, troubleshooting). Every dated round-by-round
  note (~1,450 lines) moved verbatim to
  [`docs/history/ENGINE_HISTORY.md`](history/ENGINE_HISTORY.md); the dated changelog
  for rounds 1–62 remains in
  [`docs/history/CHANGELOG_ARCHIVE.md`](history/CHANGELOG_ARCHIVE.md). No behavior,
  engine, workflow, or test changes.
