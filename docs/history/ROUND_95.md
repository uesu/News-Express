# Round 95 (2026-10-30) — independent pre-delivery liveness probe (archive-based) + Reddit summary pressure reporting

## Provenance

Three live misses on 2026-10-29, reported with screenshots, plus two production run
logs (`Reddit Feed Monitor #11334`, `#11292`) from the live repo:

| Post | State at Reddit | Delivered |
|---|---|---|
| `Zenlesszonezeroleaks_/1xijfzb` ("Robin was hiding all that cake !?") | AutoModerator removed it **6 s** after submission ("likely being a question post"); the mod-removal banner appeared later | 13:11:02Z, **4.6 min** old, `media=video \| proxy: embedez` |
| `Genshin_Impact_Leaks/1xifykm` ("A City Forged of Towering Kristall") | "Locked post" + "removed by the moderators", AutoModerator karma rule (needs 5 karma, 1 day old) | 10:25:57Z, 13 min old |
| `WutheringWavesLeaks_/1xifc1c` ("Version 2.2 Drip - Cantarella") | "Post is awaiting moderator approval" at delivery; removed by a moderator hours later | 09:41:01Z, **5.1 min** old |

The logs settle the two design questions that mattered:

1. **`REDLIB-REACH: 0/26 instance(s) answered this run` in BOTH runs**, and
   `redlib gallery enrichment failed (all instances)` on both delivered posts. Every
   Redlib mirror is dead from the Actions runner. A redlib-page probe would therefore be
   dormant exactly when it is needed, so this round does **not** build one.
2. **The Arctic archive answers normally** (`[arctic <sub>] RSS had no new posts — trying
   N post(s)`), and its records carry the deciding field. `removed_by_category` is the
   archive's own copy of Reddit's removal state, and `automod_filtered` is the queue state
   round 83c already documented.

`FRESH_HOLD_SECONDS` cannot fix this class: the hold in production is 60 s, and these posts
were 4.6 / 5.1 / 13 minutes old when delivered — the removal state does not expire.

## What changed

### 1. `candidate_liveness_verdict()` — one independent verdict before delivery

Runs after the round-20/32/93 gate and before media resolution/card build. Cheapest
evidence first:

| Step | Cost | Verdict |
|---|---|---|
| FULL-MODE post JSON already fetched (`removed_by_category`, title/selftext markers) | **0 requests** | `removed` / `live` |
| archive record of an archive-sourced candidate (`entry._arctic_post`) | **0 requests** | `removed` / `live` |
| archive lookup by id (`/api/posts/ids?ids=<id>`, 8 s cap) | **1 request** | `removed` / `live` / `unverified` |
| nothing available (no record, archive down, budget spent) | — | `unverified` |

`automod_filtered` → `pending approval` (retryable queue reason); any other non-empty
category → `removed by moderators/filters`. Both are the existing
`pending_reddit.json` vocabulary, so nothing downstream changes meaning. A record that
exists and carries no removal evidence is treated as **positive** proof of life — that is
what lets the default stay lenient without guessing.

### 2. Lenient by default; strict is one Variable away

`liveness_hold_decision(state, strict)`:

| state | lenient (default) | strict (`REDDIT_LIVENESS_STRICT=1`) |
|---|---|---|
| `removed` | hold | hold |
| `unverified` | **post** (exactly as today) | hold, retry |
| `live` / `skipped` | post | post |

The consequence is the whole point: in the default mode this change **cannot withhold a
live post**. A hold requires positive evidence; uncertainty behaves exactly as `main` did.

A held post is written to `pending_reddit.json` (never to the dedup cache) and re-checked
after `PENDING_RECHECK_SECONDS` (or immediately when it reappears in RSS), so
"held" means "later", not "lost".

The hold reason is deliberately **not** the archive's own wording: it is
`liveness_removed` / `liveness_unverified`, both **outside** `_NO_RECHECK_REASONS`.
Those never-re-check reasons exist for evidence read from a live page; the archive record is a
snapshot, so a removal it reports may since have been reversed (a moderator approving a queued
post is a routine event in these subreddits). Reusing the never-re-check vocabulary here would
have turned a stale snapshot into a **permanent** hold — the round-34 "held and never posted"
failure shape. With its own reason, a held post is re-probed every 30 min and posts as soon as
the record is clean, and it is never written into the dedup cache.

### 3. Bounded cost

- `LIVENESS_PROBE_BUDGET` (default **10**) archive lookups per run, so a flood run cannot
  add unbounded latency; the rest report `unverified`/`budget`.
- `LIVENESS_PROBE_TIMEOUT` (default **8 s**) per lookup.
- Nothing runs in DRY RUN or TEST POST mode, or when `REDDIT_LIVENESS_PROBE=0`.
- The probe has its **own** failure counter (`_liveness_fail_count`) precisely so that an
  archive hiccup here can never trip the shared `_arctic_fail_count` and disable the
  media/archive paths.
- Runs with no candidates to process: **0 requests, 0 ms**.

### 4. Honesty fix in the existing gate

`verify_archive_post_live()`'s success path always said `live via redlib`, but with
`feed_ok=True` it answers from the combined RSS feed via `fetch_test_post_base()` — the two
production logs show `live via redlib` while `REDLIB-REACH` was `0/26`. It now says
`live via redlib/rss fallback`.

### 5. Reddit run summary (so a held post is explainable without the Actions log)

- New **`### Liveness`** block: probe enabled/disabled, lenient/strict,
  `Verified live`, `Held as removed/queued` (+ by reason), `Unverified (posted)`, and
  `evidence source` (`post-json` / `arctic-entry` / `arctic-lookup`), plus `Probe skipped`.
- **`- Dedup cache: N key(s), M dropped at the cap this run (hot: …)`** — eviction and
  per-sub saturation were log-only warnings (`dedup cache near cap: 1016 key(s)`,
  `evicted 1 oldest key(s)`), invisible in the summary.
- **`- Instances (REDLIB-REACH): …` prefix fixed**: the engine already stores the line with
  its prefix, so the summary printed `Instances (REDLIB-REACH): REDLIB-REACH: 0/26…`.
- **All-mirrors-down warning**: when the run probed ≥1 instance and none answered, the
  summary says so and states that page-based checks were unavailable, instead of leaving a
  `0/26` burying the fact in a long line.

## Files

| File | Change |
|---|---|
| `testing area/reddit_main_v3.py` | ROUND 95 block (probe, mapping, decision helper, counters), call site after the liveness gate, per-run resets, dedup-cache counters, `live via redlib/rss fallback` |
| `.github/workflows/reddit_monitor.yml` | four optional Variables mapped; Liveness + dedup-cache blocks; REDLIB-REACH prefix + warning |
| `tests/test_smoke.py` | 26 new guards (mapping matrix, lenient/strict matrix, request accounting, budget, failure isolation, workflow wiring, rendered summary) |
| `docs/history/ROUND_95.md` | this file |
| `docs/CHANGELOG.md`, `README.md`, `docs/REPOSITORY_TRACKING.md` | operator-facing documentation |

## Verification

| Check | Result |
|---|---|
| `tests/test_smoke.py` | **1215 PASS** (1189 before this round; +26) |
| `tests/test_reddit_signals.py` | **103 PASS** |
| `tests/test_twitter_media.py` | **ALL PASS** |
| `compileall` (`testing area`, `tests`) | clean |
| YAML parse (all workflows + dependabot) | OK, Reddit workflow still **7 steps**, 1 job |
| Embedded summary script | compiles; exercised against a 2026-10-29-shaped record, a round-95 record, and the probe-off record |
| zizmor 1.31.1 | finding set identical to base (`8931a34`), 0 `ref-version-mismatch` |
| Mutation test | **10 / 10 caught** (see table) |

### Mutation table (each rule broken on purpose; the named guard must fail)

| Mutation | Guard that caught it |
|---|---|
| lenient holds `unverified` (withholds a live post) | `r95: lenient holds ONLY on positive evidence…` |
| `automod_filtered` treated as a hard removal | `r95: queued post -> pending approval` |
| probe ignores `REDDIT_LIVENESS_PROBE=0` | `r95: … -> skipped with ZERO requests` |
| free records ignored (request where none was needed) | `r95: a FULL-MODE post JSON record answers the probe with no request` |
| liveness lookup shares `_arctic_fail_count` | `r95: a failed liveness lookup returns None and does NOT touch…` |
| per-run budget removed | `r95: LIVENESS_PROBE_BUDGET caps lookups per run` |
| `REDDIT_LIVENESS_STRICT` not mapped in the workflow | `r95: both probe Variables are mapped…` |
| summary loses the Liveness block | `r95: the summary reports the probe's outcome…` |
| summary re-doubles the REDLIB-REACH prefix | `r95: the REDLIB-REACH line is printed ONCE…` |
| summary drops the all-mirrors-down warning | `r95: a 0/26 Redlib run is called out…` |

Two of these guards were written **vacuous** first (a substring `### Liveness` match, and a
prefix check run against a scenario whose log was empty) and were only found by the
mutation run — both now assert the exact rendered line.

## Limits (deliberate, and what would change them)

- **Coverage depends on the archive having a record.** A post removed seconds after
  submission may have no archive row when the probe looks minutes later; that reports
  `unverified`, which the default **posts**. Only `REDDIT_LIVENESS_STRICT=1` holds it. The
  `evidence source` counters in the summary are how to see the real coverage rate before
  flipping that switch.
- **A removed post whose archive record is still pre-removal** is not caught; the archive
  is a snapshot and its ingestion lag is not observable from here.
- **Post-delivery removals are out of scope** — that is the retraction seatbelt
  (`RETRACT_DEAD_POSTS`, still off in production: `posted_messages.json` has been `{}`
  since 2026-10-27 19:02Z).
- **No Redlib page check is built.** With `0/26` answering, it would add latency for no
  signal. If the fleet recovers, the round-93 classifiers
  (`redlib_moderator_removal_reason`, `removed_post_reason`) are already there and can be
  added as one more evidence source without touching the decision rule.
- **The queue wording** ("temporarily sent to the moderators for review") is only visible
  on a Redlib page, so no regex for it was added; the archive's `automod_filtered`
  category covers the same state where the archive has the record.
- Nothing here was verified against live Reddit/Redlib/Arctic from the sandbox (no egress).
  The mapping, decision rule, request accounting and summary rendering are proven offline;
  the ingestion-lag figures above are the open question.
