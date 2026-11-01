# Gaming Express — Reddit → Discord intake relay

A [Devvit](https://developers.reddit.com/) app that polls the **public** new-post
listings of a fixed set of gaming-leak subreddits and forwards each new post, once, as
one compact JSON message to a **private Discord intake channel**. A separate bot
(News-Express) reads that channel and renders the public news card.

The app is installed on a private subreddit owned by the developer. It never posts,
comments, votes, or reads anything on Reddit beyond the public `/new` listings of the
configured subreddits. It does not scrape Reddit, does not fetch private
conversations, and stores only post IDs (7-day de-dup markers) in Redis.

Replaces Reddit RSS, which Reddit retires on 2026-11-13.

## How it works

```
Reddit scheduler (cron */2 * * * *)
   │  POST /internal/scheduler/poll
   ▼
this app (hosted by Reddit)
   │  1. read settings: intakeWebhook (secret), subreddits, relayEnabled
   │  2. reddit.getNewPosts({subredditName}) for each subreddit (6 calls)
   │  3. first poll per subreddit = bootstrap: remember IDs, send nothing
   │  4. skip IDs already in Redis (seen:<id>, 7-day TTL)
   │  5. oldest-first, max 10 per poll: POST to the Discord webhook
   ▼
#reddit-intake (private): one ```json block per post
```

| Outcome | What the app does |
| --- | --- |
| Discord 200/204 | `seen:<id>` set for 7 days |
| Discord 429 | waits `Retry-After` (≤ 5 s) once, then retries next poll |
| Discord 5xx / network error | retries next poll; gives up after 3 failures |
| Discord 400/401/403/404 | drops the post, logs the body (webhook deleted or invalid) |
| `relayEnabled` off | polls and marks posts as seen, sends nothing (no burst when re-enabled) |
| Subreddit fetch error | that subreddit is skipped this poll; the others continue |

Messages are sent with `allowed_mentions: {parse: []}`, so a post title can never ping a
role or `@everyone`. Only `https://discord.com/api/webhooks/…` URLs are accepted.

## Intake record (v1)

The message content is a single fenced JSON block. Field order and names are stable.

```json
{"v":1,"id":"1xkgd9m","sub":"Genshin_Impact_Leaks","title":"…","permalink":"/r/…/comments/1xkgd9m/…/",
 "url":"https://…","created":1793400000,"author":"…","flair":"Megathread","spoiler":false,"nsfw":false,
 "score":1,"comments":0,"removed":null,"xpost":null,"media":["https://i.redd.it/…"],
 "body":"selftext markdown…","bodyTruncated":false}
```

`body` is trimmed (and `bodyTruncated` set) when the message would exceed Discord's
2000-character limit; identity fields are never trimmed. `score`/`comments` are the
values at poll time (usually 1/0 for a post that is seconds old).

## Setup

1. **Discord:** create a private channel (e.g. `#reddit-intake`) and one webhook on it.
   Copy the URL. Never put it in a file or a public channel.
2. **Reddit:** create a private subreddit you own (install target only; nothing is
   posted there). Under 200 members a private upload can be installed without publishing.
3. **This folder:** `npm ci` → `npm test` (types, lint, unit tests, build).
4. `npx devvit login` (opens the browser; links the CLI to your Reddit account).
5. `npx devvit upload` — uploads a private version and submits the `discord.com` fetch
   domain for review (globally allow-listed; normally confirmed within 1–2 business days).
6. `npx devvit settings set intakeWebhook` — paste the webhook URL at the prompt.
   Optionally `npx devvit settings set subreddits` to change the list.
7. `npx devvit install <your-private-sub>` — the cron task starts on install.
8. Watch: `npx devvit logs <your-private-sub>`. The first poll bootstraps (remembers the
   current 25 posts per subreddit, sends nothing); from the second poll on, new posts
   appear in `#reddit-intake` within ~2 minutes.
9. Subreddit menu (`…` on your private sub) → **[Gaming Express] Poll now** /
   **[Gaming Express] Status** for a manual run and a quick health line.

To pause without uninstalling: `npx devvit settings set relayEnabled` → `false`.

## Fetch Domains

The following domains are requested for this app:

- `discord.com` — used only to `POST` each relayed post to the developer's own Discord
  webhook URL stored in the encrypted `intakeWebhook` setting. No other hosts are
  contacted. (Globally allow-listed per the Devvit HTTP Fetch policy.)

## Data handling

- Stored in Redis: `seen:<postId>` (7-day TTL), `boot:<subreddit>`, `fail:<postId>`,
  `last:poll`, `total:sent`. No user data beyond the public author name inside the
  relayed record.
- Relayed records live in the developer's private Discord channel. When the consumer
  bot detects a post removal it deletes the public card; the intake record can be
  purged from the channel by the same bot (planned) — or set the channel to auto-delete.
- Terms of Service and Privacy Policy: see the News-Express repository
  (`TERMS_OF_SERVICE.md`, `PRIVACY_POLICY.md`).

## Known limitations

- Devvit secrets are global, so one webhook serves every installation of this app.
- Posts older than the newest 25 per subreddit at poll time are not seen (irrelevant at a
  2-minute cadence on these subreddits).
- `media` lists direct image/video URLs only when Reddit's listing exposes them;
  galleries that are still processing may arrive with an empty list — the consumer
  already handles that case (media-wait).
- `intakeWebhook` is `isSecret: true` and therefore has **no** `defaultValue` — Reddit's
  config schema forbids the combination (`devvit upload` fails with
  `settings.global.intakeWebhook is not exactly one from …`). Until the secret is set the
  poll runs in polling-only mode and reports `intakeWebhook is empty …` in `devvit logs`.
  A unit test guards this rule.

## Commands

- `npm test` — typecheck, lint, unit tests, build
- `npm run upload` — clean, build, `devvit upload`
- `npm run playtest [r/sub]` — watch, build, upload and install on a test subreddit
