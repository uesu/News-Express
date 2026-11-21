# Devvit relay — setup, update and operations (owner's PC, zip route)

Operating notes for the Reddit Developer Platform app in
[`devvit/gaming-express/`](../devvit/gaming-express/) (Reddit slug `gaming-express`).
The app's own `readme.md` is the text Reddit shows on the app's Directory page: a generic
product readme (behaviour, setup, settings, inbox contract, fetch domains, sources) that
names no repository and no consumer, and keeps the exact numbers, Redis keys, record schema
and command sequence out — enough to understand the app, not enough to clone the pipeline.
Operating notes for *this* deployment live here.

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
- `npx devvit login --copy-paste` once (opens the browser, you paste the code shown there
  back into Command Prompt). See §3 step 4 for why the `--copy-paste` form is the one to use.

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

   `npm ci` may print deprecation and audit warnings for transitive packages of the Devvit
   CLI. `npm test` must end with `pass N` / `fail 0` followed by the esbuild line; use the
   count printed by the current checkout rather than a historical fixed test count.

4. Log in with the **copy-paste** flow, upload, switch the installation to the new version:

   ```
   npx devvit logout
   npx devvit login --copy-paste
   npx devvit whoami
   npx devvit upload --copy-paste
   npx devvit install GamingExpressRelay
   npx devvit logs GamingExpressRelay
   ```

   `login --copy-paste` prints a reddit.com link: open it, approve as the relay account,
   copy the code the page shows, paste it into Command Prompt, Enter. `whoami` must name
   the relay account. `upload` prints `Automatically bumped app version to: 0.0.N` (the
   number comes from Reddit's server, not from the zip) and ends with
   `✨ Visit https://developers.reddit.com/apps/gaming-express`. `install` upgrades the
   existing installation in place — one version runs at a time, the previous one stops the
   moment the install completes; there is nothing to delete. The **Update** button on
   `developers.reddit.com/r/GamingExpressRelay/apps/gaming-express` does the same thing as
   `install`; after using it the CLI answers `Version 0.0.N has already been installed`,
   which is the confirmation, not an error. `logs` should show the normal poll line and, when
   delivered posts are due, `recheck N looked, N update msg, N re-sent`.

   Recheck work is stored in the installation's Redis state and is pruned automatically after
   the 24-hour schedule (plus its 30-minute scheduling slack). An in-place update preserves
   that state; do **not** uninstall/reinstall or clear Redis just to make the pending count
   zero, because that discards dedup/recheck history and can cause duplicate deliveries. A
   zero recheck count means no delivered posts are due on that poll, not an error. Relay
   candidates bypass legacy transient retry throttles, but a terminal removal/deletion hold in
   `pending_reddit.json` remains active until a newer clean relay listing confirms restoration.
   Do not clear that file to force a held post through.

   **Why `--copy-paste`** (2026-11-02, CLI 0.15.1, Windows 11): the default
   `npx devvit login` (localhost callback, OAuth client `Bep8X2RR…`) produced a token that
   every tiny call accepted (`whoami`, `list apps`, `GetUserAccountInfoIfExists`,
   `GetBySlug`, asset sync all `HTTP 200`) but that the Dev Portal refused on the one call
   that matters: `AppVersion/Create` → `HTTP 401` → `Error: You must be logged in to upload a
   new app version.` Logout/login did not change it, and it had cost a whole afternoon the
   day before. The copy-paste login uses Reddit's second CLI OAuth client (`TWTsqXa5…`,
   redirect `developers.reddit.com/cli-login`); with that token the same upload returned
   `AppVersion/Create – HTTP 200` on the first try (Reddit 0.0.5). Nothing in the project
   files was involved. `set NODE_DEBUG=fetch` before the command shows the per-request
   status codes if this ever needs to be diagnosed again.

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

   `settings list` shows the keys, labels and types only — never the values — so a changed
   webhook is confirmed by the next record arriving in the new channel, not by the CLI.
   Newly added targets are bootstrapped silently on their first poll (remembered, not sent).

6. Watch two or three polls, then `Ctrl+C` → `Y`:

   ```
   npx devvit logs GamingExpressRelay
   ```

   Expected line every 5 minutes (every 2 minutes before 0.0.6; 0.0.7+ appends `; recheck N looked, N update msg, N re-sent`):

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
  and installed only on the private subreddit. Keep the listing generic — the readme names
  no repository, no consumer and no retired Reddit feature, and the Terms/Privacy URL fields
  can stay empty because the app is not submitted for publication. The readme is part of the
  upload bundle: a readme change ships with the next `npx devvit upload --copy-paste` +
  `install` (§3 step 4); the version number is assigned by the server, nothing to bump.

## 5. Troubleshooting

| Symptom | Meaning / action |
| --- | --- |
| `npx devvit upload` → `"Create" failed after 3 attempts. First error: fetch failed` | The bundle upload never reached Reddit (local network/DNS/firewall). Nothing was created. Run `npx devvit upload` again. |
| `upload` → `Error: You must be logged in to upload a new app version.` (with or without `Create failed after 3 attempts … fetch failed` in front) while `npx devvit whoami` works | The Dev Portal answers `HTTP 401` to `AppVersion/Create` for the token the default localhost login issued, while every other call succeeds. Seen 2026-11-01 (all afternoon) and again 2026-11-02 right after a fresh `logout`/`login`. **Fix: `npx devvit logout` → `npx devvit login --copy-paste` → `npx devvit upload --copy-paste`** (§3 step 4) — uploaded on the first try both times it was used. Re-downloading, editing `package.json`'s version (0.15.1 takes the number from the server) or creating a new app do **not** help (a new app burns the name). `set NODE_DEBUG=fetch` before the command shows the status code of each request. The FAQ entry for this message says to report it with `--verbose` output in r/Devvit if even that fails. |
| `npx devvit whoami` → not logged in / token error | The token at `%USERPROFILE%\.devvit\token` expired or was removed. `npx devvit login --copy-paste` and continue. |
| `upload` → `settings.global.<key> is not exactly one from …` | `devvit.json` schema violation (for example `isSecret: true` together with `defaultValue`). The unit test guards the known case; validate against `node_modules/@devvit/shared-types/schemas/config-file.v1.json`. |
| `install` → `Something went wrong…` | Transient on Reddit's side on a brand-new subreddit; retry once. |
| logs: `intakeWebhook is empty or not a discord.com webhook URL — polling only` | Secret not set (or not a `discord.com/api/webhooks` URL). Set it; no posts are lost — they are remembered, not sent. |
| the same post arrives on every poll | Was the v0.0.1 defect (Redis key spelling). Fixed in 0.0.2; upgrade. |
| `relayEnabled` set to `false` but posts keep arriving | Was the v0.0.2 defect (string `"false"`). Fixed in 0.0.3; upgrade. |
| `poll:` shows `issue(s): r/<sub>: …` | That target failed this poll (private/banned subreddit, typo, API hiccup); the others continue. Check the name with `settings list`. |

## 6. Data handling

Redis (per installation): `seen:<postId>` (7-day TTL), `boot:<subreddit>` /
`boot:u/<account>`, `fail:<postId>`, `last:poll`, `total:sent`; since 0.0.7 also the
re-check bookkeeping `sent:z`, `stage:<postId>`, `state:<postId>`, `bh:<postId>` (a short
hash of the body, to notice edits), `rev:<postId>`, and `attach:fails` / `attach:off`. No
user data beyond the public author name inside the relayed record. Records live only in the
private Discord channel (the complete record as the message's `record.json` attachment).

## 7. Clean uninstall of the PC-side tooling

Reddit side first: `npx devvit uninstall GamingExpressRelay`, then `npx devvit logout`.
Do this only when the relay is being retired for good — every future upload needs the CLI.
PC: delete `%USERPROFILE%\Downloads\News-Express-main` and the zip → Settings › Apps ›
Node.js › Uninstall → delete `%USERPROFILE%\.devvit`, `%APPDATA%\npm`,
`%APPDATA%\npm-cache`, `%LOCALAPPDATA%\npm-cache`, `%USERPROFILE%\.npm`,
`%USERPROFILE%\.cache\devvit`, `C:\Program Files\nodejs` if left → remove both
"Node.js JavaScript Runtime" Windows Firewall rules → reboot.

## 8. Version history

The **code** versions below are the repository's numbering (rounds 99–104). Reddit numbers
uploads itself: 0.0.1–0.0.4 were uploaded one by one; code 0.0.5–0.0.8 went up together as
**Reddit 0.0.5** on 2026-11-02 (merge of PR #109, `--copy-paste` login); the readme-only
code 0.0.9 went up as **Reddit 0.0.6** on 2026-11-03 (same code as 0.0.8, settings and Redis
memory carried over, no re-bootstrap), code 0.0.10 (devvit 0.15.2) as **Reddit 0.0.7** and code
0.0.11 (devvit 0.15.3) as **Reddit 0.0.8**, live on `r/GamingExpressRelay` since then.
`npx devvit install` / the portal's **Update** button name the Reddit number.

| Version | Date | Change |
| --- | --- | --- |
| 0.0.1 | 2026-11-01 | first live install on `r/GamingExpressRelay`; six News-Express subreddits |
| 0.0.2 | 2026-11-01 | Redis keys on the bare post id — fixes the re-send of every post on every poll |
| 0.0.3 | 2026-11-01 | `relayEnabled` accepts the CLI's text `"false"`; `officialUsers` setting (`getPostsByUser`); Game-Express subreddits and accounts in the defaults; in-poll de-dup across targets; `dev.subreddit` pinned; generic Directory readme; this document. Reached Reddit as **`0.0.2`** on 2026-11-01 20:20Z after a ~10 h server-side upload fault (0.0.2 itself never uploaded, so Reddit's counter is one behind this table). |
| 0.0.4 | 2026-11-02 | intake record gains `distinguished` (`"moderator"`/`"admin"`/`null`); documented how official Wuthering Waves content reaches the relay (`Official News` flair on `r/WutheringWaves`, no publisher account, `officialUsers` unchanged); Biome schema 2.6.4; troubleshooting entries for the upload fault. Uploads as Reddit **`0.0.3`**. |
| 0.0.5 | 2026-11-02 | `officialUsers` default trimmed to the verified, active accounts (`genshinimpact,HonkaiStarRail,HonkaiNexusAnima`); dormant `u/ZZZ_Official` / `u/AnantaOfficial` dropped (publisher-account audit above); setting documented as optional. Settings persist, so existing installs must re-pin `officialUsers` (§3 step 5). Uploads as Reddit **`0.0.4`**. |
| 0.0.6 | 2026-11-02 | poll cadence 2 → **5 minutes** (owner's choice, matching the 5-minute engine crons; 3 requests/min); per-poll send cap 10 → 15 so the per-minute ceiling is unchanged. No record-format change. Uploads as Reddit **`0.0.5`**. |
| 0.0.7 | 2026-11-02 | **the relay is the complete source** (round 103). (a) Every record message also carries **`record.json`** — the untrimmed record (full body, every media URL, video renditions, the crosspost parent as a nested record) — sent as a multipart webhook upload; the inline fenced record stays `v: 1` (new optional keys `full`, `mediaTruncated`, `edited`, `revision`, `xpostPermalink`, `video`), so older readers keep working. If Discord refuses the form, the record goes out as plain content exactly as before (`attachment refused` log line; three in a row pause the attachment for an hour). (b) **Post-delivery re-check**: each delivered post is looked at again ~10 min, 30 min, 2 h and 6 h after creation (`reddit.getPostById`, ≤ 20 per poll) and the result is written as one batched **`v: 2` update message** per poll (`{v:2,kind:"update",at,posts:[{id,sub,age,stage,removed,deleted,edited,spoiler,…,locked,score,comments}]}`) — the first look always, later looks only when the state changed. An **edited body** is re-sent as a `v: 1` record with `revision` ≥ 2 (readers keep the newest message per id). New Redis keys: `sent:z` (sorted set, 7.5 h), `stage:<id>`, `state:<id>`, `bh:<id>`, `rev:<id>`, `attach:fails`/`attach:off`. Poll line gains `; recheck N looked, N update msg, N re-sent`. Uploads as Reddit **`0.0.6`**. |
| 0.0.8 | 2026-11-02 | **1:1 with the old chain** (round 104). (a) Re-check stages ~**5 min** / 30 min / 2 h / 6 h / **24 h** (the first look is the next poll after delivery; late approvals and late publisher comments are caught by the 24 h look). (b) A post first seen filtered/removed and later live (**approval**) is re-sent complete (`resent: "approved"`, `revision` ≥ 2; reasons join with `+`) so a reader whose 6 h window lost the first record still has the whole post. (c) Record keeps `v: 1`; `RECHECK_WINDOW` 24 h + 30 min. A publisher-comment follow-up was prototyped the same day and dropped at the owner's request before upload (neither engine shows OP comments). Uploads as Reddit **`0.0.7`**. |
| 0.0.9 | 2026-11-03 | Directory readme rewritten as a full product readme (how it works, delivery semantics, setup, settings, inbox contract with `v:1` / `v:2` examples, permissions, Devvit/Discord sources, toolchain). No code change. Vaguer second pass the same day (#116: no exact numbers, keys, schema or command sequence). Uploaded as Reddit **`0.0.6`** on 2026-11-03 10:16 PHT and installed in place. |
| 0.0.10 | 2026-11-03 | `devvit` / `@devvit/web` 0.15.1 → **0.15.2** (release notes: Community Engagement Playbook docs + `media.upload` attribution — nothing the relay uses; the portal's App Versions tab flagged 0.15.1 with "a new version of Devvit is available"). No code change; 25 unit tests, build and schema check green. Uploads as Reddit **`0.0.7`**. |
| 0.0.11 | 2026-11-10 | `devvit` / `@devvit/web` 0.15.2 → **0.15.3** (tarball diff: `@devvit/shared-types` fetch polyfill wraps the response body as `Uint8Array`; `@devvit/reddit` `getCurrentUsername()` reads `context.username`; dev-portal proto fields; the other packages differ in source maps only — nothing the relay uses). No code change; 25 unit tests, build and lint green. Uploads as Reddit **`0.0.8`**. |

| 0.0.13 | Unreleased | Spoiler-flag-only changes resend a higher-revision full record so News-Express can PATCH the existing Discord card; the Python reader consumes terminal Devvit removal/deletion updates and deletes saved Discord card/page/YouTube companion IDs automatically, preserving retryable AutoMod-filtered items. Reader changes make the relay the sole default intake, pause rather than probe/fall back when unhealthy, and bypass generic legacy fresh-age/transient pending throttles for relay candidates while still enforcing terminal removal/deletion holds until a newer clean relay listing confirms restoration; the retained old engine remains available explicitly. Devvit source changes are not live until uploaded/installed. No `RETRACT_*` Variables or Reddit `/new` absence probes are used for post-delivery deletion. |
| 0.0.12 | Superseded before upload | The proposed 48 h Devvit recheck stage is withdrawn; the relay remains on its existing 5 min / 30 min / 2 h / 6 h / 24 h schedule. Python's 48 h intake/cache window and relay Discord-ID retention remain separate and do not extend Devvit's checks. The earlier proposal also documented revised-card PATCHes and the optional `SPOILER_MEDIA_AND_BODY=1` behavior; this switch remains off unless explicitly enabled. |

## 9. News-Express reader (round 101 — the relay as the primary listing)

The Reddit engine (`testing area/reddit_main_v3.py`) reads the intake channel before
processing candidates. With the default `INTAKE_READER=primary`, Devvit is the sole active
intake and authority: only a healthy relay is processed. Stale, empty, unconfigured, or
unreachable intake logs `INTAKE-PAUSED` and pauses delivery; it does not fall back to or probe
the old RSS / Redlib / Arctic listing engine. To deliberately use the retained old engine,
set `INTAKE_READER=off`; `shadow` runs the old engine and logs a comparison for diagnostics.
The old engine keeps its own fresh-hold and pending-recheck behavior. Relay candidates bypass
the generic fresh-age and transient pending-retry throttles and do not use old-chain liveness
probes. The reader still enforces terminal removal/deletion evidence in each relay record, and
retains those terminal pending holds until a newer clean relay listing confirms restoration;
AutoModerator queue states remain retryable.

Since relay 0.0.7 the relay also carries the complete record (`record.json`); relay-served
posts make no Redlib, reddit.com, or Arctic request. The vxreddit / embedez / embeddit proxies
remain available for supported media resolution as part of the relay delivery structure.

- **Full body, full media, crosspost parent** — read from the message's `record.json`
  (`cdn.discordapp.com`, no token) only when the inline record was cut or names a crosspost
  parent; ≤ `INTAKE_ATTACHMENT_FETCHES` = 10 per run. A failed attachment read leaves the
  round-101 behaviour (archive/proxy fill-in, relayed part as last resort).
- **Liveness from the relay's re-checks** — the latest `v: 2` update per post is consulted by
  `candidate_liveness_verdict()` before the record's own `removed` and before any archive
  lookup (`relay-update`: *still listed* ⇒ live, removed/deleted ⇒ hold, queue category ⇒
  pending approval), while terminal relay removals automatically delete matching delivered Discord cards
  before the mirror/proxy probe. Re-check messages count as relay liveness; a quiet relay reads
  `relay empty (relay alive (N re-check message(s)) but no new post …)`, not stale.
- **Edits** — a re-sent record (`revision` ≥ 2) is the newer message and supersedes the first
  for a post that has not been delivered yet; delivered posts are not re-posted.
- **Relay-only resolution.** Every relay record is treated as authoritative input, even if
  `record.json` could not be fetched or the inline body was truncated. `intake_base_data()`
  prevents reddit.com JSON, archive, and Redlib discovery/liveness lookups; media can still use
  the relay-carried URLs and the approved media proxy services. A truncated body uses the
  relayed portion if no complete body is available. Relay lifecycle handling consumes v2
  status updates directly; it does not infer removal from listing absence.
- **Rechecks and retries.** Devvit checks delivered posts at ~5 min / 30 min / 2 h / 6 h /
  24 h. Relay-path media readiness is retried on the next intake pass without the old engine's
  `PENDING_RECHECK_SECONDS` delay or `FRESH_HOLD_SECONDS` floor. Reddit's counts ride on the
  card stats line when available. The app carries no comments; there is no OP-comment feature.

Record: [`docs/history/ROUND_103.md`](history/ROUND_103.md),
[`docs/history/ROUND_104.md`](history/ROUND_104.md).

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
   `relay`; `monitor.log` has `INTAKE: relay ok — …`. Before step 5 the run logs
   `INTAKE-PAUSED: relay unconfigured …` and does not probe either engine.

### Switches (repo Variables, all optional)

| Variable | Default | Meaning |
| --- | --- | --- |
| `INTAKE_READER` | `primary` | `primary` = relay-only; unhealthy intake pauses delivery. `shadow` = old engine runs for comparison; `off` = explicitly use the retained old engine |
| `INTAKE_STALE_SECONDS` | `1800` | newest relay message (record or re-check) older than this ⇒ relay delivery pauses; no automatic old-engine fallback |
| `INTAKE_LOOKBACK_HOURS` | `48` | how far back the channel is read each run (≤ 8 pages of 100); Python intake retention is separate from Devvit's 24 h check schedule |

### Reader-side troubleshooting

| Log / summary | Meaning / action |
| --- | --- |
| `INTAKE-PAUSED: relay unconfigured` | secret or Variable missing in the prod repo (step 5); delivery paused, no old-engine fallback |
| `relay http_401 (bot token rejected)` | token wrong or reset — paste the current one |
| `relay http_403 (bot lacks View Channel / Read Message History…)` | step 3 |
| `relay http_404 (channel id unknown to this bot…)` | wrong id, or the bot was never invited (step 2) |
| `relay ok` but `0 record(s) for this engine` every run | records arrive with empty `content` ⇒ Message Content Intent off (step 1), or the `sub` names do not match `SUBREDDITS` |
| `INTAKE-PAUSED: relay stale` / `relay empty` / `relay error` | relay-only delivery is paused; check `npx devvit logs GamingExpressRelay`, its `relayEnabled` setting, target subreddits, and webhook. The old engine was not queried. |
| `relay empty` | no message in the lookback window at all — same causes as stale |
| `relay empty (N message(s) in the last 360 min but none is a relay record …)` | the bot sees the channel but no relay record: Message Content Intent off (step 1), wrong channel id, or the relay webhook (`intakeWebhook`) still points at the old channel — `npx devvit settings set intakeWebhook` |
| `relay empty (relay alive (N re-check message(s)) but no new post …)` | The relay is running, but no new post record is in the intake window. Delivery remains relay-only; no legacy discovery calls are made. |
| `[<id>] relay record.json unavailable (…) — inline record kept` | the CDN read of the complete record failed (expired link, outage); relay-carried fields remain authoritative, including the relayed body portion if it was truncated — no old-engine fill-in is probed |
| relay log `attachment refused (Nx) — sending content only` | Discord/Devvit rejected the multipart upload; records still arrive as plain content; after 3 in a row the attachment pauses for an hour (`attach:off`) — report it, nothing is lost |

## 10. Roadmap (each step its own PR, none started without an explicit go)

1. ~~Let the relay run clean for a few days~~ — waived by the owner on 2026-11-02; round 101
   shipped the reader with the old chain as the automatic fallback.
2. ~~**News-Express intake reader**~~ — done in round 101 (§9). Relay 0.0.6 candidates if the
   reader needs them: a heartbeat record (exact staleness), a long-body attachment
   (bodies above the message budget arrive truncated today).
3. ~~**Game-Express**~~ — delivered in round 102 as a `git am`-able patch, merged as
   [Game-Express #141](https://github.com/uesu/Game-Express/pull/141). `RedditClient._gather_listing()`
   asks the reader first; `u/<account>` listings are served from records whose `author` is
   that account (records carry the real subreddit in `sub`), subreddit listings per `sub`;
   the same two settings activate it in `uesu/8mqzv4k2n7c`.
4. ~~Post edits/removals as update records, long bodies, crosspost parent~~ — done in
   round 103 (relay 0.0.7, both readers, Game-Express patch refreshed). ~~Late approvals,
   per-post archive/redlib/reddit.com calls~~ — done in round 104 (relay 0.0.8, both
   readers): a relay-served post needs nothing but the relay and the vxreddit / embedez /
   embeddit proxies. Author follow-up comments: dropped by the owner (never shown on cards).
   Nothing open; the old chain stays as the fallback.

Dates that drive this: 2026-11-13 Reddit RSS retired (kills the engine's reddit.com feed
hosts and Game-Express's `REDDIT_FEED_TOKEN` path); 2027-01-12 unregistered access removed
(kills the redlib fleet); 2027-03 public Data API closed. Only the Developer Platform path
survives all three.
