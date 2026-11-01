# Reddit survival investigation — keeping the Reddit → Discord feed alive past 2026-11-13

Date: 2026-11-01 (Asia/Manila). Status: **investigation only — no engine changes, nothing committed.**
Companion to Round 99 (`docs/history/ROUND_99.md`, PR #97), which found `REDLIB-REACH 0/26` to be an
upstream Reddit outage. This document answers the follow-up: *what else is out there to keep the feature alive.*

---

## 0. TL;DR

1. **Reddit is retiring RSS on 2026-11-13 — 12 days from now.** Announced 2026-09-30 in r/modnews
   ("Continuing our infrastructure updates", post `1wubgvt`): *"Because RSS is now a common surface for
   large-scale scraping and automated abuse, we'll stop supporting RSS feeds on November 13, 2026."*
   Outside communities you moderate, Reddit says *"there is no replacement."* No exemption is mentioned for
   private token feeds (`?feed=…&user=…`), per-post `.rss`, or multireddit feeds — assume all of them stop.
2. That kills the engine's **primary discovery path** (`https://www.reddit.com/r/<a+b+c>/new.rss?limit=100`
   + `REDDIT_FEED_TOKEN`, `fetch_combined_feed` L4327) and the `old.reddit.com` alternate. The per-sub fallback
   chain (`fetch_working_reddit_feed`, 28 hosts, serial, 15 s timeouts) and Arctic Shift search are what is left.
3. **The public Data API (OAuth, PRAW) is also ending**: new access requests closed **today (2026-10-31)**;
   unregistered apps lose access from **2027-01-12**; everything remaining closes **March 2027**
   (r/redditdev `1wubcvf`). Self-service API keys already ended 2025-11-11 (Responsible Builder Policy).
   → A new `REDDIT_CLIENT_ID/SECRET` is realistically **not obtainable**. The proxies the engine leans on
   (vxReddit, Embeddit) run on exactly those credentials and will die with them.
4. **Two realistic lifelines exist**, and they are complementary:
   - **Bridge (days, low effort):** redlib forks that no longer depend on Reddit's RSS/JSON — chiefly
     **Nachtalb/redlib (`r.naa.gg`, already fleet slot [25])**, which serves its *own* `/r/a+b+c/new.rss` from
     Reddit's still-open anonymous GraphQL and/or logged-in sessions. Needs a small engine change to use the
     combined feed on redlib hosts in parallel and to stop wasting ~7 min/run on dead reddit.com hosts.
   - **Long-term (weeks, medium effort, the only officially hosted path):** a **Devvit app** (Reddit Developer
     Platform) on a personal subreddit, cron every 1–2 min, `reddit.getNewPosts({subredditName})` for the six
     tracked subs (works for subs it is *not* installed in), POSTing full post JSON to a private Discord intake
     channel (`discord.com` is on Devvit's **global fetch allowlist**). The engine then reads that channel
     instead of RSS. Payload is FULL-MODE grade (body, bodyHtml, gallery, secureMedia, flair, score, spoiler…).
5. **Recommended sequence:** ship the bridge before 11-13 (one round), start the Devvit app in parallel,
   keep Arctic Shift as the archive backup, and plan for the proxies to disappear by March 2027.
   Five decisions are needed from you (§6).

---

## 1. Official timeline (primary sources: r/modnews `1wubgvt`, r/redditdev `1wubcvf`, both 2026-09-30)

| Date | What Reddit does | Hits News-Express how |
|---|---|---|
| 2025-11-11 (past) | Self-service API keys ended (Responsible Builder Policy) | No new OAuth app since then without approval |
| ~2026-05-30 (past) | Unauthenticated `.json` → 403 | FULL MODE 403 ("native mode") in every run |
| 2026-07 (past) | old.reddit login-only | `old.reddit.com` fallback slot [1] dead |
| 2026-10-20 (past) | Anonymous Android-OAuth thread JSON 403 → Redlib post pages dead | `REDLIB-REACH 0/26` (Round 99) |
| 2026-10-29 (past) | CEO Q3 letter: logged-in-only Reddit tests in select non-US markets in Q4 | Anonymous listings/HTML increasingly unreliable |
| **2026-10-31 (today)** | Last day new public Data API requests are accepted | Cannot obtain `REDDIT_CLIENT_ID/SECRET` any more |
| 2026-11-10 | Migration progress update (r/redditdev) | Watch for RSS clarifications |
| **2026-11-13** | **RSS feeds stop** (subreddit, user, comment feeds; "no replacement" outside your own communities; mods pointed to the Devvit "Discord Relay" app) | **Primary discovery path dies**; `old.reddit`/eddrit/redlib hosts that merely mirror Reddit RSS die too |
| 2026-11-30 | Devvit app-registration + $1,000 migration-bounty deadline for existing API apps | Only relevant if you already own an approved app |
| 2027-01-12 | API access removed for apps/users not registered or engaged with the Developer Platform team | vxReddit/Embeddit/EmbedEZ lose creds unless registered |
| 2027-02-23 | Another migration update | — |
| **2027-03** | Public Data API closes for all remaining apps; Redlib PR #603 notes GraphQL is also slated to close "March 2027" | Proxies end; anonymous-GraphQL redlib forks likely end |
| "next few months" | Old Reddit limited to logged-in users active in the last 6 months (mods exempt) | — |

---

## 2. Impact per engine data source (as of run #11982, 2026-10-31)

| Source (code landmark) | Role today | 11-13 | 2027-01-12 | 2027-03 | Notes |
|---|---|---|---|---|---|
| `www.reddit.com/r/a+b+c/new.rss` + `REDDIT_FEED_TOKEN` (`_combined_feed_url`, L4320) | **Primary discovery** | **dead** | — | — | Token feeds are RSS; no exemption announced |
| `old.reddit.com` RSS (slot [1]) | alt origin | dead (already login-only) | — | — | |
| Per-post `/comments/<id>/.rss` (`_fetch_post_rss`) | test-post + retraction checks | **dead** | — | — | |
| `oauth.reddit.com/comments/<id>.json` FULL MODE (`fetch_post_json` L4509) | enrichment when creds exist | ok if creds | **dead unless app registered on Devvit** | dead | Engine has **no OAuth listing path**; creds not obtainable now |
| Redlib fleet RSS/`/new` (28 hosts, `REDDIT_RSS_INSTANCES` L1180) | per-sub fallback, gallery enrichment, listing seatbelt | upstream-style hosts (plain redlib ≤0.40.0) **dead**; GraphQL/session forks (`r.naa.gg` [25], `redlib.thepixora.com` [26], maybe `r4fo`, `ducks.party`, `reallyaweso.me`) **alive** | alive | at risk (GraphQL closure) | Nachtalb fork generates RSS from its own backends — independent of Reddit RSS |
| eddrit `EDDRIT_BASE` (after miningtcup) | token-free RSS fallback | dead (eddrit reads Reddit JSON) | — | — | |
| Arctic Shift `/api/posts/search`, `/api/posts/ids` (L2233, L2473) | backfill, bodies, liveness, archive verdicts | **alive** | alive | **unknown** | Maintainer (ArthurHeitmann) worked around every 2026 change so far ("Posts should be fine", 10-21); frequent 500/522 outages in Oct (#77, #85, #87, #89); comments 1–2 days behind; ingestion method undisclosed |
| vxReddit (`reddit_proxy.py`) | media/stats | alive | **dies** unless its PRAW app is registered | dead | source: `get_embed_info_from_url_praw` + `.json?raw_json=1` |
| Embeddit (`embeddit.deltandy.me`) | selftext_html/media | alive | dies | dead | source: `src/util/oauth.ts` client_credentials |
| redditez / EmbedEZ API | media | alive | likely dies | dead | commercial, method unknown |
| Native `i.redd.it` / `v.redd.it` / `preview.redd.it` URLs | media delivery | alive | alive | alive | Reddit's CDN; no sign of gating |
| Discord webhooks | output | alive | alive | alive | |

**Net:** after 11-13 the run survives *only* through the redlib-fork RSS fallback (slow, serial) and Arctic search.
After March 2027 nothing that touches Reddit anonymously or via a script app is safe; only Devvit, Arctic Shift
(if it survives), and the CDN remain.

---

## 3. Options evaluated

Ranked by (survives 11-13) × (survives 03-2027) × effort × policy risk.

### A. Devvit app as the discovery source (recommended long-term) — ★★★★★
**Mechanism.** A tiny Devvit Web app installed on a private subreddit you create. `devvit.json` schedules a
cron task (`"*/1 * * * *"` or `*/2`), handler calls `reddit.getNewPosts({ subredditName, limit: 25 })` for each
of the six subs (cross-subreddit reads do **not** require installation there — Devvit docs example uses
`'memes'`; r/Devvit thread `1q34dym`: *"Yes you can query other posts from other subs without it being
installed there"*), de-dupes via Redis (TTL), and `fetch()`es a Discord webhook with compact JSON
(id, subreddit, title, permalink, url, createdAt, authorName, flair, spoiler/nsfw, body, bodyHtml, gallery,
secureMedia, thumbnail, score, numberOfComments, crosspostParentId, removed/removedByCategory).
Engine side: a new discovery source that reads that intake channel (Discord bot token, `GET
/channels/{id}/messages?after=`) and converts each record into the same shape `entry_to_base_data` produces —
but richer, so FULL-MODE formatting (galleries, videos, spoilers, stats) comes back for free.

**Verified facts (reddit/devvit-docs, 2026-11-01):**
- HTTP Fetch: https only, 30 s timeout, `discord.com` is on the **global fetch allowlist** (still must be listed
  in `devvit.json` → reviewed at playtest/upload, "most within 1–2 business days"); personal domains refused
  (so **not** GitHub/your own server — Discord is the transport).
- Scheduler: UNIX cron, minute granularity, 10 live recurring jobs per installation, 60 deliveries/min.
- `Post` model exposes `body`, `bodyHtml`, `gallery`, `secureMedia`, `thumbnail`, `flair`, `score`,
  `numberOfComments`, `spoiler`, `nsfw`, `crosspostParentId`, `removed`, `removedByCategory`, `toJSON()`.
- External Endpoints (pull model: your runner calls the app with a `devvit_at_` managed token, 5 req/s) exist but
  are **limited-access by form** — nice-to-have later, not needed.
- Fetching apps need a Terms + Privacy link and a "Fetch Domains" README section; Devvit Rules require deleting
  relayed content on `PostDelete` (the engine's retraction/seatbelt logic already covers this on the Discord
  side; the intake record would need the same treatment).

**Risks.** (1) Policy: Reddit explicitly said RSS outside your own communities has "no replacement", so a
relay app for subs you don't moderate is tolerated-by-platform, not blessed; an unpublished app on your own
sub never goes through directory review, but the fetch-domain review will see the README. Keep it honest
("relays new-post notifications to a private Discord"), rate-light (6 calls/min), and delete-on-removal.
(2) Account: runs under your Reddit account + an app account. (3) Devvit platform churn (0.11→0.15 in a year).
(4) New secret in prod: Discord bot token with Read Message History on one private channel.

**Effort.** ~1 day for the app (TypeScript, `npm create devvit`), 1–2 engine rounds for the intake reader
+ guards + docs. Can run in **shadow mode** alongside RSS until 11-13 to compare coverage/latency.

### B. Redlib-fork RSS as the bridge (recommended now) — ★★★★☆ short-term
**Mechanism.** Nachtalb/redlib (`r.naa.gg`, fleet slot [25]; `ghcr.io/nachtalb/redlib`) implements backends
*anonymous JSON → GraphQL → session cookie → HTML scrape → Obscura headless browser*, auto-reordered by success,
and serves RSS for every listing incl. multireddits: `/r/sub1+sub2/new.rss?limit=100` (FORK.md "RSS feeds").
Its feeds therefore keep working after Reddit's RSS is gone, as long as *some* backend reaches Reddit.
`redlib.thepixora.com` (mv12star, PR #603 GraphQL) is similar for post pages. Upstream redlib ≤ v0.40.0 is dead.

**Engine changes needed (small, one round):**
1. In the combined-feed step, after `www.reddit.com` fails, fan out `**/r/<a+b+c>/new.rss?limit=100**` to the
   GraphQL-capable hosts **in parallel, first-success**, before falling back to per-sub serial.
2. Reorder/skip: after 11-13 `www`/`old`/eddrit will fail on every run — short-circuit them when the first
   response is 404/410/403 so the run doesn't burn up to 28 × 15 s per subreddit.
3. Provenance: `FEED_SOURCE_BY_SUB` already distinguishes `reddit.com` from mirrors (Round 98) — keep the
   stale-archive override rule as is (mirror provenance must not override `removed`).
4. New log line + `r100:` guards; README/AGENTS landmine update.

**Risks.** Third-party instances (rate limits, uptime, operator decisions); anonymous GraphQL may close
March 2027 or earlier; Reddit's logged-in-only rollout could push forks to session-cookie-only mode.

### C. Self-hosted Nachtalb redlib *sidecar inside the GitHub Actions job* — ★★★☆☆ contingency
Start `ghcr.io/nachtalb/redlib:latest` as a service container in `reddit_monitor.yml`, query
`http://localhost:8080/r/<a+b+c>/new.rss` and `/comments/<id>.rss`, stop. Removes dependence on public instances.
Optional `REDLIB_REDDIT_COOKIE` (throwaway account `reddit_session`, lasts ~6 months) survives logged-in-only.
**Costs:** +20–40 s per run; GitHub Actions egress IPs may be scored worse than r.naa.gg's; a session cookie is a
ToS grey zone (account bans) — your call (§6). Workflow `run:` block size cap (21,000) must be respected —
use a `services:` block / composite step, not inline shell.

### D. Arctic Shift as discovery — ★★★☆☆ already wired, keep as backup
Posts ingestion healthy per maintainer (2026-10-21); API returns bodies (`md2html`), media hints, removal
verdicts; engine already uses it for backfill. Downsides: latency unmeasured today (was "laggier" than RSS),
October stability poor (five outage issues), single volunteer, ingestion method undisclosed → unknown fate under
logged-in-only/March 2027. Suggest adding a **lag probe log line** (newest `created_utc` vs now) so we know
what we'd get if it became primary.

### E. Keep proxies (vxReddit / Embeddit / EmbedEZ) — ★★☆☆☆ decaying
All run on registered OAuth creds → work until 2027-01-12 at best (March 2027 only if their operators register
and are granted an exemption, which Devvit cannot host). Plan for enrichment to come from A (Devvit JSON) or D
instead. No action now; the engine already degrades gracefully when they fail.

### F. Reddit's own "Discord Relay" Devvit app — ★☆☆☆☆ (not applicable unless you moderate the subs)
Trigger-based (`onPostCreate`) — only fires in subreddits where it is installed, i.e. ones you moderate.
Open-source lookalikes exist (`BoardyB/hikinghu-discord-relay`, pushed 2026-10-31) and are a good code reference
for A's webhook/de-dup/retry handling.

### G. OAuth listing path with *existing* creds — ★★★☆☆ only if you already own an approved app
If `REDDIT_CLIENT_ID/SECRET` in prod came from an app approved before today: register it at
developers.reddit.com **before 2027-01-12** (bounty form by 11-30), and add a 20-line discovery path
`oauth.reddit.com/r/<a+b+c>/new?limit=100` (100 QPM free tier). Buys time until March 2027 only.
Status unknown to me — see §6 Q1.

### H. Logged-in session scraping from the engine itself (reddit.com `.json` + `reddit_session`) — ★☆☆☆☆
Works technically (it is what the Nachtalb `cookied-json` backend does), but it is a direct User-Agreement
violation from a GitHub-hosted IP, invites account bans, and needs 2FA/cookie rotation. Not recommended; if
ever, do it via C with a throwaway, not in the engine.

### I. Commercial scrapers / third-party Reddit APIs (redditapis.com, Apify, listening tools) — ★☆☆☆☆
Cost per request, uncertain legality after March 2027, another dependency with the same upstream risk. Skip.

### J. Other mirrors checked and rejected
PullPush.io — unstable, months of missing recent posts, maintenance for weeks (2026-07/08). Pushshift — mods
only. RSS-Bridge / RSSHub reddit routes — read Reddit JSON/API → same cliff. Lemmy/Telegram mirrors of these
specific leak subs — none reliable. Strategic note: the leak content originates on X/Telegram, which the
twitter monitor (`uesu/wvkhabh2s22`) already covers — partial mitigation, not a replacement for the megathreads.

---

## 4. Recommended plan

| When | Action | Owner / effort |
|---|---|---|
| **Nov 1–6** | **Round 100 (bridge):** combined `/r/a+b+c/new.rss` on GraphQL-capable redlib hosts, parallel first-success; dead-host short-circuit after 11-13; `FEED-SOURCE` log; Arctic lag probe; guards + docs. No fleet growth beyond what already exists. | engine, 1 round |
| Nov 1–10 | **Devvit intake app (Option A)** in a new repo: `npm create devvit`, cron `*/2`, 6 × `getNewPosts`, Redis de-dup, webhook to a private `#reddit-intake` channel. Playtest on a private subreddit, submit `discord.com` fetch domain, README "Fetch Domains" + Terms/Privacy links. | you + me, ~1 day |
| Nov 8–12 | **Round 101:** engine discovery source `DISCORD_INTAKE` (bot token, `after=` cursor in the run record), mapping Devvit JSON → base data (FULL-MODE grade), shadow-compare against RSS, then promote above the redlib bridge. | engine, 1–2 rounds |
| Nov 10 | Read Reddit's migration update for any RSS clarification (private feeds, dates). | — |
| Nov 13+ | Watch run logs: expect `Combined feed` from reddit.com to fail; bridge or intake must carry. Remove `REDDIT_FEED_TOKEN` probes from the hot path once confirmed dead (keep code; skip fast). | — |
| Dec–Feb | Option C sidecar only if public forks become unreliable. Decide on throwaway-session policy. | optional |
| Mar 2027 | Expect proxies + anonymous GraphQL to end; by then Devvit intake + Arctic + CDN must be the whole stack. | — |

What stays untouched: Discord formatting (Round 99 fixes), caches, posting logic, prod repos until a PR is
approved and merged.

---

## 5. Measured facts worth remembering

- `fetch_working_reddit_feed` is **serial** across 28 hosts with `ClientTimeout(total=15)`; `_fetch_new_listing`
  is parallel with an 8 s cap. After 11-13 the serial chain is the main latency risk.
- `REDDIT_RSS_INSTANCES[25] = https://r.naa.gg` and `[26] = https://redlib.thepixora.com` are the only fleet
  members known (via fork code) to not depend on Reddit RSS/JSON for listings; `_REDLIB_POST_FAST_HOSTS` already
  includes both.
- Nachtalb/redlib `/healthz/reddit.json` reports whether the instance is currently getting Reddit JSON — usable
  as a cheap pre-flight for the bridge.
- Engine has OAuth for **per-post** JSON only (`fetch_post_json`), never for listings.
- Devvit limits: cron ≥ 1 min, 10 recurring jobs/installation, 60 deliveries/min, fetch 30 s, https only,
  `discord.com` globally allowed, External Endpoints 5 req/s (limited access).

---

## 6. Decisions needed from you

1. **Do you already hold approved `REDDIT_CLIENT_ID/SECRET`** (an app created/approved before today)? If yes →
   register it on developers.reddit.com before 2027-01-12 and I add the OAuth listing path (Option G) as a
   second bridge.
2. **Do you moderate any of the six subreddits?** If yes, Reddit's own Discord Relay / `onPostCreate` triggers
   become the sanctioned path for those.
3. **Go for the Devvit intake app (Option A)?** It runs under your Reddit account; I can scaffold the repo and
   the engine side, you run `devvit login` / `devvit upload` / install on a private sub you create.
4. **OK to add a Discord bot token secret** (read-only on one private intake channel) to the prod workflow?
5. **Throwaway-session cookies** (Options C/H): allowed as a last resort, or off the table?

Sources: r/modnews `1wubgvt`, r/redditdev `1wubcvf` (2026-09-30); Reddit CEO Q3 letter (2026-10-29);
reddit/devvit-docs (`capabilities/server/http-fetch.mdx`, `scheduler.mdx`, `external-endpoints.mdx`,
`devvit_rules.md`, `api/redditapi/RedditClient`, `models/classes/Post`); r/Devvit `1q34dym`;
Nachtalb/redlib `FORK.md`, `CONFIGURATION.md` (2026-10-31); redlib-org/redlib #551 #591 #599 #603 #604 #609;
ArthurHeitmann/arctic_shift #53 #82 #84 #85 #87 #89; dylanpdx/vxReddit `vxreddit.py`; DeltAndy123/Embeddit
`src/util/oauth.ts`; BoardyB/hikinghu-discord-relay README; heise / TechCrunch / xenospectrum / bigideasdb /
redditapis.com summaries of the same announcements.

---

## 7. Owner answers and standing decision (2026-11-01)

**Decision: no changes to the Reddit engine or the News-Express repo for now.** The feature is posting timely
and fully functional through the remaining sources (token RSS until 11-13, Arctic Shift, proxies, native
media), and the owner expects redlib/instance updates soon. This document is a prepared plan, not a work order.

Answers to §6:

1. **No approved OAuth app** — API access requested and rejected twice. Option G is closed for good.
2. **Does not own or moderate any of the six subreddits** (joined as `u/jieunlatte` only). `REDDIT_FEED_TOKEN`
   comes from `old.reddit.com/prefs/feeds` ("Private RSS feeds") — these are ordinary RSS/JSON feed URLs with a
   `feed=…&user=…` query, so they fall under the 11-13 RSS retirement; no exemption has been announced.
3. The Devvit app `ananta-news-relay` ("Ananta Cafe News", unlisted, installed in r/AnantaLeaks) is **third-party,
   not the owner's**. It still matters as a precedent: Reddit's app review accepted an unlisted "public
   subreddit posts → private Discord inbox → bot renders the card" relay with a `discord.com` fetch domain.
   Its README also documents two platform constraints to design around: private (unpublished) installs are
   limited to subreddits **under 200 members**, and Devvit secret settings are **global-only**.
4. Owner has **four verified Discord bots** — a read-only intake reader (Option A step 3) is feasible without
   new infrastructure. Current prod secrets hold webhooks, `REDDIT_FEED_TOKEN`, `NITTER_RSS_TOKEN`, `ACCOUNTS`,
   `SUBREDDITS`, `BUMP_PAT`; variable `REDDIT_MIRROR=embeddit.deltandy.me` (OAuth-backed on Embeddit's side →
   expected to last until 2027-01-12 / 2027-03 at most).
5. Throwaway-session cookies: not decided; treated as off the table unless the owner says otherwise.

### Triggers that would reopen this plan

| Signal (run log) | Meaning | Prepared response |
|---|---|---|
| `Combined feed` from `www.reddit.com` fails on consecutive runs after 11-13 (expect 403/404/410) | Reddit RSS retired as announced | Option B bridge round (combined `/r/a+b+c/new.rss` on GraphQL-capable redlib hosts, parallel) |
| Per-sub fallback runs take minutes (serial 28 × 15 s) | dead hosts burning the budget | dead-host short-circuit (part of the same round) |
| redlib-org/redlib ships a release that restores listings/post pages (watch #603/#599/#609) | fleet recovers | re-run the fleet audit from Round 99; possibly no engine change |
| `r.naa.gg` / `redlib.thepixora.com` stop answering RSS | anonymous GraphQL closed | Option C sidecar or Option A intake |
| Arctic Shift search 5xx for >1 h or newest `created_utc` lags >30 min | archive backup degraded | start Option A (Devvit intake) immediately |
| Embeddit/vxReddit 401/403 after 2027-01-12 | proxy creds revoked | enrichment from Devvit JSON / Arctic; native media unaffected |

### Update 2026-11-01 (later): Devvit relay built

Owner created the Devvit app **`gaming-express`** ("Gaming Express") under `u/jieunlatte` via
developers.reddit.com (Bare template). The relay app is implemented and tested in
`devvit/gaming-express/` (tsc + biome + 10 unit tests + esbuild all green against `@devvit/web` 0.15.1):
cron `*/2`, six concurrent `getNewPosts`, bootstrap-silent first poll, Redis de-dup (7 d), ≤10 sends per
poll, `discord.com` webhook whitelist, mentions disabled, 2000-char-safe JSON record v1. It is **not**
wired into the engine; it writes to a private Discord intake channel only (shadow mode). Engine-side
reader = a later round, only on owner approval. Run #12061 showed `REDLIB-REACH: 1/10`
(`snoo.habedieeh.re 1/1`) — first redlib post page answered since 10-29.

