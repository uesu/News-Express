# devvit/ — Reddit Developer Platform apps (not part of the engine)

Apps in this folder run **on Reddit's servers**, not in the GitHub Actions monitors.
They are kept in News-Express only as the source of truth; `sync_prod.yml` copies
`testing area/**` and `tests/**` only, so nothing here is ever deployed to the
production repositories, and nothing here changes engine behaviour.

| App | Reddit slug | Purpose | Status |
| --- | --- | --- | --- |
| [`gaming-express/`](gaming-express/readme.md) | `gaming-express` | Polls the public `/new` listings of the six tracked subreddits and relays each new post as a JSON record to a private Discord intake channel — the planned replacement for Reddit RSS discovery after Reddit retires RSS on 2026-11-13 (see `docs/history/ROUND_99_investigation_reddit_survival.md`). | shadow mode — the engine does not read the intake channel yet |

Each app is a self-contained Node project: `cd devvit/<app> && npm ci && npm test`.
The Devvit CLI steps (`devvit login` / `upload` / `settings set` / `install`) run on the
owner's machine against their Reddit account; see the app readme.
