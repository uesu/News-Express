# Gaming Express

Relays new posts from a configurable set of gaming subreddits and official publisher
accounts to a private Discord intake channel — one compact JSON record per post, delivered
once, followed up with removal, deletion, edit and approval notices during the post's first
day.

Gaming Express is the Reddit intake of a Discord server that publishes news from the official
accounts of a handful of games. The publisher posts it exists for are the ones a community
expects to see quickly and exactly once: a version preview or *Special Program* broadcast
announcement from `u/genshinimpact` or `u/HonkaiStarRail`, a maintenance notice from
`u/HonkaiNexusAnima`, a redemption-code post flaired `Official News` on `r/WutheringWaves`,
a `distinguished` moderator announcement on `r/ZZZ_Official` or `r/AnantaOfficial`. The app
forwards every new post of its targets with the fields needed to classify it (`author`,
`flair`, `distinguished`); the decision of what is official, and what is posted to which
channel, stays with the reader on the Discord side.

- **Private, single-installation app.** Installed on one private subreddit owned by the
  developer. Not intended for publication or for installation on other communities.
- **Read-only.** It reads public post listings through the Reddit Developer Platform API.
  It never submits, comments, votes, flairs, messages or moderates anything on Reddit, and
  it reads nothing private.
- **Minimal state.** Redis holds post identifiers (7-day de-duplication and re-check markers)
  and poll counters. No post content, no user data.
- **One external host.** Every delivery is a `POST` to the developer's own Discord webhook
  on `discord.com`; the webhook URL is an encrypted app setting.

## How it works

1. **Poll.** A scheduler task runs every five minutes (`*/5 * * * *`). For each configured
   subreddit it reads the newest 25 posts of `/new`; for each configured account it reads
   the account's newest 25 submissions. Profile posts are labelled with the subreddit they
   were actually posted in (`u_<name>` for a profile-page post), which is what readers key on.
2. **Bootstrap.** The first poll after installation — and the first poll for every target
   added later — only *remembers* what is already there. Nothing historical is sent, so a new
   target never produces a burst of old posts.
3. **Deliver.** New posts are sent oldest-first, once per post id, at most 15 per poll; a
   longer backlog simply continues on the next poll. Each delivery is one Discord message
   whose content is the fenced JSON record (trimmed to a 1,900-character budget — the body
   is shortened first, then the media list) and whose attachment `record.json` is the
   complete record: untruncated body, every media URL, video renditions and, for a crosspost,
   the parent post as a nested record.
4. **Re-check.** Each delivered post is looked at again five times — about 5 minutes,
   30 minutes, 2 hours, 6 hours and 24 hours after delivery. The first look is always
   reported (it confirms the post is still live, or that an automated removal caught it);
   the later looks report only a change — removal, deletion, lock, spoiler/NSFW flag or edit
   — as one batched *update* message. An edited post, and a post that was removed and later
   approved, are additionally re-sent as a new revision of the record. Score and comment
   counts are carried in every message but never trigger one.
5. **Pause.** With `relayEnabled` off the app keeps polling and remembering, and sends
   nothing — switching it back on resumes without a backlog.

### Delivery semantics

- Discord webhook `POST … ?wait=true` with `allowed_mentions: { "parse": [] }` — a record can
  never ping anyone.
- `429` honours `Retry-After` once (capped at 5 s) inside the same poll. `5xx` and network
  errors leave the post for the next poll; after three failed polls it is marked `gave-up`
  and not retried. Any other `4xx` is a permanent error: the post is marked `dropped`.
- If the multipart upload of `record.json` is refused, the same record goes out as plain
  content immediately, so no post is ever lost to the attachment; three refusals in a row
  pause attachments for one hour.
- Posts are de-duplicated for seven days per id (`seen:<id>`), across upgrades and
  restarts. Re-check state lives in the same keyspace with the same expiry.
- Posts the targets have in common (a crosspost, a post that appears both on a subreddit and
  on its author's profile) are sent once.

## Setup

1. In Discord, create a private channel for the intake and one webhook on it. Copy the
   webhook URL; never paste it into a file, a commit or a public channel. Other bots may
   write to the same channel — readers skip every message that is not a relay record.
2. Build and test the app:

   ```
   npm ci
   npm test
   ```

   `npm test` runs the type check, the linter, the unit tests and the esbuild bundle and must
   end with `fail 0`.
3. Log in and upload (the copy-paste login works from any terminal, including Windows
   Command Prompt):

   ```
   npx devvit login --copy-paste
   npx devvit whoami
   npx devvit upload --copy-paste
   ```

   `upload` assigns the next app version on the server and prints the link to this listing.
4. Set the secret and, if the defaults do not fit, the target lists. Settings are global and
   persist across versions; the CLI shows keys and labels, never values:

   ```
   npx devvit settings set intakeWebhook
   npx devvit settings set subreddits
   npx devvit settings set officialUsers
   npx devvit settings set relayEnabled
   npx devvit settings list
   ```
5. Install the app on the private subreddit that hosts it, and keep it unlisted:

   ```
   npx devvit install <your_private_subreddit>
   ```

   The first scheduled poll after the install is the bootstrap poll; the first records
   arrive on the tick after it. Later uploads are switched in with the same `install` command (or
   the **Update** button on the installation page) — one version runs at a time.
6. Verify with the moderator menu on that subreddit — **[Gaming Express] Status** shows the
   last poll time, counters and configuration; **[Gaming Express] Poll now** runs one poll
   immediately and reports the result — or with `npx devvit logs <your_private_subreddit>`.
   Every poll logs one line:
   `poll: N subs, N users, N fetched, N sent, N seen, N failed, N bootstrapped; recheck N looked, N update msg, N re-sent`.

## Settings

| Setting | Type | Meaning |
| --- | --- | --- |
| `intakeWebhook` | secret | `https://discord.com/api/webhooks/…` of the private intake channel. Only Discord webhook URLs are accepted; the app refuses to relay anywhere else. |
| `subreddits` | string | Comma-separated subreddit names to poll, without `r/`. The primary target list. |
| `officialUsers` | string, optional | Comma-separated publisher accounts to poll, without `u/`, as a second path — their home subreddits are polled anyway, this catches posts they make elsewhere and profile posts. Only accounts that actually post belong here; a publisher without an active account (or a dormant one) is covered by its subreddit through `flair` (`Official News`, `Official Media`, …) and `distinguished`. May be empty. |
| `relayEnabled` | boolean | `false` pauses delivery: posts are still polled and remembered, nothing is sent. `0`, `no`, `off` and `paused` are understood as well. |

## Inbox contract

Every message in the intake channel is one of two shapes. Both are a single fenced JSON
block as the message content; the fields are stable and additive — readers ignore keys they
do not know.

**Record** (`v: 1`) — one new post, plus the `record.json` attachment when `full` is true:

```json
{
  "v": 1,
  "id": "1xuc001",
  "sub": "Genshin_Impact",
  "title": "Version 7.3 Special Program Preview",
  "permalink": "/r/Genshin_Impact/comments/1xuc001/version_73_special_program_preview/",
  "url": "https://i.redd.it/example.jpeg",
  "created": 1793583000,
  "author": "genshinimpact",
  "flair": "Official Media",
  "distinguished": null,
  "spoiler": false,
  "nsfw": false,
  "score": 1240,
  "comments": 187,
  "removed": null,
  "xpost": null,
  "media": ["https://i.redd.it/example.jpeg"],
  "body": "Dear Travelers, the Version 7.3 Special Program will premiere on …",
  "bodyTruncated": false,
  "full": true,
  "mediaTruncated": false,
  "edited": false,
  "revision": 1,
  "xpostPermalink": null,
  "video": null
}
```

| Field | Meaning |
| --- | --- |
| `id` | Reddit post id without the `t3_` prefix |
| `sub` | subreddit the post was made in (`u_<name>` for a profile post) |
| `author`, `flair`, `distinguished` | the classification inputs: author name, link flair text or `null`, `"moderator"` / `"admin"` / `null` |
| `created` | unix seconds |
| `removed` | Reddit's removal category at relay time, `null` when live |
| `xpost`, `xpostPermalink` | crosspost parent (`t3_…`) and its permalink, or `null` |
| `media` | image and video URLs, oldest-first gallery order (`mediaTruncated` when cut to the budget) |
| `body`, `bodyTruncated` | selftext markdown; `bodyTruncated` when cut to the budget |
| `full` | `true` when `record.json` is attached — it holds the untruncated body, the complete media list, `video` renditions and `parent` (the crosspost parent as a nested record) |
| `video` | `{ "fallback": "<mp4>", "hls": "<m3u8>", "gif": false }` for a Reddit-hosted video, else `null` |
| `edited`, `revision`, `resent` | `revision` ≥ 2 marks a re-sent record (readers keep the newest message per id); `resent` says why: `edited`, `approved`, or both joined by `+` |

**Update** (`v: 2`, `kind: "update"`) — the batched result of a re-check round. Readers
written for `v: 1` only ignore it:

```json
{
  "v": 2,
  "kind": "update",
  "at": 1793584800,
  "posts": [
    {
      "id": "1xuc002",
      "sub": "HonkaiStarRail",
      "age": 1812,
      "stage": 2,
      "removed": "moderator",
      "deleted": false,
      "edited": false,
      "spoiler": false,
      "nsfw": false,
      "locked": false,
      "score": 15,
      "comments": 3
    }
  ]
}
```

`stage` is the re-check that produced the item (1 ≈ 5 min … 5 = 24 h), `age` the post's age in
seconds at that moment. A post that answers `404` on re-check is reported as `deleted: true`.

## Moderator menu

Both actions appear in the subreddit menu for moderators of the subreddit the app is
installed on, and nowhere else.

- **[Gaming Express] Poll now** — run one poll immediately and show the result line.
- **[Gaming Express] Status** — last poll time, counters and current configuration.

## Fetch Domains

- `discord.com` — `POST` of each relayed record and each update message to the developer's
  own webhook URL. No other hosts are contacted.

## Permissions

- `http` — outbound fetch, limited to `discord.com` (see Fetch Domains).
- `redis` — post identifiers, re-check markers and poll counters; everything expires within
  seven days.
- `reddit` — read access to public post listings and individual posts. No write scopes are
  used.

## Sources

- Devvit — [devvit.json configuration](https://developers.reddit.com/docs/capabilities/devvit-web/devvit_web_configuration)
- Devvit — [Scheduler](https://developers.reddit.com/docs/capabilities/server/scheduler)
- Devvit — [Settings and secrets](https://developers.reddit.com/docs/capabilities/server/settings-and-secrets)
- Devvit — [HTTP Fetch](https://developers.reddit.com/docs/capabilities/server/http-fetch) and [HTTP Fetch policy](https://developers.reddit.com/docs/capabilities/server/http-fetch-policy)
- Devvit — [Redis](https://developers.reddit.com/docs/capabilities/server/redis)
- Devvit — [Triggers](https://developers.reddit.com/docs/capabilities/server/triggers)
- Devvit — [Menu actions](https://developers.reddit.com/docs/capabilities/client/menu-actions)
- Devvit — [CLI reference](https://developers.reddit.com/docs/guides/tools/devvit_cli)
- Devvit — [Rules](https://developers.reddit.com/docs/devvit_rules)
- Discord — [Execute Webhook](https://discord.com/developers/docs/resources/webhook#execute-webhook)

## Toolchain

Pinned to `devvit` 0.15.1 / `@devvit/web` 0.15.1, TypeScript 7, Biome 2, esbuild, Node 24+.

- `npm test` — type check, lint, unit tests (25 cases covering record trimming, budget and
  media handling, de-duplication, re-check scheduling, update batching, webhook URL
  validation and status classification), build
- `npm run upload` — clean, build, `devvit upload`
- `npm run playtest` — `devvit playtest` against the development subreddit

## Current installation

One installation, on a private subreddit created for it, delivering to one private Discord
channel. The app is unlisted and is not accepting installation requests.
