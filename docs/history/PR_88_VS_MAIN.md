# PR #88 vs `main` — every change, in plain words, with examples

**What this PR is:** four small rounds that make the monitors **report what they
did** and **stop a specific class of false delivery**, without touching how a
normal post is built or how fast it goes out.

| | |
|---|---|
| Base | `main` @ `8931a34` (PR #87 merge) |
| Head | `00254fe` (round 95c) |
| Engine files touched | 3 (`reddit_main_v3.py`, `twitter_v3.py`, `twitter_v2_button_outside.py`) |
| Workflows touched | 2 (both keep **7 steps**, 1 job each) |
| New files | **3 docs only** — no new code file, no new service, no new dependency |
| Lines **removed** in engine + workflows | **8**, each listed in §7 |

---

## 1. The one-sentence version of each round

| Round | What it fixes | Toggle |
|---|---|---|
| **94** | The Twitter summary said "cache failed" when the cache step never even ran; Reddit's said nothing when the run-result file was missing or corrupt. Also: an optional 350 MiB video cap. | `TWITTER_HIGH_VIDEO_LIMIT` (unset → 256 MiB) |
| **95** | A removed / mod-queued / automod-filtered post could still be delivered, because "a proxy answered" was treated as "the post is live". Now an **independent record** must also agree. | `REDDIT_LIVENESS_PROBE=1`, `REDDIT_LIVENESS_STRICT=0` (lenient) |
| **95b** | Bug inside 95: a probe hold reused a "never re-check" reason, so a post held by the probe would have been held **forever**. Holds now use their own reasons and clear themselves. | none (always on) |
| **95c** | A degraded nitter fleet that answers `feed OK` with an **old backlog** could post days-old tweets as news. Plus: the pending re-check wait drops 30 min → 5 min; the Twitter summary now shows dedup/backlog state. | `TWITTER_MAX_AGE_HOURS` (24), `PENDING_RECHECK_SECONDS` (300) |

---

## 2. Round 94 — the summary stops lying, and an opt-in video cap

**Problem A.** The Twitter workflow only sets `TWITTER_CACHE_RESULT` inside the
*persist cache* step. If the monitor itself fails, that step never runs, the
variable is unset, and the summary rendered `cache: failed` — blaming a cache
failure that never happened.

* Now: `cache: not-reached`. Same wording the Reddit summary already used.

**Problem B.** The workflow pipes the monitor through `tee twitter_monitor.log`,
so the log file exists from the first second of the run. "Zero matching lines"
therefore meant *either* a clean quiet run *or* a crashed monitor — the summary
showed five `0`s for both.

* Now: `diagnostic coverage: unavailable (empty or missing log)`, and the block
  is labelled **"matching log lines, not unique posts"**. Only counts are
  printed; the log (which can contain webhook URLs in error bodies) is never
  echoed.

**Problem C.** A corrupt `reddit_run_result.json` looked exactly like a clean
empty run.

* Now: `**Run-result record:** read | missing | invalid shape | unreadable`.

**Problem D.** The video cap was a hard `256 * 1024 * 1024` literal in two
engines.

* Now one function, `_video_size_limit()`, opt-in via `TWITTER_HIGH_VIDEO_LIMIT`.
  Only `1`/`true`/`yes`/`on` select 350 MiB; unset, empty, `0`, `false`, `off`,
  `350`, `garbage` all keep **256 MiB**. The Variable is unset in production, so
  the live cap does not move.

**Example.** A run where the monitor crashed before printing anything used to
show `posts delivered: 0`, `Discord delivery errors: 0`, …, `cache: failed`.
It now shows `posts delivered: 0`, `diagnostic coverage: unavailable`, `cache:
not-reached` — three different facts, not three zeros.

---

## 3. Round 95 — "a proxy answered" is no longer proof the post is live

**Problem.** The old gate accepted *any* proxy response on the RSS path. A proxy
serves a removed post's pre-removal title, body and media. Live on 2026-10-29:

* `1xijfzb` — auto-removed **6 s** after submission, delivered **4.6 min** later;
* `1xifykm` — removed by an AutoModerator karma rule, delivered anyway;
* `1xifc1c` — still awaiting moderator approval at delivery.

**Fix.** Before delivery, ask an **independent record** in a ladder that costs
nothing when it can:

1. the FULL-MODE post JSON we already fetched → free;
2. the archive record already in hand → free;
3. **one** Arctic ids lookup (≈0.8 s typical, 8 s timeout, budget 10 per run);
4. "no record yet" → post anyway (lenient).

**Example.** A post created 4:18 PM that is genuinely live: the 4:20 PM run
looks it up once (≈0.8 s), sees it live, posts it. A post removed at 4:19 PM:
the same lookup says *removed*, the post is **not** sent to Discord, and it is
parked in `pending_reddit.json` as `liveness_removed`.

**Cost on a normal run:** zero extra requests when nothing is new — the probe
only runs for a candidate that is already about to be delivered.

---

## 4. Round 95b — the bug inside round 95

Round 95 first recorded probe holds with the existing "removed by moderator"
style reason. Those reasons live in `_NO_RECHECK_REASONS`, which means **never
re-checked** — correct for a live page that says "removed", wrong for an archive
*snapshot* that might since have been reversed. A single stale snapshot would
have held a post until it aged out at 48 h.

* Now the hold reasons are `liveness_removed` / `liveness_unverified`, which sit
  **outside** that set, so the post is re-probed and goes out as soon as the
  record is clean.

**Example.** Archive snapshot at 4:00 PM says "removed". At 4:05 PM the post is
approved. With the 95b fix it posts on the next re-check; without it, never.

---

## 5. Round 95c — the stale-backlog guard (this is the new one)

### What actually happened (measured)

Run **#12043**, `2026-10-30T00:55:25Z`:

* `nitter.cf`, `xitter.cf`, `nitter.gq`, `xitter.gq` → **HTTP 502** each;
  `nitter.meowing.monster` → **429** first, then OK;
* all five accounts still reported `feed OK` (17–20 entries each) — so "the
  fleet is down" is *not* the failure shape to design for. A **partly** healthy
  fleet is;
* `TYPEII_EN` posted three tweets at `00:55:39`, `00:55:42`, `00:55:45`:

| tweet id | actually created | age when posted |
|---|---|---|
| `2115271059188613499` | 2026-10-28 02:34 UTC | **46.4 h** |
| `2114559707734245394` | 2026-10-26 03:28 UTC | **93.4 h** |
| `2112102702817972715` | 2026-10-19 08:44 UTC | **256.2 h** (10.7 days) |

### "Were they re-posts?" — no, and that is the point

All three keys were **absent from every earlier version** of
`posted_tweets.json`: across the 100 commits that touch that file in
`uesu/wvkhabh2s22`, they appear only in `74c4fd42` (`+3/−0` — that run). They
were **first-time posts of an old backlog**.

And **#12044** (5 minutes later) posted **nothing**: all five feeds answered from
`nitter.cf`, all 20 `TYPEII_EN` entries were re-read, all three keys were now in
the cache, `TWITTER_CACHE_RESULT=no-changes`. That is exactly your screenshots:
the same three tweets, **one card each**, no duplicate.

So the cache works — *for keys it already holds*. The hole is the key it does
not hold: a fresh deployment, a reset, an evicted key. That key goes out as
"news" days late.

### The fix

One guard in the existing per-entry loop, **before** the tweet-data fetch:

```
age = feed date, else (tweet_id >> 22) + twitter_epoch   # snowflake, always present
if known and age > TWITTER_MAX_AGE_HOURS:  # default 24
    log "STALE-SKIP" and continue          # 0 requests, 0 Discord traffic
```

* **24 h floor.** The cron fires every 5 minutes; a real tweet goes out within
  minutes. A day-old entry is a backlog, never news.
* **Two witnesses.** The feed date *and* the tweet-id snowflake both give an
  age. For the account's **own** tweet the older one wins, so a mirror that
  re-stamps an old entry with "now" is still refused. For a **repost** (link
  points at another author's status) the feed date wins, so reposting an older
  tweet still posts — that is a legitimate new post, not a backlog item.
* **Cannot lose a live post.** Unknown age → posts. `TEST_TWEET_ID` → exempt.
  `TWITTER_MAX_AGE_HOURS=0` → byte-identical pre-95c behaviour.
* **Zero requests.** The guard runs before `fetch_tweet_details_any`, so a
  stale feed now costs *less* than before, not more.

**Example.** Same #12043 conditions, with this change: the feed still reports
`feed OK` and still serves 20 entries; the three old ones are logged
`STALE-SKIP: entry is 46.4 h old (> 24 h floor)` and quietly dropped; a genuine
tweet from 4 minutes ago is 240 s old and posts normally.

End-to-end check with fake network (real `main()`, real dedup, real guard):

| scenario | result |
|---|---|
| feed = 2 min + 12 h + 40 h | **2 posted**, 1 `STALE-SKIP` (the 40 h) |
| same feed, next 5-min run | **0 posted**, `dedup_skipped=2`, `stale_skipped=1` — no re-post |
| guard off (= today's `main`) | 3 posted — the only difference is the 40 h entry |
| tweet at 11:00, run at 11:00:30 | **posted** |
| same tweet, 11:05 run | **0 posted**, `dedup_skipped=1` |
| feed says "2 min", id says 40 h | **refused** (id wins) |
| repost of a 60 h-old tweet | **posted** (feed date wins) |
| feed date 10 min in the future (clock skew) | **posted** (age clamps to 0) |

### Round 95c, part 2 — the re-check wait

`PENDING_RECHECK_SECONDS` **1800 → 300** (one 5-minute cron tick).

* Before: a post held for a transient reason waited up to **30 min** for its
  re-probe while the workflow ran every 5 min → an approved post could sit
  missing for 25 extra minutes.
* Now: the hold is re-probed on the **next** run.
* Scope: removed/deleted posts are still **never** re-checked; the extra work is
  one Arctic lookup (~0.8 s) per due post, inside the same probe budget; a run
  with no held posts does no extra work at all.
* `PENDING_RECHECK_SECONDS=1800` restores the old wait.

### Round 95c, part 3 — the summary a later agent can read

The engine now prints one line:

```
V3 SUMMARY: posted=0 dedup_skipped=3 stale_skipped=0 cache_missing=0 cache_keys=294 max_age_hours=24
```

and the step summary renders it under **Dedup / backlog state**, plus
`entries refused as stale backlog: N`, plus `engine: unavailable` when the line
is missing (so absence never reads as "zero re-posts"), plus a re-post warning
when `cache: failed` — because an unpersisted cache is the only remaining way
this monitor can duplicate a post.

**Why it matters, concretely:** #12044 looked fine but *proved nothing* to a
reader — it had no `V3 Posted:` line and no "skipped" line. A future agent
could not tell "3 duplicates correctly blocked" from "the feed was empty".
With the new line it reads `dedup_skipped=3`.

---

## 6. Speed and structure — what did **not** change

### Measured, production

| | #12043 (3 posts) | #12044 (0 posts) |
|---|---|---|
| feeds answered | 5/5 in ~1.2 s (4 mirrors dead) | 5/5 in **0.16 s** (one healthy mirror) |
| posts | 3 (+1.5 s spacing each: card build + webhook round-trip) | 0 |
| engine finished | 00:55:46.6 | 01:00:54.1 |

A quiet run is **unchanged** — same requests, same order. A posting run adds the
same one lookup round 95 already adds, and **nothing** for round 95c.

### Measured, per entry

| Operation | Cost |
|---|---|
| 95c stale check (shift + compare, no network) | **0.61 µs** per feed entry → **12 µs** for a 20-entry feed |
| 95: liveness probe, record already in hand | 0 requests |
| 95: liveness probe, needs a lookup | ≈0.8 s, once per *delivered* post, budget 10/run |

### Structural footprint

* Both workflows: **7 steps → 7 steps**. No new step, no new job, no new action.
* No new dependency, no new service, no new file in `testing area/`.
* Card payloads: the card-building code is untouched — 12/12 payloads compared
  byte-identical (20 683 bytes) during this branch's verification.
* `FRESH_HOLD_SECONDS=60` unchanged. `MAX_POSTS_PER_RUN=25` unchanged.
  Cache caps (250/account, 10 000 total) unchanged; production holds 294 keys.
* `TWITTER_HIGH_VIDEO_LIMIT` stays **unset** → the live cap stays 256 MiB.
* `sync_prod.yml` still never copies a cache file.

---

## 7. Every removed line, in full

| File | Removed | Replaced by |
|---|---|---|
| `twitter_monitor.yml` | `- cache: ${TWITTER_CACHE_RESULT:-failed}` | `:-not-reached` (round 94) |
| `reddit_monitor.yml` | the doubled `Instances (REDLIB-REACH): REDLIB-REACH: …` print | printed once (round 95) |
| `reddit_main_v3.py` | `PENDING_RECHECK_SECONDS = … 1800  # 30 min` | `… 300  # 5 min` (95c) |
| `reddit_main_v3.py` | `return True, "live via redlib"` | source-labelled verdict (round 95) |
| `twitter_v3.py` | `VIDEO_SIZE_LIMIT = 256 * 1024 * 1024` | `_video_size_limit()` (round 94) |
| `twitter_v2_button_outside.py` | same literal | same function (round 94) |
| `reddit_main_v3.py` | 2 comment lines saying "default 30 min" | updated comments |

That is the entire deletion set: **8 lines**, six of them one-liners with a
named replacement.

---

## 8. Variables — nothing needs turning on

Every switch in this PR is **on by default with a safe value**; after you merge,
the runs behave as described above with **no repository Variable set at all**.
The table below is only for changing or undoing a behaviour (`Settings →
Secrets and variables → Actions → Variables`, then the next run picks it up).

## 8b. Rollback, per piece — no revert needed

| Want the old behaviour? | Set |
|---|---|
| old stale-backlog behaviour | `TWITTER_MAX_AGE_HOURS=0` |
| old 30-minute re-check wait | `PENDING_RECHECK_SECONDS=1800` |
| no liveness probe at all | `REDDIT_LIVENESS_PROBE=0` |
| no video cap change | leave `TWITTER_HIGH_VIDEO_LIMIT` unset |

Each is a repository Variable; no code revert, no redeploy.

---

## 9. Verification totals

| Suite | Result |
|---|---|
| `tests/test_smoke.py` | **1236 PASS** (main: 1175; head before 95c: 1218) — **0 guards lost** |
| `tests/test_reddit_signals.py` | 103 PASS |
| `tests/test_twitter_media.py` | ALL PASS |
| `compileall`, YAML parse, zizmor | clean / OK / identical to base |
| Mutation tests | 10/10 (r95) + 8/8 (r95c) |
| CI on PR #88 | `smoke` **SUCCESS**, `MERGEABLE/CLEAN` |
