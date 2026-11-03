# Gaming Express

Relays new posts from a configurable set of gaming subreddits and official publisher
accounts to a private Discord intake channel — one compact record per post, delivered once,
followed up with removal, deletion, edit and approval notices during the post's first day.

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
- **Minimal state.** Redis holds post identifiers (short-lived de-duplication and re-check
  markers) and poll counters. No post content, no user data.
- **One external host.** Every delivery is a `POST` to the developer's own Discord webhook
  on `discord.com`; the webhook URL is an encrypted app setting.

## How it works

1. **Poll.** A scheduler task runs every few minutes and reads the newest public posts of
   each configured subreddit and each configured account. Profile posts are labelled with
   the subreddit they were actually posted in.
2. **Bootstrap.** The first poll after installation — and the first poll for every target
   added later — only *remembers* what is already there. Nothing historical is sent, so a new
   target never produces a burst of old posts.
3. **Deliver.** New posts are sent oldest-first, once per post id, a bounded number per poll;
   a longer backlog simply continues on the next poll. Each delivery is one Discord message:
   a compact record as the content and the complete record (untruncated body, every media
   URL, video renditions, crosspost parent) as a small JSON attachment.
4. **Re-check.** Each delivered post is looked at again a few times during its first day.
   The first look always reports back; the later looks report only a change — removal,
   deletion, lock, spoiler/NSFW flag or edit. An edited post, and a post that was removed and
   later approved, are re-sent as a new revision. Score and comment counts are carried but
   never trigger a message.
5. **Pause.** With `relayEnabled` off the app keeps polling and remembering, and sends
   nothing — switching it back on resumes without a backlog.

### Delivery semantics

- Mentions are disabled on every message — a record can never ping anyone.
- Rate limiting is honoured; transient Discord or network errors leave the post for a later
  poll, with a bounded number of attempts; permanent errors are recorded and not retried.
- If the attachment is refused, the same record goes out as plain content immediately, so no
  post is ever lost to the attachment.
- Posts are de-duplicated per id across polls, upgrades and restarts. A post the targets have
  in common (a crosspost, a post that appears both on a subreddit and on its author's
  profile) is sent once.
- The record format is versioned and additive; the reader on the Discord side ignores
  messages it does not recognise, so other bots may share the channel.

## Setup

1. In Discord, create a private channel for the intake and one webhook on it. Keep the
   webhook URL out of files, commits and public channels.
2. Build and test with `npm ci` and `npm test` (type check, lint, unit tests, bundle).
3. Log in with the Devvit CLI, upload, set `intakeWebhook` with `devvit settings set`, adjust
   the target lists if the defaults do not fit, and install the app on the private subreddit
   that hosts it. Settings are global and persist across versions; the CLI never prints
   secret values.
4. Verify with the moderator menu on that subreddit (**Status**, **Poll now**) or with
   `devvit logs`; every poll logs one summary line.

Later versions are switched in with the same upload + install step — one version runs at a
time, settings and memory carry over.

## Settings

| Setting | Type | Meaning |
| --- | --- | --- |
| `intakeWebhook` | secret | `https://discord.com/api/webhooks/…` of the private intake channel. Only Discord webhook URLs are accepted; the app refuses to relay anywhere else. |
| `subreddits` | string | Comma-separated subreddit names to poll, without `r/`. The primary target list. |
| `officialUsers` | string, optional | Comma-separated publisher accounts to poll, without `u/`, as a second path — their home subreddits are polled anyway, this catches posts they make elsewhere and profile posts. Only accounts that actually post belong here; a publisher without an active account is covered by its subreddit through `flair` (`Official News`, `Official Media`, …) and `distinguished`. May be empty. |
| `relayEnabled` | boolean | `false` pauses delivery: posts are still polled and remembered, nothing is sent. |

## Inbox contract

Every message in the intake channel is one of two shapes, both plain JSON in the message
content, both versioned so a reader can tell them apart and skip anything else:

- **Record** — one new post: identity (`id`, `sub`, `title`, `permalink`, `url`, `created`),
  classification inputs (`author`, `flair`, `distinguished`), flags (`spoiler`, `nsfw`,
  `removed`, crosspost parent), counters, the body and media list trimmed to the message
  budget with explicit truncation markers, and a revision number when a post is re-sent.
  The attachment carries the same record untrimmed.
- **Update** — the batched result of a re-check round: per post, its age, the look that
  produced it, and the current removal / deletion / edit / lock / spoiler / NSFW state.

Field names are stable; new fields are only ever added. The precise schema is shared with
the reader it was built for and is not a public interface.

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
- `redis` — post identifiers, re-check markers and poll counters; everything expires on its
  own within days.
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

Pinned Devvit SDK and CLI, TypeScript, Biome, esbuild, Node 24+. `npm test` runs the type
check, the linter, the unit tests (record trimming, de-duplication, re-check scheduling,
update batching, webhook validation, status classification) and the build.

## Current installation

One installation, on a private subreddit created for it, delivering to one private Discord
channel. The app is unlisted and is not accepting installation requests.
