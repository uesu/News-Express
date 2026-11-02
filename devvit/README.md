# devvit/ — Reddit Developer Platform apps (not part of the engine)

Apps in this folder run **on Reddit's servers**, not in the GitHub Actions monitors.
They are kept in News-Express only as the source of truth; `sync_prod.yml` copies
`testing area/**` and `tests/**` only, so nothing here is ever deployed to the
production repositories, and nothing here changes engine behaviour.

| App | Reddit slug | Purpose | Status |
| --- | --- | --- | --- |
| [`gaming-express/`](gaming-express/readme.md) | `gaming-express` | Polls the public `/new` listings of the tracked subreddits (six News-Express leak subs + six Game-Express official subs) and the three verified, active publisher accounts (`u/genshinimpact`, `u/HonkaiStarRail`, `u/HonkaiNexusAnima`), and relays each new post once as a JSON record to a private Discord intake channel — the replacement for Reddit RSS discovery after Reddit retires RSS on 2026-11-13 (see `docs/history/ROUND_99_investigation_reddit_survival.md`). | live on `r/GamingExpressRelay` (Reddit 0.0.4 = 0.0.5 code) — **News-Express reads the channel since round 101** (primary listing, old chain as fallback; `docs/DEVVIT_SETUP.md` §9); Game-Express does not read it yet |

Operator documentation (deploy/update from a zip, settings, expected log lines,
troubleshooting, roadmap) lives in [`docs/DEVVIT_SETUP.md`](../docs/DEVVIT_SETUP.md). The
app's own `readme.md` is kept short and generic because Reddit displays it on the app's
Directory page.

Each app is a self-contained Node project: `cd devvit/<app> && npm ci && npm test`.
The Devvit CLI steps (`devvit login` / `upload` / `settings set` / `install`) run on the
owner's machine against their Reddit account; see `docs/DEVVIT_SETUP.md`.
