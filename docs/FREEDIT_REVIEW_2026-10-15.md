# Freedit review — 2026-10-15

**Later fleet-wide follow-up:** see [OTHER_INSTANCES_LIVE_REVIEW_2026-10-15.md](OTHER_INSTANCES_LIVE_REVIEW_2026-10-15.md) for the remaining public Nitter/Redlib hosts. The shared diagnostic workflow now runs that matrix; the results below remain the historical record of this earlier run.

**Subsequent live test:** the exact Freedit subreddit-root URL and Eddrit across
all six game communities were tested in a second run. See
[EDDRIT_LIVE_REVIEW_2026-10-15.md](EDDRIT_LIVE_REVIEW_2026-10-15.md) for those
results and the expanded diagnostic's current workflow/suite configuration.
The first-run results and configuration below are retained as that run's record.

## Live-test result — completed

**Freedit did not supply usable RSS or listing HTML in the live GitHub-hosted
runner test. Do not add Redlib Freedit or promote Nitter Freedit on this evidence.**

- Run: [38722163102](https://github.com/uesu/News-Express/actions/runs/38722163102).
- Tested commit: `c32b8ac726018a7b231add5dbb5a9828f147f105` on
  `arena/c45edf9b-news-express`; event: diagnostic-only branch push.
- Requests: **2026-10-15 10:42:30–10:42:46 UTC** (18:42 in Manila).
- Runner: GitHub-hosted Linux/X64, `ubuntu-latest`,
  `GitHub Actions 1000020311`; job `116379108444`, completed in 21 seconds.
- Exact cloud/region was **not obtained**. Do not label this a verified specific
  Azure-region result based only on the hosted-runner label.
- Evidence was retrieved from the check-run annotations API, not inaccessible
  signed full-log downloads. The diagnostic published escaped public JSON via
  notice annotations; it required no check-write permission or repository secret.

| Request | HTTP | Observed body/result | Usable candidate? |
|---|---:|---|---|
| Redlib Freedit homepage | 403 | HTML, JavaScript-required marker | No; homepage alone would not be feed evidence anyway |
| Redlib Freedit `/new.rss?limit=100` | 200 | HTML with Anubis + JavaScript-required markers; zero matching entries | **No RSS** |
| Redlib Freedit `/new/.rss` (engine path) | 200 | HTML with Anubis + JavaScript-required markers; zero matching entries | **No RSS** |
| Redlib Freedit `/new?limit=100` | 403 | HTML, JavaScript-required marker; zero post IDs | No |
| Redlib Freedit pristine `/new?limit=100&_fresh=...` | 403 | HTML, JavaScript-required marker; zero post IDs | No |
| Nitter Freedit `/TYPEII_EN/rss` | 403 | HTML, JavaScript-required marker; zero matching entries | No |
| nitter.cf `/TYPEII_EN/rss` control | 200 | RSS: 20 entries, 10 with matching account status paths | **Yes** |
| catsarch pristine Redlib listing control | 429 | HTML with Anubis + JavaScript-required markers; zero post IDs | No |

The nitter.cf control's newest matching ID was `2110581431927967903`, published
`2026-10-15T04:00:00+00:00`. The successful control establishes that this runner
could obtain a real feed from another mirror during the same test. The catsarch
control was itself challenged/rate-limited; it does not establish a working
Reddit listing baseline. The Redlib RSS responses illustrate why HTTP 200 alone
must not count as success.

This is a direct **GitHub-hosted-runner failure/challenge observation**, not
proof of a permanent or universal Azure/datacenter-block policy, nor proof of
failure from residential browsers. No JavaScript challenge bypass, credentials,
cookies, production monitors or Discord calls were used. A green diagnostic job
means all measurements completed, not that the mirrors worked. All 27 offline
diagnostic tests also passed on the runner.

Machine-readable observations, including exact requested URLs, times, headers,
body classifications and sampled control IDs:
[`diagnostics/freedit-2026-10-15-run-38722163102.json`](diagnostics/freedit-2026-10-15-run-38722163102.json).

Only the isolated diagnostic additions were committed/pushed to the session
branch. No PR was opened; main, production repositories, runtime fleets and
Kite files were not changed. The push trigger is limited to this session branch
and the three diagnostic code/workflow/test paths; documentation/result-only
pushes do not run it. No scheduler or automatic production promotion was added.

The earlier initial-review section below is retained as the pre-test record.
Its "unverified" and "no push/run" statements have been superseded by this live
follow-up, not by a production deployment.

## Initial review decision

**Pre-test recommendation: do not change the production fleets on the evidence then available.**

- **Nitter Freedit is already configured**, at position **5**, in current News-Express, both production copies, and Game-Express. No duplicate addition or new secret is needed. Keep it a trial fallback; do not move it ahead of the operator-selected first four without runner evidence.
- **Redlib Freedit is not configured.** Its RSS and HTML capabilities must be evaluated separately. The user's `/new.rss?limit=100` URL is different from the engine's `/new/.rss` URL.
- **GitHub Actions/Azure reachability remains unverified for Freedit.** Healthy monitor runs, a working homepage, and off-runner tests do not establish it. This workspace permits outbound access only to GitHub/package-registry hosts, not Freedit or the control mirrors. At the initial-review stage no live Freedit request or diagnostic workflow dispatch had been performed. The subsequent branch-triggered live results are recorded above.
- The additions accompanying this review are an isolated, manual diagnostic and its offline tests. No monitor engine, production workflow, fleet, secret, Variable, posting behavior or runtime cache was changed. No commit, push, PR or deployment was performed. Existing Kite deliverables were not modified.

## Audit scope and evidence quality

Read-only main-branch snapshots were downloaded and inspected:

| Repository | Snapshot commit | Relevant role |
|---|---|---|
| `uesu/News-Express` | `83a701ab4c8644a9b1ae5e61472dafdf8175b99a` | Development source, current round 76 |
| `uesu/7jkxmy9nvbc` | `a98d56fd7a89de16813cd619d1ccab97cfb55f7d` | Live Reddit |
| `uesu/wvkhabh2s22` | `905e4c96f52be88bbe895d891fba1bead3024cb5` | Live Twitter/X |
| `uesu/Game-Express` | `a41459e537c1e966310f9658800e2de860dc4737` | Game schedules/codes and X sources |

The audit inventoried and hashed 255 files, then reviewed the relevant feed, listing, post-page, token, configuration, workflow and historical-audit paths. This is not a claim that every line of every file was semantically audited. Every production file was compared byte-for-byte to its corresponding current News file. Differences were limited to runtime state: Reddit's `pending_reddit.json`, `posted_reddit.json`, `posted_tweets.json`, `proxy_health.json`; Twitter's first three of those. No production code/config/test divergence was found.

The latest 30 workflow-run metadata records from each repository all reported success (120 total). These are job conclusions, **not mirror-specific HTTP or parser results**. Fourteen attempts to retrieve full logs failed on the signed Actions log-download host, which this workspace cannot access; the empty download files were not used as evidence. The only usable full execution logs were the three supplied by the user.

The session checkout is older than the remote round-76 snapshots. This patch deliberately does not sync/reset the checkout or overwrite the newer remote fleet. Merge only the diagnostic additions into the current development tree if desired; do not upload this older checkout wholesale to production.

### Supplied execution logs (all 2026-10-15, UTC)

| Run | Runner evidence supplied | What the log establishes | What it does not establish |
|---|---|---|---|
| Twitter #7938, 10:00 | Azure `northcentralus`; checkout `9eafc497f78ea19cc3d18ad7725a08a1db7c3b44` | All five accounts fetched through **nitter.cf**, 98 entries total; one Wuthering Waves post delivered; state push succeeded (`905e4c9`) | No Freedit request/result is shown |
| Reddit #7345, 10:10 | Azure `westus3`; checkout `8d7ab86086d245d24fc47f2276bcc66867ecb4c7` | Combined RSS: 100 entries across five of six subs; 12 candidates; one native-DASH post delivered at about 2.5-minute latency; state push succeeded (`a98d56f`) | Freedit was not demonstrated; unavailable Ananta listing is not proof of deletion and does not establish a fix by switching mirrors |
| Game #2867, 10:20 | Azure `northcentralus`; checkout `d72c244d8ae0587efc036c00c5db4c1a0bb106f3` | Source groups completed; Nitter HTTP aggregate 18 ok / 0 fail, 21 configured instances, token set; no new matching announcement/code; about 3.7-second monitor runtime | The aggregate is not per-instance evidence, not 21 successful mirror tests, and not necessarily 18 parsed usable feeds |

In the Reddit run, archive candidates missing from pristine listings were skipped without caching. Genshin/HSR pristine listings returned 100 entries, Wuwa 101. The EmbedEZ upgrade returned 400, but the already validated base was retained; the three embed warmups and final state push succeeded. Those embed-service results are distinct from Redlib source health. The intentionally skipped anonymous JSON/OAuth probe is consistent with the supplied inventory having no Reddit OAuth app secrets.

## Nitter: integration is already present

Current News and both production `testing area/twitter_v3.py` lists have 12 instances, in this order:

1. `nitter.cf`
2. `xitter.cf`
3. `nitter.meowing.monster`
4. `nitter.miningtcup.me`
5. **`nitter.freedit.eu`**
6. `nitter.gravitywell.xyz`
7. `tw.eir-nya.gay`
8. `shitter.thepixora.com`
9. `nitter.kareem.one`
10. `xcopy.uk`
11. `nitter.netbub.com`
12. `nitter.jaydenha.uk`

News's fetch loop is serial and accepts the first usable feed. If nitter.cf works, a successful run says nothing about the fifth entry. Both production repositories intentionally include both monitor implementations; do not delete the other platform's files.

Game's `gamexpress/config.py:DEFAULT_NITTER` has 21 defaults, also with Freedit fifth. `gamexpress/sources/twitter.py` probes batches of four and stops after two working sources, merging those timelines. Freedit is in the second batch and need not be attempted during healthy first-batch runs. Its separate status-feed resolver is not the same fleet as the timeline list.

Round-76 News and Game's rotation notes describe Freedit as a trial with historical off-runner success across eight union accounts and control-ID parity. Those results were **not reproduced here** and are not Azure admission evidence. The same history records why an off-runner success cannot justify promotion: xcopy later produced runner-side 403s across several Azure regions. The first two mirrors are documented as sharing a backend, so two hostnames should not be counted as independent redundancy.

No Freedit token is required by the inspected clients. `NITTER_RSS_TOKEN` is attached only to the explicitly token-gated miningtcup host, not to Freedit. Do not forward it to other mirrors. Game's `NITTER_INSTANCES`, if configured, **replaces** the default list rather than appending; setting it to just Freedit would discard the fallback fleet. It was not present in the supplied Variable inventory. Game loads its configuration through its environment/JSON wiring (`GE_VARS_JSON`); do not assume a newly created Variable is consumed without checking that wiring.

## Redlib: RSS, listing HTML and post HTML are different contracts

The current shared `REDDIT_RSS_INSTANCES` contains:

`www.reddit.com`, `old.reddit.com`, `redlib.miningtcup.me`, `redlib.catsarch.com`, `redlib.nadeko.net`, `redlib.privadency.com`, `safereddit.com`, `red.artemislena.eu`, `redlib.privacyredirect.com`.

`redlib.freedit.eu` is absent. Native combined Reddit RSS remains the primary source. The per-subreddit fallback also inserts Eddrit separately; it is not simply another entry in this shared list.

| Route | Intended purpose | Required observation |
|---|---|---|
| `https://redlib.freedit.eu/` | Homepage availability | Not RSS or listing evidence |
| `/r/Genshin_Impact_Leaks/new.rss?limit=100` | User-requested feed URL | Real RSS/Atom with matching post permalinks, not a 200 HTML error |
| `/r/Genshin_Impact_Leaks/new/.rss` | Current fallback's exact URL shape | Test independently; do not assume it aliases the preceding route |
| `/r/Genshin_Impact_Leaks/new?limit=100` | HTML listing | HTML Content-Type and correctly scoped post links |
| Same HTML URL with `&_fresh=<milliseconds>` and no-cache headers | Pristine-listing request | IDs/visible ages compared with a control; a cache-buster expresses intent, not proof of freshness |
| A known post's own RSS and HTML permalink | Single-post recovery, liveness and media enrichment | Correct post identity and compatible removal/media markup; not covered by the initial fixed-URL probe |

Relevant current News code paths:

- `_fetch_feed` accepts only nonempty parsed feeds with a `/comments/` link among the first five entries; it has a 15-second timeout and special 429 backoff. A 200 response alone is not usable RSS.
- `_fetch_new_listing` races HTML `/new` requests and native RSS listing probes, accepting the first usable ID set within a bounded deadline. HTML requires HTTP 200, an HTML Content-Type and post IDs. Pristine requests send `Cache-Control: no-cache, no-store`, `Pragma: no-cache`, and `_fresh`; successful results are memoized for the run. It separately records the oldest visible age. These checks are not an RSS-subscription test.
- `_fetch_post_rss` iterates the same shared fleet for a post's own feed. `_fetch_redlib_post_page` uses it for post HTML; successful HTML is reused by liveness/media logic. Gallery enrichment also fans out over this fleet. Therefore merely appending Freedit changes more than RSS failover, including parallel listing traffic and which listing can win first.
- Tokens remain host-specific. `REDDIT_FEED_TOKEN` is for native Reddit requests, and the miningtcup token helper is for that gated mirror. Neither should be sent to public Freedit.

Round-75 history recorded six other public Redlib RSS routes returning upstream `Reddit error 400` / `Bad Request` HTML, while catsarch's ordinary HTML listing worked. This is a warning to distinguish formats, **not a measured Freedit failure**. We cannot infer that Freedit has the same internal route problem without observing its response.

### Supplied Variables/secrets

`REDDIT_MIRROR=embeddit.deltandy.me` is documented as a **V1 embed-mirror setting**, not a V3 Redlib source selector. The inspected V3 workflow does not wire it into a Redlib fleet override. Do not change this Variable to Freedit expecting RSS failover to change, and do not replace an embed-rendering service with Redlib.

The supplied webhook/account/subreddit tokens, automation settings and Game role-ping settings do not add an implicit Freedit probe. None needs to be disclosed or changed for this diagnostic. Game has no corresponding Reddit monitor integration requiring a Redlib fleet addition for this task.

## Added manual diagnostic (development only)

Files:

- `.github/scripts/probe_freedit.py`
- `.github/workflows/freedit_probe.yml`
- `tests/test_freedit_probe.py`
- This review

The stdlib-only script makes one sequential request to each of eight fixed endpoints: the five Redlib requests above, Freedit's `TYPEII_EN/rss`, nitter.cf's matching control, and catsarch's pristine HTML control. Requests are spaced by two seconds. It has a 12-second socket timeout, a 20-second child-process deadline per endpoint, a 2 MiB response cap, and no retries, cookie jar, proxy-environment use, tokens, browser challenge execution or monitor imports. Redirects are restricted to same-host HTTPS on the standard port; a provider redirect outside that boundary is reported, not followed.

It records HTTP status, content type/encoding, selected cache headers, error markers, matching IDs, feed timestamps, listing counts/visible ages and timings. It rejects DTD/entity-bearing XML. Error-marker detection is deliberately conservative and can flag an ordinary post mentioning the same phrase; inspect such results rather than treating the label as a definitive provider block. Listings additionally require HTML Content-Type to qualify as a candidate.

A `candidate_response: true` is only a **syntactic, scoped response observation**, not proof of freshness, full runtime-parser parity, all-account coverage, media support or datacenter policy. Controls are also fallible. The strict stdlib XML parser is not the monitors' more tolerant `feedparser`, and the diagnostic network stack differs from `aiohttp`. Any rejected response requires inspection before concluding it is unusable by the engine. A successful first sample likewise needs runtime-equivalent follow-up.

The workflow supports `workflow_dispatch` and a diagnostic-path-only push on the session branch (never main or a production branch), grants `contents: read`, uses the repository's SHA-pinned checkout with `persist-credentials: false`, has a five-minute timeout, and references no repository secrets. It runs the offline tests and then the diagnostic. There is no cron, posting, cache commit or automatic promotion. Results appear as JSON in the step log and as a table in the job summary; escaped JSON notices are also available through the check-run annotations API; a temporary runner JSON file is not a persistent uploaded artifact. **A green job means the diagnostic completed, not that the mirrors passed.** Endpoint failures intentionally remain report data.

### How to obtain the missing runner evidence

The initial review did not dispatch anything. The completed follow-up used the branch-only push trigger; the manual instructions below remain an alternative for future use.

1. If desired, accept these four additions into the **current development tree**, preserving the newer remote runtime code. No PR is required by this deliverable. A newly added manual workflow normally needs to exist on the default branch before the Actions UI exposes its Run workflow button.
2. Run **Freedit endpoint probe (no posting)** from News-Express's Actions page. Do **not** run a live monitor as a substitute; Game's test mode can also send real cards.
3. Save the JSON from the probe step plus the `Set up job` runner cloud/region details. The `ubuntu-latest` label alone does not prove an Azure region. No external IP/geolocation service is called by this script.
4. Compare exact routes independently. HTTP 403/429, challenges, HTML returned on an RSS route, and genuinely empty feeds are different results. Compare matching IDs and creation dates against a working control; a quiet account is not stale merely because its last post is old. Review ordinary versus pristine listing IDs and visible ages without assuming 100 entries is mandatory.
5. If the initial sample succeeds, repeat sparingly at different times and on actual runner allocations. It covers only one handle and one subreddit. Before promotion, use a separately reviewed bounded diagnostic to cover all configured accounts/subreddits, known post RSS/HTML, and representative gallery/video/removal cases. Verify current control-ID parity rather than relying on the historical eight-account report.
6. A development-run success does not prove every future production runner can connect. If production-repository confirmation is needed later, copy only the isolated diagnostic workflow/helper/test into those repositories with explicit approval. Keep production monitors unchanged while collecting observations. A hosted image does not guarantee a chosen cloud/region; describe only the region actually recorded.

On an unrestricted workstation, the same script can be run without GitHub Actions:

```sh
python3 tests/test_freedit_probe.py
python3 .github/scripts/probe_freedit.py --output /tmp/freedit-probe-results.json
```

A workstation result remains off-runner evidence.

## Conditional integration plan, not an applied change

- **Nitter / all four repositories:** it is already fifth. Leave the list alone, preserve the first four and the token boundary, and collect host-specific evidence before changing rank. Preserve the exact-order smoke guards when any future authorized fleet edit occurs.
- **Redlib / News and Reddit production:** if both the exact engine RSS route and HTML/post semantics pass the necessary runtime/runner checks, propose a narrow fleet change with named regression tests. Preserve native combined RSS, stateless fresh/listing gates, cancellation behavior and all dedup/liveness/media rules. Appending an HTML source is not passive: it joins parallel races.
- **Redlib HTML-only success:** do not call it an RSS fallback. A capability-separated RSS versus HTML fleet would be a different, explicit behavioral change requiring review and tests; this patch does not implement it.
- **Twitter production's shared Reddit files:** both prod trees mirror the shared source by design, but only the Reddit workflow uses that engine. Follow the maintainer's existing manual synchronized-upload process if a later change is approved; do not replace the Twitter Nitter fleet with Redlib.
- **Game:** no duplicate Nitter entry and no Redlib integration justified. Do not replace its 21 defaults with a single-host `NITTER_INSTANCES` override.

## Validation performed locally

All tests below ran offline on the session checkout. The diagnostic suite also passed on the hosted runner in the live follow-up:

- `python3 tests/test_freedit_probe.py` — **27 tests pass**, covering URL spelling, RSS/Atom parsing, account/subreddit matching, error HTML, listing extraction, MIME gating, candidate acceptance/rejection, DTD rejection, credential exclusion, redirects, oversized responses, transport failures, worker/deadline errors workflow-command escaping and branch-scoped workflow safety checks.
- `python3 tests/test_smoke.py` — **SMOKE TEST: ALL PASS**.
- `python3 tests/test_reddit_signals.py` — **REDDIT SIGNAL TEST: ALL PASS (96 pass)**.
- `python3 tests/test_twitter_media.py` — **TWITTER MEDIA TEST: ALL PASS**.

Existing monitor tests use stubs; their fixture posting log lines are not real Discord deliveries. These passes establish local regression/diagnostic checks only, not Freedit availability or a newly verified production deployment.

Source anchors: current News `testing area/twitter_v3.py`, `testing area/reddit_main_v3.py`, `tests/test_smoke.py`, the two monitor workflows, README's Variable table, `docs/history/ROUND_75.md` and `ROUND_76.md`; current Game `gamexpress/config.py`, `gamexpress/sources/twitter.py`, HTTP layer, workflow and rotation notes. Historical claims above are explicitly attributed to those repository records rather than presented as fresh measurements.
