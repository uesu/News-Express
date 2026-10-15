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

## Live results — completed

Run [38725292925](https://github.com/uesu/News-Express/actions/runs/38725292925),
commit `aede55b89bb526bad73c609e2bccb7a35ee8ea6a`, completed all **23 host jobs**.
The jobs spanned **2026-10-15 11:09:09–11:16:28 UTC**, or **19:09–19:16 Manila**.
The CLI retained the workflow's earlier display name, but its matrix jobs and
commit identify the expanded test. Each host had a separate GitHub-hosted Linux
job; exact cloud/region was not obtained. Do not infer that all hosts were tested
from one IP or one Azure region.

- **244 planned slots**, **214 attempted**, **30 skipped after 429**.
- **16 syntactic candidate responses**, all from Nitter; some are demonstrably
  stale. This is not 16 healthy/fresh sources or 16 successful deliveries.
- **No usable Redlib response among the 91 attempted Redlib requests**. Catsarch's
  17 remaining slots were not requested after its first 429.
- Both diagnostic suites passed in each job (**31 + 9 tests**). All three
  existing News suites passed locally before the diagnostic was pushed.
- The excluded hosts were not contacted. No primary-pair control was silently
  reintroduced. Freshness comparisons below use other mirrors in this run.

### Nitter results

“RSS / tried” counts HTTP-200 feeds with correctly scoped matching entries and
no detected error marker. It does **not** certify freshness. The denominator
excludes explicit rate-limit skips; eight accounts were planned for every host.

| Host | RSS / tried | Skipped | Observation |
|---|---:|---:|---|
| `nitter.meowing.monster` | 1 / 2 | 6 | TYPEII succeeded, then PomPom returned 429; stopped |
| `nitter.gravitywell.xyz` | 2 / 6 | 2 | TYPEII + PomPom succeeded; Wuwa/HNA/Ananta 404; Genshin 429; stopped |
| `nitter.kareem.one` | 4 / 8 | 0 | PomPom, Wuwa, HNA, Genshin succeeded; TYPEII/Ananta/HSR-global/ZZZ returned 404 |
| `nitter.perennialte.ch` | 7 / 8 | 0 | PomPom 502; **TYPEII and Wuwa feeds are weeks behind other mirrors** |
| `x.n0g.xyz` | 2 / 3 | 5 | TYPEII + PomPom succeeded; Wuwa 429; stopped |
| `shitter.thepixora.com` | 0 / 8 | 0 | All 403, JavaScript-required HTML |
| `nitter.xitter.cc` | 0 / 8 | 0 | All 403, JavaScript-required HTML |
| `nitter.netbub.com` | 0 / 8 | 0 | All 403, JavaScript-required HTML |
| `xcopy.uk` | 0 / 8 | 0 | All 403, JavaScript-required HTML |
| `tw.eir-nya.gay` | 0 / 8 | 0 | All 200 but Anubis/JavaScript HTML, not RSS |
| `nitter.tiekoetter.com` | 0 / 8 | 0 | All 200 but Anubis HTML, not RSS |
| `nitter.jaydenha.uk` | 0 / 8 | 0 | All 200 but HTML, not RSS; no recognized challenge marker |
| `nitter.click` | 0 / 8 | 0 | All 200 but plain text, not parsed feed XML |
| `nitter.net` | 0 / 8 | 0 | All 410 |
| `xcancel.com` | 0 / 8 | 0 | All 451; status alone does not establish why |
| `nitter.privacydev.net` | 0 / 8 | 0 | ConnectionRefusedError beneath URLError; no HTTP result |
| `x.yuuki.sh` | 0 / 8 | 0 | All 302 to `xcopy.uk`; cross-host redirects intentionally not followed |

`x.yuuki.sh` did not demonstrate an independent backend: its redirects pointed
to xcopy.uk, which was separately tested and returned 403 on all eight accounts.
Redirect refusal in the probe is a safety/attribution rule, not a claim that
production clients necessarily refuse that redirect.

#### Coverage of the five hosts that served some RSS

`RSS` = syntactic candidate, `stale` = candidate contradicted by a newer same-run
observation, `skip` = not requested after 429. In particular, an older publication
date alone is **not** called stale when no newer post is available in this run.

| Account | meowing | gravitywell | kareem | perennialte | x.n0g |
|---|---|---|---|---|---|
| `TYPEII_EN` | RSS | RSS | 404 | **stale** | RSS |
| `PomPom_HonkaiSR` | 429 | RSS | RSS | 502 | RSS |
| `Wuthering_Waves` | skip | 404 | RSS | **stale** | 429 |
| `HonkaiNA` | skip | 404 | RSS | RSS | skip |
| `Ananta_EN` | skip | 404 | 404 | RSS | skip |
| `GenshinImpact` | skip | 429 | RSS | RSS | skip |
| `honkaistarrail` | skip | skip | 404 | RSS | skip |
| `ZZZ_EN` | skip | skip | 404 | RSS | skip |

#### Concrete stale-feed evidence

| Account | perennialte newest matching post | Newer matching post from another mirror in this run |
|---|---|---|
| TYPEII | `2098622633554374759`, **2026-09-12 04:00:01 UTC** | `2110581431927967903`, **2026-10-15 04:00:00 UTC**, from meowing, gravitywell and x.n0g |
| Wuwa | `2100195290813026751`, **2026-09-16 12:09:11 UTC** | `2110672033671422277`, **2026-10-15 10:00:01 UTC**, from kareem |

Other useful observations, not freshness guarantees:

- Kareem and perennialte agreed on Genshin `2110581436130398263`
  (`2026-10-15 04:00:01 UTC`).
- Gravitywell, kareem and x.n0g agreed on PomPom `2109856657367007548`
  (`2026-10-13 04:00:01 UTC`).
- Perennialte returned HSR-global `2110641831411085772`
  (`2026-10-15 08:00:01 UTC`) and ZZZ `2110672098238824485`
  (`2026-10-15 10:00:17 UTC`), but there was no second successful current-run
  source for either in this restricted comparison.
- The newest matching HNA date on both kareem and perennialte was September 4;
  Ananta on perennialte was August 25. With no newer successful comparison here,
  those are **freshness-unverified**, not automatically stale or fresh.

### Redlib results

Six subreddits were planned per route. `Challenge` below means HTML with
recognized Anubis/JavaScript or GoAway markers and zero matching feed entries or
listing post IDs; none of these was a successful listing/feed response.

| Host | Engine RSS `/new/.rss` | Root HTML | Pristine `/new` HTML |
|---|---|---|---|
| `redlib.catsarch.com` | ZZZ 429 challenge; 5 skipped | All 6 skipped after 429 | All 6 skipped after 429 |
| `redlib.nadeko.net` | All 6: 418 challenge | All 6: 418 challenge | All 6: 418 challenge |
| `redlib.privadency.com` | All 6: 200 challenge | All 6: 200 challenge | All 6: 200 challenge |
| `safereddit.com` | All 6: 200 challenge | All 6: 200 challenge | 5: 200 challenge; HNA: 500 Anubis HTML |
| `red.artemislena.eu` | All 6: 200 challenge | All 6: 200 challenge | All 6: 200 challenge |
| `redlib.privacyredirect.com` | All 6: 200 challenge | 5: 200 challenge; HNA: 403 Anubis HTML | All 6: 200 challenge |

Catsarch's skipped HTML routes are **untested in this run**, not measured
failures. The other five public Redlib hosts were fully attempted across the
three routes and six communities. Working browser sessions or older historical
results may differ; this report describes plain unattended runner requests.

### Evidence and decision

Full per-job contexts, runner names, status/headers, exact request URLs, IDs,
dates and explicit skips are preserved in
[`diagnostics/other-public-instances-2026-10-15-run-38725292925.json`](diagnostics/other-public-instances-2026-10-15-run-38725292925.json).
The 244-slot inventory and request/skip counts were checked against the fixed
fleet and the user exclusions. Public-response notices were retrieved through
each job's check-run annotations API.

**Do not automatically promote or remove fleet members on this one matrix run.**

- Kareem demonstrated useful partial coverage, especially Wuwa/Genshin/PomPom,
  but it is not a universal fallback (four account routes returned 404).
- Meowing, gravitywell and x.n0g are capable of serving some real RSS from hosted
  runners; they also rate-limited this test. Successful responses disprove a
  blanket inability to serve these jobs, not rate limits on future jobs.
- Perennialte's 7/8 parseability is misleading as a ranking score: two feeds were
  substantially stale. It should not be promoted solely on that count.
- None of the public Redlib results supports adding/promoting a source or using
  root HTML as a workaround for pristine-listing gates.
- Miningtcup remains **not tested with authentication**, not failed. A separately
  scoped authenticated test would be needed for its real production behavior;
  no token values should ever be pasted into chat.
- No excluded-host fresh control, per-post/media test, multi-region repetition
  or complete monitor-parity test was performed. Keep those limits attached to
  any future fleet proposal. The first four operator-directed Nitter seats and
  all production fleets remain unchanged.

No production fleet, monitor, main branch, secret or Variable is changed by this
work. No PR or deployment is requested or performed. Only diagnostic files and
reports are committed/pushed to `arena/c45edf9b-news-express`; Kite files remain
untouched. Documentation-only pushes do not trigger further endpoint requests.
