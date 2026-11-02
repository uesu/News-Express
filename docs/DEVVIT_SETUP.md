# Devvit relay — setup, update and operations (owner's PC, zip route)

Operating notes for the Reddit Developer Platform app in
[`devvit/gaming-express/`](../devvit/gaming-express/) (Reddit slug `gaming-express`).
The app's own `readme.md` is deliberately short and generic because Reddit shows it on the
app's Directory page; everything an operator needs is here instead.

The relay is **not part of the engine**. `sync_prod.yml` copies `testing area/**` and
`tests/**` only, so nothing in `devvit/` reaches the production repositories, and the
engine reads the intake channel through its own code in `testing area/reddit_main_v3.py`
(§9), which *is* synced.

## 1. What it does

```
Reddit scheduler (cron */5 * * * *; */2 before 0.0.6)
   │  POST /internal/scheduler/poll
   ▼
gaming-express (runs on Reddit's servers)
   │  1. settings: intakeWebhook (secret), subreddits, officialUsers, relayEnabled
   │  2. reddit.getNewPosts({subredditName}) for each subreddit
   │     reddit.getPostsByUser({username, sort:'new'}) for each official account
   │  3. first poll per target = bootstrap: remember the newest 25 ids, send nothing
   │  4. skip ids already in Redis (seen:<id>, 7-day TTL)
   │  5. oldest-first, once per id, max 15 per poll: POST to the Discord webhook
   ▼
intake channel (private Discord channel of your choice): one ```json block per post
```

| Outcome | What the app does |
| --- | --- |
| Discord 200/204 | `seen:<id>` set for 7 days |
| Discord 429 | waits `Retry-After` (≤ 5 s) once, then retries next poll |
| Discord 5xx / network error | retries next poll; gives up after 3 failures |
| Discord 400/401/403/404 | drops the post, logs the body (webhook deleted or invalid) |
| `relayEnabled` = `false` | polls and marks posts as seen, sends nothing (no burst on resume) |
| one target fails to fetch | that subreddit/account is skipped this poll; the others continue |

Messages are sent with `allowed_mentions: {parse: []}`, so a title can never ping a role or
`@everyone`. Only `https://discord.com/api/webhooks/…` URLs are accepted.

### Intake record (v1)

```json
{"v":1,"id":"1xkw3fk","sub":"Zenlesszonezeroleaks_","title":"…","permalink":"/r/…/comments/1xkw3fk/…/",
 "url":"https://v.redd.it/7uhsezpi4yyh1","created":1793514871,"author":"…","flair":"Reliable",
 "distinguished":null,"spoiler":false,"nsfw":false,"score":1,"comments":1,"removed":null,"xpost":null,
 "media":["https://v.redd.it/7uhsezpi4yyh1/CMAF_1080.mp4?source=fallback","https://external-preview.redd.it/….png"],
 "body":"","bodyTruncated":false}
```

- Field order and names are stable; consumers key on them.
- `sub` is the configured subreddit for subreddit listings. For official-account feeds it
  is the subreddit the post was actually made in — `u_genshinimpact` for a profile post,
  `Genshin_Impact` when the account posted there — which is what Game-Express's
  `allowed_subs` (`u_<account>` + the game's subreddits) already expects.
- A post that appears in both an account feed and a subreddit listing is relayed once.
- `distinguished` (0.0.4 code / Reddit version `0.0.3`) is `"moderator"` / `"admin"` when the
  post is distinguished, else `null`. Classification is the consumer's job; the relay only carries
  the signals (`author`, `flair`, `distinguished`).
- **Wuthering Waves has no publisher account on Reddit** (`u/WutheringWaves` is an unrelated
  2022 account — never add it to `officialUsers`). Verified against the Arctic Shift archive on
  2026-11-02: `u/WutheringWavesMod` posts **only** the Daily/Weekly megathreads (flair
  `Megathread`, not distinguished), and the official content — Special Program (`1xd9vyy`,
  `1wt05uz`), the 3.8 preview broadcast date (`1xj48d3`), codes, trailers, version news — arrives
  as **community re-posts under the `Official News` flair** (`:YangyangSide: Official News`,
  authors such as `cakeel-`, `Recent-Usual-9434`), also not distinguished. The relay already
  delivers these from `r/WutheringWaves` with `"flair":":YangyangSide: Official News"`; the
  Game-Express rule (`_is_official_subreddit_post`: configured author **or** distinguished **or**
  flair matching `\bofficial\b`) matches them today, and the intake reader keeps that rule. The
  flair is self-selected, so expect duplicates (the same Kuro tweet re-posted several times) and the
  odd mis-flaired post — the consumer de-duplicates by title/link and treats them as unverified.
- `body` is trimmed (and `bodyTruncated` set) when the message would exceed Discord's
  2000-character limit; identity fields are never trimmed. `score`/`comments` are the values
  at poll time.
- Measured latency on 2026-11-01: 30–60 s from post creation to the intake message, versus
  6–10 min for the RSS-based engine on the same posts.

### Default targets (settings)

| Setting | Default |
| --- | --- |
| `subreddits` | `AnantaLeaks,Genshin_Impact_Leaks,HonkaiNexusAnimaLeaks,HonkaiStarRail_leaks,WutheringWavesLeaks,Zenlesszonezeroleaks_` (News-Express) + `Genshin_Impact,HonkaiStarRail,ZZZ_Official,WutheringWaves,HonkaiNexusAnima,AnantaOfficial` (Game-Express `reddit.subreddits`) |
| `officialUsers` | `genshinimpact,HonkaiStarRail,HonkaiNexusAnima` — the verified accounts that actually post (audit below). Optional: every one of them posts only into its own subreddit, which is already in `subreddits`, so this is a second path, not the only one. May be left empty. |
| `relayEnabled` | `true` |

12 subreddit calls + 3 account calls every 5 minutes = 3 requests/min, far inside the
platform's 100 requests/min budget (0.0.6; the 2-minute cadence of 0.0.1–0.0.5 was ≈ 7.5/min
and ran for a day with `0 failed` — 5 minutes matches the engines' own cron and leaves even
more headroom). Up to 15 Discord sends per poll; anything beyond waits for the next tick.

### Publisher-account audit (Arctic Shift archive + live profiles, 2026-11-02)

"Official" is decided by the consumer from `sub` + `author` + `flair` (+ `distinguished`), never
by which list a post came through. The audit that fixed the default:

| Game | Account | Verified | Posts | Where official content actually appears | In default? |
| --- | --- | --- | --- | --- | --- |
| Genshin | `u/genshinimpact` | yes | daily (25 in 8 days), all in `r/Genshin_Impact`, flair `Official Media` / `Official Post` | own posts | **yes** |
| HSR | `u/HonkaiStarRail` | yes | daily, all in `r/HonkaiStarRail`, flair `Official Announcement` (e.g. `1xjdyj9` "A Brief on the Version 4.7 Special Program") | own posts | **yes** |
| HNA | `u/HonkaiNexusAnima` | yes | when there is news (last burst 2026-07, Evolution Test), flair `Official Announcement` | own posts | **yes** |
| ZZZ | `u/ZZZ_Official` | no | one post ever (2024-04 merch raffle); `u/Bangboo_ZZZ` (mod) last 2024-12 | community re-posts in `r/ZZZ_Official` under `Official Media` (`1xktjo2`, `1xk0ohy`, `1xfnbwk`) | no — dormant |
| Ananta | `u/AnantaOfficial` | no | one post ever (2024-12, removed) | community re-posts in `r/AnantaOfficial` under `Official Media` (`1wrpgo9`) | no — dormant |
| WuWa | — | — | no publisher account (`u/WutheringWaves` is unrelated; `u/WutheringWavesMod` posts only megathreads) | community re-posts in `r/WutheringWaves` under `Official News` | no account exists |

Consumer rule (Game-Express `_is_official_subreddit_post`, kept by the intake reader): author in
the verified set **or** flair matching `\bofficial\b` (`Official Media`, `Official Announcement`,
`Official Post`, `Official News`) **or** `distinguished`. Flair-matched posts are community
re-posts: de-duplicate by title/link and treat as unverified. Adding a subreddit or an account
later is a settings change only (`npx devvit settings set …`), no code or upload.

## 2. Prerequisites (once)

- Windows, **Command Prompt** (not PowerShell), NanaZip or the built-in extractor.
- Node.js LTS (24.18+; the app was deployed with 26.13 / npm 11.20). Verify with
  `node -v` and `npm -v`.
- A Reddit account that owns a **private subreddit** used only as the install target
  (`r/GamingExpressRelay`). Nothing is ever posted there.
- A private Discord channel for the records (the **intake channel** — any name; the owner
  started with `#reddit-intake` and moved to `#modlogs`) with one webhook. Copy the URL;
  never paste it into a file or a public channel. Other bots may write to the same channel
  (the readers skip every message that is not a relay record), but keep it reasonably quiet:
  the readers page newest-first through at most 800 messages per run, so a very busy
  channel only shortens the 6-hour look-back, it never hides fresh records.
- `npx devvit login` once (opens the browser, links the CLI to the Reddit account).

## 3. Fresh deploy or update (same procedure every time)

1. Delete the previous copy: `%USERPROFILE%\Downloads\News-Express-main` and
   `News-Express-main.zip`.
2. Download `https://github.com/uesu/News-Express/archive/refs/heads/main.zip` and
   extract it in `Downloads` (NanaZip → *Extract Here (Smart)*).
3. In Command Prompt:

   ```
   cd %USERPROFILE%\Downloads\News-Express-main\devvit\gaming-express
   npm ci
   npm test
   ```

   `npm ci` prints deprecation and audit warnings for transitive packages of the Devvit
   CLI — expected, not actionable here. `npm test` must end with `pass N` / `fail 0`
   (16 tests as of 0.0.3) followed by the esbuild line.

4. Upload and switch the installation to the new version:

   ```
   npx devvit upload
   npx devvit install GamingExpressRelay
   ```

   `upload` prints `Automatically bumped app version to: 0.0.N` (the number comes from
   Reddit's server, not from the zip) and ends with the version URL. `install` upgrades the
   existing installation in place — one version runs at a time, the previous one stops the
   moment the install completes; there is nothing to delete.

5. Settings are global and persist across versions. First deploy only:

   ```
   npx devvit settings set intakeWebhook     → paste the webhook URL
   ```

   After an upgrade that changed the default target lists, pin them explicitly so the
   installation does not depend on which default it captured:

   ```
   npx devvit settings set subreddits
   → AnantaLeaks,Genshin_Impact_Leaks,HonkaiNexusAnimaLeaks,HonkaiStarRail_leaks,WutheringWavesLeaks,Zenlesszonezeroleaks_,Genshin_Impact,HonkaiStarRail,ZZZ_Official,WutheringWaves,HonkaiNexusAnima,AnantaOfficial
   npx devvit settings set officialUsers
   → genshinimpact,HonkaiStarRail,HonkaiNexusAnima
   npx devvit settings set relayEnabled
   → true
   npx devvit settings list
   ```

   Newly added targets are bootstrapped silently on their first poll (remembered, not sent).

6. Watch two or three polls, then `Ctrl+C` → `Y`:

   ```
   npx devvit logs GamingExpressRelay
   ```

   Expected line every 5 minutes (every 2 minutes before 0.0.6):

   ```
   poll: 12 subs, 3 users, N fetched, 0 sent, N seen, 0 failed, N bootstrapped
   ```

   `bootstrapped` is non-zero only on the first poll after a target was added. From then on
   `sent` equals the number of genuinely new posts, each exactly once.

7. Close Command Prompt. The copy in `Downloads` can be deleted — the app runs on Reddit.

Subreddit menu on `r/GamingExpressRelay` (`…` → **[Gaming Express] Poll now** /
**[Gaming Express] Status**) gives a manual run and a one-line health check.

## 4. Operations

- **Pause / resume:** `npx devvit settings set relayEnabled` → `false` / `true`. The CLI
  stores the typed text; 0.0.3+ understands `false`, `0`, `no`, `off`, `paused`.
- **Add or remove a subreddit / account:** `npx devvit settings set subreddits` (or
  `officialUsers`) with the full comma-separated list. Effective on the next poll.
- **Stop completely:** `npx devvit uninstall GamingExpressRelay`.
- **Directory page** (`developers.reddit.com/apps/gaming-express`): the app is unpublished
  and installed only on the private subreddit. Keep the listing generic — no repository
  links are needed because the app is not submitted for publication; the Terms/Privacy URL
  fields can stay empty.

## 5. Troubleshooting

| Symptom | Meaning / action |
| --- | --- |
| `npx devvit upload` → `"Create" failed after 3 attempts. First error: fetch failed` | The bundle upload never reached Reddit (local network/DNS/firewall). Nothing was created. Run `npx devvit upload` again. |
| `upload` → `Create failed after 3 attempts. First error: fetch failed. Last error: You must be logged in to upload a new app version.` while `npx devvit whoami` works | **Not an auth problem.** Only the one large `AppVersion.Create` POST (the ~7 MB bundle) is failing; reads (`whoami`, the version check) are tiny and succeed. Observed 2026-11-01 ~10:00–18:00Z, five attempts, including after `logout`/`login`; the same command succeeded unchanged at ~20:20Z. Documented by Reddit as an intermittent server-side fault (Devvit FAQ). Re-logging in, re-downloading, or creating a new app does **not** help (a new app goes through the same call and burns the name). Wait and retry; to see the real cause of `fetch failed` run `set NODE_DEBUG=fetch` before the upload; try another network (phone hotspot) once. |
| `npx devvit whoami` → not logged in / token error | The token at `%USERPROFILE%\.devvit\token` expired or was removed. `npx devvit login` (browser) and continue. |
| `upload` → `settings.global.<key> is not exactly one from …` | `devvit.json` schema violation (for example `isSecret: true` together with `defaultValue`). The unit test guards the known case; validate against `node_modules/@devvit/shared-types/schemas/config-file.v1.json`. |
| `install` → `Something went wrong…` | Transient on Reddit's side on a brand-new subreddit; retry once. |
| logs: `intakeWebhook is empty or not a discord.com webhook URL — polling only` | Secret not set (or not a `discord.com/api/webhooks` URL). Set it; no posts are lost — they are remembered, not sent. |
| the same post arrives on every poll | Was the v0.0.1 defect (Redis key spelling). Fixed in 0.0.2; upgrade. |
| `relayEnabled` set to `false` but posts keep arriving | Was the v0.0.2 defect (string `"false"`). Fixed in 0.0.3; upgrade. |
| `poll:` shows `issue(s): r/<sub>: …` | That target failed this poll (private/banned subreddit, typo, API hiccup); the others continue. Check the name with `settings list`. |

## 6. Data handling

Redis (per installation): `seen:<postId>` (7-day TTL), `boot:<subreddit>` /
`boot:u/<account>`, `fail:<postId>`, `last:poll`, `total:sent`. No user data beyond the
public author name inside the relayed record. Records live only in the private Discord
channel.

## 7. Clean uninstall of the PC-side tooling

Reddit side first: `npx devvit uninstall GamingExpressRelay`, then `npx devvit logout`.
PC: delete `%USERPROFILE%\Downloads\News-Express-main` and the zip → Settings › Apps ›
Node.js › Uninstall → delete `%USERPROFILE%\.devvit`, `%APPDATA%\npm`,
`%APPDATA%\npm-cache`, `%LOCALAPPDATA%\npm-cache`, `%USERPROFILE%\.npm`,
`%USERPROFILE%\.cache\devvit`, `C:\Program Files\nodejs` if left → remove both
"Node.js JavaScript Runtime" Windows Firewall rules → reboot.

## 8. Version history

| Version | Date | Change |
| --- | --- | --- |
| 0.0.1 | 2026-11-01 | first live install on `r/GamingExpressRelay`; six News-Express subreddits |
| 0.0.2 | 2026-11-01 | Redis keys on the bare post id — fixes the re-send of every post on every poll |
| 0.0.3 | 2026-11-01 | `relayEnabled` accepts the CLI's text `"false"`; `officialUsers` setting (`getPostsByUser`); Game-Express subreddits and accounts in the defaults; in-poll de-dup across targets; `dev.subreddit` pinned; generic Directory readme; this document. Reached Reddit as **`0.0.2`** on 2026-11-01 20:20Z after a ~10 h server-side upload fault (0.0.2 itself never uploaded, so Reddit's counter is one behind this table). |
| 0.0.4 | 2026-11-02 | intake record gains `distinguished` (`"moderator"`/`"admin"`/`null`); documented how official Wuthering Waves content reaches the relay (`Official News` flair on `r/WutheringWaves`, no publisher account, `officialUsers` unchanged); Biome schema 2.6.4; troubleshooting entries for the upload fault. Uploads as Reddit **`0.0.3`**. |
| 0.0.5 | 2026-11-02 | `officialUsers` default trimmed to the verified, active accounts (`genshinimpact,HonkaiStarRail,HonkaiNexusAnima`); dormant `u/ZZZ_Official` / `u/AnantaOfficial` dropped (publisher-account audit above); setting documented as optional. Settings persist, so existing installs must re-pin `officialUsers` (§3 step 5). Uploads as Reddit **`0.0.4`**. |
| 0.0.6 | 2026-11-02 | poll cadence 2 → **5 minutes** (owner's choice, matching the 5-minute engine crons; 3 requests/min); per-poll send cap 10 → 15 so the per-minute ceiling is unchanged. No record-format change. Uploads as Reddit **`0.0.5`**. |

## 9. News-Express reader (round 101 — the relay as the primary listing)

Since round 101 the Reddit engine (`testing area/reddit_main_v3.py`) reads the intake channel
back **before** the combined feed. While the relay is healthy (HTTP 200 and the newest
message younger than `INTAKE_STALE_SECONDS`, default 1800 s) the relay is the listing and the
RSS / redlib / Arctic sweep is skipped; in every other state the run logs one
`INTAKE-FALLBACK: relay <status> (<why>)` line and the old chain runs exactly as before.
Record of the design: [`docs/history/ROUND_101.md`](history/ROUND_101.md); shared-channel
paging and freshness rules: [`docs/history/ROUND_102.md`](history/ROUND_102.md).

### One-time setup (owner; nothing changes until both the secret and the Variable exist)

1. **Bot.** `discord.com/developers/applications` → *New Application* (any name, e.g.
   `News-Express reader`) → *Bot* → **Reset Token** → copy it once (it is shown once).
   On the same page, under *Privileged Gateway Intents*, enable **Message Content Intent** —
   without it the API returns webhook-authored messages with an empty `content`.
2. **Invite.** *OAuth2* → *URL Generator* → scope `bot` → bot permissions **View Channels** and
   **Read Message History** → open the generated URL → pick the Citlali News server → Authorize.
3. **Channel permission.** The intake channel is private: channel → *Edit Channel* →
   *Permissions* → add the bot (or its role) → allow *View Channel* and *Read Message History*.
4. **Channel id.** Discord → *User Settings* → *Advanced* → *Developer Mode* on → right-click
   the intake channel → *Copy Channel ID* (a 17–20-digit number).
5. **Prod repo `uesu/7jkxmy9nvbc`.** *Settings → Secrets and variables → Actions*:
   - Secret `DISCORD_BOT_TOKEN` = the token from step 1.
   - Variable `INTAKE_CHANNEL_ID` = the id from step 4.
   (News-Express the dev repo needs neither; the workflow syncs through `sync_prod.yml`.)
6. **Verify on the next run.** The step summary's settings line ends with
   `intake primary (relay ok; N record(s), newest S s)` and *Combined fetch status* reads
   `relay`; `monitor.log` has `INTAKE: relay ok — …`. Before step 5 each run logs
   `INTAKE-FALLBACK: relay unconfigured …` and behaves exactly as before.

### Switches (repo Variables, all optional)

| Variable | Default | Meaning |
| --- | --- | --- |
| `INTAKE_READER` | `primary` | `primary` = relay is the listing when healthy; `shadow` = read + compare, old chain decides (`INTAKE-SHADOW` log line); `off` = never read the channel |
| `INTAKE_STALE_SECONDS` | `1800` | newest relay message older than this ⇒ old chain this run |
| `INTAKE_LOOKBACK_SECONDS` | `21600` | how far back the channel is read each run (held posts re-enter while inside this window; ≤ 8 pages of 100) |

### Reader-side troubleshooting

| Log / summary | Meaning / action |
| --- | --- |
| `INTAKE-FALLBACK: relay unconfigured` | secret or Variable missing in the prod repo (step 5) |
| `relay http_401 (bot token rejected)` | token wrong or reset — paste the current one |
| `relay http_403 (bot lacks View Channel / Read Message History…)` | step 3 |
| `relay http_404 (channel id unknown to this bot…)` | wrong id, or the bot was never invited (step 2) |
| `relay ok` but `0 record(s) for this engine` every run | records arrive with empty `content` ⇒ Message Content Intent off (step 1), or the `sub` names do not match `SUBREDDITS` |
| `relay stale (newest relay message is N s old)` | the relay is paused (`relayEnabled=false`), uninstalled, or Reddit is quiet; `npx devvit logs GamingExpressRelay` — harmless either way, the old chain ran |
| `relay empty` | no message in the lookback window at all — same causes as stale |
| `relay empty (N message(s) in the last 360 min but none is a relay record …)` | the bot sees the channel but no relay record: Message Content Intent off (step 1), wrong channel id, or the relay webhook (`intakeWebhook`) still points at the old channel — `npx devvit settings set intakeWebhook` |

## 10. Roadmap (each step its own PR, none started without an explicit go)

1. ~~Let the relay run clean for a few days~~ — waived by the owner on 2026-11-02; round 101
   shipped the reader with the old chain as the automatic fallback.
2. ~~**News-Express intake reader**~~ — done in round 101 (§9). Relay 0.0.6 candidates if the
   reader needs them: a heartbeat record (exact staleness), a long-body attachment
   (bodies above the message budget arrive truncated today).
3. ~~**Game-Express**~~ — delivered in round 102 as a `git am`-able patch plus
   description: `docs/handoffs/GAME_EXPRESS_INTAKE_READER.md`. `RedditClient._gather_listing()`
   asks the reader first; `u/<account>` listings are served from records whose `author` is
   that account (records carry the real subreddit in `sub`), subreddit listings per `sub`;
   the same two settings activate it in `uesu/8mqzv4k2n7c`.
4. Optional relay additions if the readers need them: author follow-up comments
   (Game-Express merges the publisher's own comment), post edits/removals as update
   records.

Dates that drive this: 2026-11-13 Reddit RSS retired (kills the engine's reddit.com feed
hosts and Game-Express's `REDDIT_FEED_TOKEN` path); 2027-01-12 unregistered access removed
(kills the redlib fleet); 2027-03 public Data API closed. Only the Developer Platform path
survives all three.
