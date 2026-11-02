# Gaming Express

A small personal relay. It reads the public `/new` listings of a configurable set of
gaming subreddits and official publisher accounts and forwards each new post, once, as
one compact JSON message (with the complete record attached as `record.json`) to a private
Discord channel owned by the developer. It looks at each forwarded post again a few times
during its first day and reports removals, deletions, edits and approvals the same way;
for posts by the configured publisher accounts (or distinguished / "official"-flaired
posts) it also forwards the author's own follow-up comments.

- Private, single-installation app for the developer's own use. Not intended for
  publication or for installation on other communities.
- Reads only public post listings and public comments through the Reddit Developer
  Platform API. It never posts, comments, votes or messages on Reddit, and reads nothing
  private.
- Stores only post identifiers (7-day de-duplication and re-check markers, content
  fingerprints) and poll counters in Redis.
- Contacts a single external host, `discord.com`, to deliver the relayed records to the
  developer's own webhook (stored as an encrypted app setting).

## Settings

| Setting | Meaning |
| --- | --- |
| `intakeWebhook` (secret) | `https://discord.com/api/webhooks/…` of the private channel |
| `subreddits` | comma-separated subreddit names to poll |
| `officialUsers` | optional; comma-separated verified publisher accounts to poll (`u/…` submissions) as a second path — their subreddits are polled anyway. Publishers without an active account are covered by their subreddit: each record carries `flair` (e.g. `Official News`, `Official Media`) and `distinguished` (`moderator`/`admin`/`null`). May be empty |
| `relayEnabled` | `false` pauses delivery (posts are still remembered, nothing is sent) |

## Fetch Domains

- `discord.com` — `POST` of each relayed record to the developer's own webhook URL.
  No other hosts are contacted.

## Commands

- `npm test` — typecheck, lint, unit tests, build
- `npm run upload` — clean, build, `devvit upload`
