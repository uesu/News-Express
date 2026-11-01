# Gaming Express

A small personal relay. It reads the public `/new` listings of a configurable set of
gaming subreddits and official publisher accounts and forwards each new post, once, as
one compact JSON message to a private Discord channel owned by the developer.

- Private, single-installation app for the developer's own use. Not intended for
  publication or for installation on other communities.
- Reads only public post listings through the Reddit Developer Platform API. It never
  posts, comments, votes or messages on Reddit, and reads nothing private.
- Stores only post identifiers (7-day de-duplication markers) and poll counters in Redis.
- Contacts a single external host, `discord.com`, to deliver the relayed records to the
  developer's own webhook (stored as an encrypted app setting).

## Settings

| Setting | Meaning |
| --- | --- |
| `intakeWebhook` (secret) | `https://discord.com/api/webhooks/…` of the private channel |
| `subreddits` | comma-separated subreddit names to poll |
| `officialUsers` | comma-separated publisher account names to poll (`u/…` submissions) |
| `relayEnabled` | `false` pauses delivery (posts are still remembered, nothing is sent) |

## Fetch Domains

- `discord.com` — `POST` of each relayed record to the developer's own webhook URL.
  No other hosts are contacted.

## Commands

- `npm test` — typecheck, lint, unit tests, build
- `npm run upload` — clean, build, `devvit upload`
