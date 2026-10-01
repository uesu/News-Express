# Delivery latency model (after rounds 46b / 47 / 48 / 48b)

Measured from the three live incidents of 2026-10-01, then generalised. All
times are Manila (+08), as in your screenshots.

## 1. The 1wuwjiw timeline (r/HonkaiStarRail_leaks)

| Time | Event | Source |
|---|---|---|
| 19:06:00 | post created | post tooltip |
| 19:06:01 | AutoModerator stickied "respond with a mirror link and source link" | comment tooltip |
| ~19:10 | OP replies with Source + mirror ("23m ago" at 19:33) | comment list |
| **19:16** | **delivered to Discord** (too early — round-46 code) | your card |
| 19:17 | page still shows "Post is awaiting moderator approval" | screenshot |
| ≤ 19:28:39 | post is public — an unrelated user comments | comment tooltip |
| 19:33 | post fully visible with all media | screenshot |

So for this post: **AutoMod demand at +1 s, OP compliance at ≈ +4 min,
moderator/AutoMod approval somewhere in +11 … +22 min**, call it **≈ 20 min**.

## 2. What each code generation would do with it

| Code | Behaviour on 1wuwjiw | Delivered |
|---|---|---|
| pre-round-42 | 300 s settle, no queue evidence | ~19:11–19:16 (queued ❌) |
| round 46/46b (what ran) | listing asked first → "released" | 19:16 (queued ❌) |
| **round 48 (now)** | banner read first → HOLD, re-check every 5 min | **first tick after approval ⇒ ~19:20–19:30 ✅** |

Round 48 cannot make the post appear before the moderators approve it. What
it guarantees is that it appears **within one cron tick of approval** and
never before.

## 3. The general model

```
delivery = creation
         + T_approval        (0 for a normal post; moderator-dependent otherwise)
         + T_detect          (≤ 1 cron tick = ≤ 5 min, average 2.5 min)
         + T_settle          (60 s fast path, or 300 s when unconfirmed)
         + T_build           (~2–6 s: listing + page + media + webhook)
```

### Case A — ordinary post, no AutoMod gate (the majority)

* `T_approval` = 0
* `T_detect` = 0–5 min (avg 2.5)
* `T_settle` = **60 s** whenever an API-backed redlib `/new` listing confirms
  the post (round 42 + 46b), else 300 s
* **Typical: ≈ 3.5 min. Best: ~1 min. Worst: ~10 min** (listing unreadable
  ⇒ 300 s settle ⇒ the check lands on the next tick)

Round 48 changes **nothing** here: there is no banner on the page, so the
listing still releases the post immediately.

### Case B — subreddit with the AutoMod source/mirror rule (HSR, Ananta, GI, ZZZ leaks)

* `T_approval` = time until a human/AutoMod approves. Observed on 2026-10-01:
  **1wuqy6z ≈ ?, 1wurg8f ≈ ?, 1wuwjiw ≈ 20 min.** Published evidence from
  your own screenshots gives a working range of **10–25 min** when the OP
  replies promptly, and unbounded when they do not.
* `T_detect` after approval = ≤ 5 min (the pending entry is re-checked every
  `APPROVAL_RECHECK_SECONDS` = 300 s, which matches your cron tick)
* `T_settle` = already satisfied (the post is older than the window by then)
* **Typical: approval + 0–5 min ⇒ ≈ 12–30 min after creation**
* A post that is never approved is simply never posted (pending expires at
  `PENDING_MAX_AGE_SECONDS`, 48 h).

### Case C — queued post that gets removed instead of approved

Never posted at all. This is the case rounds 46–48 exist for; the cost is the
extra wait in case B, which only applies to posts that were in the queue.

## 4. Estimated effect on your channels

| Post type | Share (leak subs, rough) | Latency before | Latency now |
|---|---|---|---|
| Normal, listed, no queue | ~70–80 % | ~3.5 min | **~3.5 min (unchanged)** |
| Queued, later approved | ~15–25 % | 5–10 min, but **often posted while queued** | approval + ≤ 5 min (~12–30 min) |
| Queued, later removed | a few % | posted, then dead | **never posted** |

Net: the fast path is untouched, and the slow path is slow **only because
Reddit's moderators are slow** — which is exactly the trade you asked for
("never post awaiting-approval content").

## 5. Peak performance is preserved

Nothing added per post in round 48 — it only reorders two `if`s inside
`queue_verdict()` (pure function, no I/O). The per-run cost profile is
unchanged from round 46b:

| Stage | Requests | Wall time |
|---|---|---|
| `/new` listing | all mirrors + RSS **in one concurrent batch**, cached per subreddit per run | < 0.5 s healthy, hard cap 8 s |
| mod-queue page | mirrors in parallel, only for posts inside `MOD_QUEUE_WINDOW_SECONDS` | ~1 s |
| media resolution | unchanged | 1–4 s |
| Discord | 1 POST | ~0.3 s |

## 6. New in round 48b — measure it instead of guessing

Every delivery now logs:

```
Reddit V3 Posted: HonkaiStarRail_leaks_1wuwjiw (media=image | native | 1 item(s))
  | LATENCY 24.3min after creation | held 18.1min as 'pending approval'
```

Grep the Actions log for `LATENCY` and you get, per subreddit, the real
distribution of (a) end-to-end delivery time and (b) how long the queue held
each post. After a week of data you can decide, with numbers:

* whether `MOD_QUEUE_WINDOW_SECONDS` (6 h) is wider than it needs to be;
* whether `POST_SETTLE_SECONDS` (300 s) can be lowered for subs that never
  queue;
* which subreddits justify the AutoMod weak-hold grace at all.

## 7. The only remaining levers

1. **Cron interval.** Everything above is quantised by it. 5 min → average
   +2.5 min on every post. A 2-minute interval would cut the average
   detection delay to ~1 min (set `APPROVAL_RECHECK_SECONDS=120` to match).
2. **Reddit itself.** Approval latency is 100 % outside the repo. Nothing in
   any round can shorten it — only avoid publishing before it happens.
