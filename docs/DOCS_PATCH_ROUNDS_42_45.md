# Docs patch for PR #20 (rounds 42–45)

PR #20 ships the code but no operator documentation. Two copy-paste blocks
below close that: one for `.env.example`, one for `README.md`.

Both describe the behaviour **as implemented in PR #20** (verified against
`68d5049`: defaults 300/60, NSFW fail-closed, page fallback on, repost gate
on, retraction off + edit mode).

---

## 1. `.env.example`

### 1a. FIX A STALE LINE FIRST (important)

`.env.example` currently claims the NSFW gate fails **open**. That is no
longer true — it fails **closed**. Find this block:

```
# Round 35: every NEW post is checked against Reddit's own NSFW markers
# (over_18 + the "nsfw" thumbnail sentinel) in one batched Arctic Shift
# lookup. Flagged posts are held for the 48 h pending window and are not
# posted. Lookup failures fail open; TEST_POST_ID rebuilds bypass the gate.
```

and replace that fourth line so the block reads:

```
# Round 35: every NEW post is checked against Reddit's own NSFW markers
# (over_18 + the "nsfw" thumbnail sentinel) in one batched Arctic Shift
# lookup. Flagged posts are held for the 48 h pending window and are not
# posted. TEST_POST_ID rebuilds bypass the gate. Round 42 CHANGED the
# failure mode: an unreadable lookup now fails CLOSED (see below).
```

### 1b. ADD THIS BLOCK

Paste immediately after the existing `# MOD_QUEUE_WINDOW_SECONDS=21600` line:

```
# ---------------------------------------------------------------------------
# Rounds 42-45 (2026-10-01): faster delivery + a stricter safety gate.
# Every value below is OPTIONAL. Unset = the default shown, which is the
# shipped behaviour; you do not need to set any of these.
# ---------------------------------------------------------------------------

# Round 42 — EVIDENCE-BASED SETTLE (the latency fix).
# A post confirmed present in the subreddit's public /new listing is, by
# definition, neither in Reddit's spam filter nor in the mod queue, so it
# only waits out a short AutoModerator buffer instead of the full window.
# A post that is NOT confirmed (or when the listing cannot be read) keeps
# the unchanged 300 s wait, so the fast path can never apply to a filtered,
# queued or removed post.
#   confirmed in /new  -> POST_SETTLE_VERIFIED_SECONDS (60 s)
#   not confirmed      -> POST_SETTLE_SECONDS          (300 s, unchanged)
# Set POST_SETTLE_VERIFIED_SECONDS=300 to reproduce the old timing exactly.
# POST_SETTLE_VERIFIED_SECONDS=60

# Round 42 — NSFW GATE NOW FAILS CLOSED.
# The gate runs BEFORE any Discord message, embed, thumbnail or media work,
# and checks the post (over_18), the community (over18) and, for crossposts,
# the source post and source community. Missing/malformed/unfetchable
# metadata is held as nsfw_unknown and re-checked — never read as safe.
#   NSFW_FAIL_OPEN=1        restores the pre-round-42 fail-open behaviour.
#   NSFW_REQUIRE_SUBREDDIT=1 also demands a READABLE community record before
#                           posting (default off: SUBREDDITS plus the
#                           per-sub webhook map is already an allowlist).
# NSFW_FAIL_OPEN=0
# NSFW_REQUIRE_SUBREDDIT=0

# Round 45 — LIVE-PAGE NSFW FALLBACK (protects the speed win).
# Failing closed on one source has a cost: the Arctic archive lags behind
# brand-new posts, so a 2-minute-old post could be held a whole extra cron
# tick. When the archive has no record, the marker is instead read off the
# live Redlib post page (<small class="nsfw">NSFW</small>) that the run
# already fetches for the liveness check — no extra request. A spoiler badge
# is NOT NSFW. An unreadable page still fails closed.
#   0 = strict archive-only (the post is held instead).
# NSFW_PAGE_FALLBACK=1

# Round 43 — AUTHOR RE-UPLOAD GATE.
# The round-36 duplicate gate compares exact media URLs, and a re-upload
# always gets a BRAND NEW v.redd.it/i.redd.it id, so it cannot see the
# "author deletes and re-posts the same thing" pattern. This gate compares
# the (subreddit + author + normalised title) identity instead and skips a
# post already on Discord. An unknown author ([deleted]) or an empty title
# produces no identity and the gate fails open. Costs no extra request.
#   0 = off. REPOST_WINDOW_SECONDS = how far back the comparison reaches.
# REPOST_GATE=1
# REPOST_WINDOW_SECONDS=86400

# Rounds 43/44 — DEAD-POST RETRACTION. SHIPPED DISABLED.
# When a post that was already delivered later dies (author deleted it, mods
# removed it), its Discord card can be rewritten in place as a tombstone.
# It EDITS, never deletes: per Discord's Announcement Channel FAQ an edit
# updates the message in every FOLLOWING server, while a delete leaves a
# permanent "[Original Message Deleted]" note there — which matters because
# this channel is autopublished. Two independent proofs are required
# (absent from a /new listing that should still show it, AND a removal
# verdict from a live source), and the post id stays in the dedup cache, so
# a retraction can never cause a re-post.
# It is OFF by default because it costs extra requests; when enabled it runs
# AFTER the posting loop, so it still cannot delay a new post, and only then
# is wait=true added to the webhook call.
#   RETRACT_DEAD_POSTS=1 enables it. RETRACT_MODE: edit (default) | delete | off.
# RETRACT_DEAD_POSTS=0
# RETRACT_MODE=edit
# RETRACT_WINDOW_SECONDS=21600

# If you lower the cron-job.org interval below 5 minutes, match the short
# re-check interval to it so held posts are re-evaluated every tick:
#   3-minute cron -> APPROVAL_RECHECK_SECONDS=180
#   2-minute cron -> APPROVAL_RECHECK_SECONDS=120
# APPROVAL_RECHECK_SECONDS=300
```

---

## 2. `README.md`

Paste this as a new section. The cleanest spot is **immediately before**
the line:

```
## 🗒 Changelog
```

```markdown
## 🆕 Reddit V3 — rounds 42–45 (2026-10-01): delivery in one cron tick

Reddit posts used to reach Discord 5–10 minutes after they appeared. They
now arrive on the **first cron tick after the post is confirmed alive**,
with no loss of safety.

### The latency fix (round 42)

Every post used to wait a flat `POST_SETTLE_SECONDS` (300 s) so a mod or
AutoModerator had time to act. That wait was applied even to posts already
proven live. It is now evidence-based:

| Evidence this run | Wait before posting |
|---|---|
| Post present in `r/<sub>/new` | `POST_SETTLE_VERIFIED_SECONDS` = **60 s** |
| Listing unreadable, or post absent | `POST_SETTLE_SECONDS` = **300 s** (unchanged) |

A post visible in the public `/new` listing is by definition not filtered
and not in the mod queue — the two things the 300 s wait protected against.
60 s remains as an AutoModerator buffer. A confirmed post also skips the
mod-queue page fetches entirely.

**Result with a 5-minute cron:** average latency **7.5 min → ≈3.5 min**.
A post at 4:51 PM now lands at ~4:55 instead of ~5:00–5:03. The fast path
can never apply to a filtered, queued or removed post, because those are
absent from `/new` by definition.

### Fewer requests per run

* the Redlib post page was fetched up to **3×** per post → now **1×**
* the proxy chain ran **2×** per post → now **1×**
* a post confirmed in `/new` skips up to **9** mod-queue instance requests
* NSFW markers, duplicate identity and re-upload identity now ride on **one**
  batched Arctic Shift call

### NSFW gate — earlier, wider, fail-closed

The gate runs **before** any Discord message, embed, thumbnail or media
resolution — not just before sending. It rejects:

* posts marked `over_18`
* posts from communities marked `over18`
* crossposts whose **source post or source community** is NSFW

Missing, malformed or unfetchable metadata now **fails closed**: the post is
held as `nsfw_unknown` and re-checked, never posted on a guess. A blocked
post produces **no** Discord output of any kind — the log records only the
post id and the reason. `NSFW_FAIL_OPEN=1` restores the old behaviour.

**Round 45** keeps that strictness from costing speed: when the Arctic
archive has no record of a brand-new post, the marker is read off the live
Redlib post page instead of holding the post for another tick. The page is
one the run already fetches, so it costs no extra request; a **spoiler**
badge is never read as NSFW; an unreadable page still fails closed.

| Archive | Live page | Result |
|---|---|---|
| has record | not consulted | unchanged |
| no record | NSFW badge present | **blocked** |
| no record | renders, no badge | **delivered this tick** |
| no record | unreadable | held `nsfw_unknown` (fail closed) |

### Author re-upload gate (round 43)

Real case in `r/Genshin_Impact_Leaks`: post `1wukgrn` was deleted by its
author ~9 minutes in and re-uploaded as `1wukoah` — same title, same author,
new video file. The round-36 duplicate gate compares exact media URLs, and a
re-upload always gets a brand-new `v.redd.it` id, so it could not see this.

The gate now also compares a `sub|author|title` identity (case, punctuation,
whitespace and zero-width normalised, then matched **exactly** — no fuzzy
scoring) and skips a post already on Discord. An unknown author
(`[deleted]`) or an empty title yields no identity and the gate fails open.
It reuses the existing batched archive call, so it costs no extra request.

### Dead-post retraction — shipped disabled (rounds 43/44)

A delivered card whose Reddit post later dies can be rewritten in place as a
tombstone. It **edits, never deletes**: per Discord's
[Announcement Channel FAQ](https://support.discord.com/hc/en-us/articles/360032008192-Announcement-Channel-FAQ),
an edit updates the message in every following server while a delete leaves
a permanent `[Original Message Deleted]` note there — which matters because
this channel is autopublished. Two independent proofs are required, and the
post id stays in the dedup cache so a retraction can never cause a re-post.

It is **off by default** (`RETRACT_DEAD_POSTS=0`) because it costs extra
requests. When enabled it runs *after* the posting loop, so it adds no
latency, and only then is `wait=true` appended to the webhook call.

### New repository Variables (all optional)

| Variable | Default | Meaning |
|---|---|---|
| `POST_SETTLE_VERIFIED_SECONDS` | `60` | wait for a post confirmed in `/new` |
| `POST_SETTLE_SECONDS` | `300` | wait for an unverified post (unchanged) |
| `NSFW_FAIL_OPEN` | off | `1` restores pre-round-42 fail-open NSFW |
| `NSFW_REQUIRE_SUBREDDIT` | off | `1` also demands a readable community record |
| `NSFW_PAGE_FALLBACK` | on | `0` disables the live-page NSFW fallback |
| `REPOST_GATE` | on | `0` disables the author re-upload gate |
| `REPOST_WINDOW_SECONDS` | `86400` | how far back the re-upload comparison reaches |
| `RETRACT_DEAD_POSTS` | **off** | `1` enables tombstoning cards whose post died |
| `RETRACT_MODE` | `edit` | `edit` / `delete` / `off` |
| `RETRACT_WINDOW_SECONDS` | `21600` | how long a delivered card is watched |

Nothing needs to be set to get the speed improvement.

### Cron interval

The settle window is no longer the bottleneck — the cron is. With the
5-minute interval, latency is 1–6 min. Lowering it now pays off:

| Interval | Average latency |
|---|---|
| 5 min | ≈3.5 min |
| 3 min | ≈2.5 min |
| 2 min | ≈2.0 min |

Below ~2 minutes returns diminish (the 60 s AutoMod buffer becomes the
floor) while cache-commit churn and mirror rate-limiting both rise. If you
do lower it, set `APPROVAL_RECHECK_SECONDS` to match so held posts are
re-evaluated on every tick.
```
