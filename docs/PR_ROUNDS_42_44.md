# PR package — Reddit V3 rounds 42–45

Copy the title and body below into the GitHub "New pull request" form.
Branch: `arena/01a0f4c3-news-express` → `main`.

---

## PR title

```
Reddit V3 rounds 42-45: cut posting latency to the cron tick, evidence-based settle, fail-closed NSFW gate, author re-upload gate
```

---

## PR body (copy everything inside the box)

```markdown
## What this changes

Reddit posts used to reach Discord 5-10 minutes after they appeared. They now
arrive on the **first cron tick after the post is confirmed alive**, with no
loss of safety: removed, deleted, filtered, queued and NSFW posts are still
never delivered.

Twitter is untouched.

### 1. New decision core: `testing area/reddit_signals.py`

All "is this post safe to post?" logic moved out of the 4,000-line engine into
one pure, importable, side-effect-free module: removal classification, NSFW
verdicts, settle timing, duplicate identity and retraction decisions. Pure
functions mean this logic is now directly unit-testable without network, which
is what made the rest of this PR verifiable.

### 2. Evidence-based settle (the latency fix)

Previously every post waited a flat `POST_SETTLE_SECONDS` (300 s) before being
posted, to avoid mirroring something a mod was about to remove. That wait was
applied even to posts already proven live.

Now the wait depends on evidence gathered in the same run:

| Evidence this run | Wait before posting |
|---|---|
| Post is present in `r/<sub>/new` | `POST_SETTLE_VERIFIED_SECONDS` = **60 s** |
| Listing unreadable, or post absent from it | `POST_SETTLE_SECONDS` = **300 s** (unchanged) |

A post visible in the public `/new` listing is by definition not filtered and
not sitting in the mod queue - the two things the 300 s wait was protecting
against. 60 s remains as a deliberate AutoModerator buffer. Confirmed posts
also skip up to 9 mod-queue instance requests.

Net effect: **5-10 min -> 0-5 min**, bounded only by the 5-minute cron tick.

### 3. Per-run request memo

The redlib post page was being fetched up to 3x per post and the proxy chain
2x. Both are now memoised per run (and cleared at the start of every run, with
failures left retryable). Fewer requests = less wall-clock inside the tick.

### 4. NSFW gate, widened and fail-closed

The NSFW check now runs **before** any Discord message, embed, thumbnail or
attachment is built - not just before sending. It rejects `over_18` posts,
posts from `over18` subreddits, and crossposts whose **source** post or source
subreddit is NSFW. Missing, malformed or unfetchable metadata now **fails
closed** (previously treated as safe): the post is held as `nsfw_unknown` and
re-checked, never posted on a guess. Blocked posts produce no Discord output
at all - the log records only the post id and the reason.

`NSFW_FAIL_OPEN=1` restores the old behaviour if ever needed.

### 5. Author re-upload gate (round 43)

Real case from `r/Genshin_Impact_Leaks`: post `1wukgrn` was deleted by its
author ~9 minutes in, then re-uploaded as `1wukoah` - same title, same author,
new video file. The existing duplicate gate compares exact media URLs, and a
re-upload always gets a brand-new `v.redd.it` id, so it could not see this.

`content_fingerprint()` builds a `sub|author|title` identity (case,
punctuation, whitespace and zero-width normalised, then matched **exactly** -
no fuzzy scoring). A new post matching a card already on Discord is held as
`duplicate_repost`. An unknown author (`[deleted]`) or empty title yields no
fingerprint and the gate fails open.

Cost: **zero extra requests** - it reuses the duplicate gate's existing
batched Arctic Shift call, which now also returns title and author.

### 6. Bug caught from a live post

`"i am a bot, and this action was performed automatically"` was being treated
as an AutoModerator *removal*. It is AutoMod's **signature**:
r/Genshin_Impact_Leaks posts it on every healthy post ("Please reply to this
comment with the source"). Left in, it would eventually have frozen good leak
posts. It is now a diagnostic footer only; a removal requires an actual
removal phrase.

### 7. Live-page NSFW fallback (round 45) - protects the speed win

Making the NSFW gate fail closed created one risk: its only metadata source
was the Arctic Shift archive, and the archive lags behind brand-new posts.
A post Arctic has not indexed yet would be held as `nsfw_unknown` and slip to
the next cron tick - giving back the five minutes the settle change saved.

A second, live source removes that. Redlib renders the marker into the post
page; from redlib's own template (`templates/utils.html`, upstream
`redlib-org/redlib`):

    {% if post.flags.nsfw %} <small class="nsfw">NSFW</small>{% endif %}
    {% if post.flags.spoiler %} <small class="spoiler">Spoiler</small>{% endif %}

`nsfw_from_post_page()` reads exactly that badge and returns True / False /
None. **Spoiler is a separate badge and is never read as NSFW** - which
matters, because every leak post is a spoiler.

It runs **only** when the archive returned no record, never in fail-open
mode, and it reuses the memoised post-page fetch the liveness check performs
later in the same iteration - so for a post that goes on to be delivered it
costs **no extra request**.

| Archive | Live page | Result |
|---|---|---|
| has record | not consulted | unchanged |
| no record | NSFW badge present | **blocked** |
| no record | renders, no badge | **delivered this tick** |
| no record | unreadable | held `nsfw_unknown` (fail closed) |

Kill switch: `NSFW_PAGE_FALLBACK=0`.

### 8. Dead-post retraction - built, tested, OFF by default

When a delivered post later dies, its Discord card can be rewritten in place
as a tombstone (original title, stats, media and buttons kept; notice
prepended; accent greyed). It **edits**, never deletes: per Discord's
[Announcement Channel FAQ](https://support.discord.com/hc/en-us/articles/360032008192-Announcement-Channel-FAQ),
an edit updates the message in every following server, while a delete leaves a
permanent `[Original Message Deleted]` stub in all of them - which matters
because this channel is autopublished.

It requires **two independent proofs** (absent from a `/new` listing that
should still show it, AND a removal verdict from a live source), so outages
and queued posts never trigger it, and the post id stays in the dedup cache so
it can never cause a re-post.

**It ships disabled (`RETRACT_DEAD_POSTS` defaults to off)** because it costs
extra requests and this PR is about speed. When enabled it runs *after* the
posting loop, so it still adds zero latency, and `wait=true` is only appended
to the webhook call when it is on.

## New repository Variables (all optional - defaults are the shipped behaviour)

| Variable | Default | Meaning |
|---|---|---|
| `POST_SETTLE_VERIFIED_SECONDS` | `60` | wait for a post confirmed live in `/new` |
| `POST_SETTLE_SECONDS` | `300` | wait for an unverified post (unchanged) |
| `NSFW_FAIL_OPEN` | off | `1` restores pre-round-42 fail-open NSFW behaviour |
| `NSFW_REQUIRE_SUBREDDIT` | off | `1` also demands a readable community record |
| `NSFW_PAGE_FALLBACK` | **on** | `0` disables the live-page NSFW fallback |
| `REPOST_GATE` | **on** | `0` disables the author re-upload gate |
| `REPOST_WINDOW_SECONDS` | `86400` | how far back re-upload comparison reaches |
| `RETRACT_DEAD_POSTS` | **off** | `1` enables tombstoning cards whose post died |
| `RETRACT_MODE` | `edit` | `edit` / `delete` / `off` |
| `RETRACT_WINDOW_SECONDS` | `21600` | how long a delivered card is watched |

Nothing needs to be set to get the speed improvement.

## Tests

Run locally on this branch:

- `python tests/test_smoke.py` -> **572 pass / 0 fail**
- `python tests/test_reddit_signals.py` -> **168 pass / 0 fail**
- `python -m compileall -q "testing area" tests` -> clean

`tests/test_reddit_signals.py` is new and includes end-to-end cases that drive
the real `main()` with a fake session and assert the Discord sender is never
called: NSFW post, NSFW subreddit, NSFW crosspost source, missing metadata,
invalid metadata, API failure, subreddit outside the allowlist, plus the full
`1wukgrn -> 1wukoah` re-upload story, the live-page NSFW fallback (delivered /
blocked / spoiler-not-NSFW / unreadable-page-still-fails-closed / kill switch)
and every retraction failure mode. CI now runs both suites.

## Risk / rollback

Every behaviour change sits behind a Variable listed above; setting
`POST_SETTLE_VERIFIED_SECONDS` equal to `POST_SETTLE_SECONDS` reproduces the
old timing exactly. New cache file: `posted_messages.json` (only written when
retraction is enabled; the workflow commits it alongside the existing caches).
```

---

## Suggested test plan after merge

1. Merge with **no** Variables set - confirm posts land within one cron tick
   and that the log shows `SETTLE: ... confirmed in /new` lines.
2. Watch for `REPOST SCAN: ... (PASS)` on normal posts and
   `REPOST GATE: ... SKIPPED` only on a genuine re-upload.
3. If you see `NSFW SCAN: ... not in the archive yet - live page says
   over_18=False`, that is round 45 saving a tick, working as intended.
4. Only once that looks right, optionally set `RETRACT_DEAD_POSTS=1`.
