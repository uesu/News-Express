# Other public instances — live review, 2026-10-15

## Scope and source snapshots

User requested the other instances, explicitly excluding the working
`nitter.cf` / `xitter.cf` pair and the already-tested Eddrit/Freedit hosts.
This diagnostic does not request those hosts, including as controls.

Current main-branch fleet definitions were retrieved before constructing the
fixed probe matrix:

| Repository | Commit | Fleet source |
|---|---|---|
| News-Express | `83a701ab4c8644a9b1ae5e61472dafdf8175b99a` | `testing area/twitter_v3.py` |
| Reddit production `7jkxmy9nvbc` | `a98d56fd7a89de16813cd619d1ccab97cfb55f7d` | same path |
| Twitter production `wvkhabh2s22` | `905e4c96f52be88bbe895d891fba1bead3024cb5` | same path |
| Game-Express | `e9dc3a68d59e0ab0f91595c7678802fe4e7b89ce` | `gamexpress/config.py` |

The three News/production fleets match (12 entries); Game has 21. The six public
Redlib hosts come from the previously audited News snapshot's shared
`REDDIT_RSS_INSTANCES`; News main is unchanged since that audit.

### Included

- **17 public Nitter hosts**, the deduplicated fleet union after exclusions:
  `nitter.meowing.monster`, `nitter.gravitywell.xyz`, `tw.eir-nya.gay`,
  `shitter.thepixora.com`, `nitter.kareem.one`, `xcopy.uk`, `nitter.netbub.com`,
  `nitter.jaydenha.uk`, `nitter.click`, `nitter.tiekoetter.com`, `nitter.xitter.cc`,
  `nitter.perennialte.ch`, `nitter.privacydev.net`, `nitter.net`, `xcancel.com`,
  `x.yuuki.sh`, `x.n0g.xyz`.
- **Eight Nitter account paths per host:** `TYPEII_EN`, `PomPom_HonkaiSR`,
  `Wuthering_Waves`, `HonkaiNA`, `Ananta_EN`, `GenshinImpact`, `honkaistarrail`,
  `ZZZ_EN`. The parser scopes results to each requested account (retweets of
  other accounts do not count as matching author-path entries).
- **Six public Redlib hosts:** `redlib.catsarch.com`, `redlib.nadeko.net`,
  `redlib.privadency.com`, `safereddit.com`, `red.artemislena.eu`,
  `redlib.privacyredirect.com`.
- **Six game subreddits per Redlib host**, matching the prior six-game audit:
  `Zenlesszonezeroleaks_`, `Genshin_Impact_Leaks`, `HonkaiStarRail_leaks`,
  `WutheringWavesLeaks`, `HonkaiNexusAnimaLeaks`, `AnantaLeaks`.
- Three independent Redlib routes: engine RSS `/r/<sub>/new/.rss`, root HTML
  `/r/<sub>`, and pristine HTML `/r/<sub>/new?limit=100&_fresh=<milliseconds>`
  with `Cache-Control: no-cache, no-store` / `Pragma: no-cache`.

### Not tested

- The user's excluded hosts: nitter.cf, xitter.cf, Eddrit, Nitter Freedit and
  Redlib Freedit. They are not re-probed as controls.
- **nitter.miningtcup.me and redlib.miningtcup.me:** token-gated, intentionally
  excluded from this no-secrets public audit. An anonymous rejection would not
  establish failure with the production token. No authenticated verdict is made.
- Native `www.reddit.com` / `old.reddit.com`: not public mirror instances in
  this comparison. The prior run already obtained a working native RSS control.
- Per-post RSS, media endpoints, Discord rendering and Game's unrelated source
  APIs. No claim of full end-to-end monitor delivery is made.

## Execution and limits

The existing branch-scoped diagnostic workflow is repurposed for this matrix;
it does **not** also run the earlier Freedit/Eddrit suites. One hosted job owns
one host, at most four jobs run concurrently, and each job is capped at ten
minutes. All jobs run both offline diagnostic suites first (31 + 9 tests).
The original three News regression suites also passed locally before publishing.

Each endpoint is requested at most once, with five-second spacing per host,
a 20-second total child-process deadline, a 12-second socket timeout and a
2 MiB body cap. Only fixed reviewed HTTPS URLs are allowed; redirects must stay
on the same host. No credentials, cookie jars, ambient proxies, browser challenge
execution, retries, monitor imports or Discord calls are used.

There are **244 planned endpoint slots** (17 × 8 Nitter + 6 × 6 × 3 Redlib).
A **429 stops that host for the entire remainder of its job**, including later
HTML route steps. Those remaining slots are explicitly recorded as
`not_requested_after_429` with `request_attempted: false`; they are not failures
observed on those accounts/routes. No attempt is made to evade the rate limit.

Results are parsed locally on the runner and emitted as escaped public JSON
check annotations (at most nine per step). The report collector uses GitHub's
Checks API; no custom write token or signed log download is required. A green
job means the diagnostic completed, not that an instance passed.

A candidate response requires HTTP 200 with matching scoped feed entries or
HTML post links, no detected error marker, and HTML Content-Type for listings.
This does not certify freshness, independent backend diversity, runtime-parser
parity, media support or permanent Azure/datacenter availability. Error-marker
matching is conservative and can flag a post that mentions the same words.
Check returned IDs/dates and account-specific gaps before any promotion. No
freshness parity claim will be made against the excluded control hosts.

## Live results

Pending the branch-triggered run at this revision. The result file will retain
per-job runner names, timestamps, exact URLs and per-account/subreddit outcomes.
Region/cloud will not be inferred from the `ubuntu-latest` label.

No production fleet, monitor, main branch, secret or Variable is changed by this
work. No PR or deployment is requested or performed. Only diagnostic files and
reports are committed/pushed to `arena/c45edf9b-news-express`; Kite files remain
untouched. Documentation-only pushes do not trigger further endpoint requests.
