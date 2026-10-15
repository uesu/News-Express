# Eddrit and Freedit subreddit-root live review — 2026-10-15

**Later fleet-wide follow-up:** see [OTHER_INSTANCES_LIVE_REVIEW_2026-10-15.md](OTHER_INSTANCES_LIVE_REVIEW_2026-10-15.md) for the remaining public Nitter/Redlib hosts. The shared diagnostic workflow now runs that matrix; the results below remain the historical record of this earlier run.

## Scope

Requested follow-up to the first Freedit probe: test the exact Eddrit URL
`https://eddrit.com/r/Zenlesszonezeroleaks_/new`, cover all six game communities,
and test `https://redlib.freedit.eu/r/Genshin_Impact_Leaks` without `/new` or a
query string. The initial Freedit run did **not** request that exact subreddit
root. Prior `/new` failures do not settle whether a root page works.

“All games” is interpreted as the six public Reddit communities in the
News-Express documented defaults and the supplied webhook inventory, not a
request to run Game-Express's posting workflows or test unrelated source APIs:

- ZZZ: `Zenlesszonezeroleaks_`
- Genshin: `Genshin_Impact_Leaks`
- HSR: `HonkaiStarRail_leaks`
- Wuwa: `WutheringWavesLeaks`
- HNA: `HonkaiNexusAnimaLeaks`
- Ananta: `AnantaLeaks`

For each community the isolated diagnostic requests:

1. Eddrit `/r/<sub>/new` — exact HTML route shape in the user's link.
2. Eddrit `/r/<sub>/.rss` — **the existing engine's actual Eddrit fallback**.
3. Eddrit `/r/<sub>/new/.rss` — a separate new-sorted RSS route check, not assumed equivalent.
4. Freedit `/r/<sub>` — root HTML, including the user's exact Genshin URL.

One additional anonymous native Reddit `/r/Genshin_Impact_Leaks/new/.rss?limit=100`
request is a control. Controls can fail too; one control is used instead of six
requests against Reddit's tight anonymous quota. There are 25 fixed URL requests
in total, no retries, no token forwarding and no arbitrary URL input. Requests
within each game's suite are separated by two seconds. Each endpoint retains a
20-second total child-process deadline, 12-second socket timeout and 2 MiB cap.

The same session-branch-only workflow now runs the six suites as separate steps,
keeping each step's public JSON notice count below ten. Its job budget is ten
minutes for the larger bounded request set. The original eight-URL Freedit suite
remains available with `--suite freedit`; it is not automatically repeated in
this follow-up. The workflow filename remains `freedit_probe.yml`, with display
name **Reddit mirror probe (Eddrit + Freedit, no posting)**.

## Existing integration and interpretation

Eddrit is **already integrated** as a token-free RSS fallback in both the local
and previously audited current News/production engines. In
`fetch_subreddit_feed`, its `/r/<sub>/.rss` request is inserted after the
miningtcup attempt. It is not part of the shared HTML listing fleet.

A working Eddrit `/new` page is not proof that its RSS route works, and does not
mean it is already being used for pristine HTML listing gates. A working
Freedit subreddit root is not proof of `/new` compatibility or freshness: its
sort order may differ. No monitor integration, route substitution, fleet
promotion or freshness-gate changes are included in this diagnostic.

Matching feed entries and HTML links are scoped case-insensitively to the
specific requested subreddit, not hard-coded to Genshin. HTTP status, content
type, markers, IDs and feed dates are reported separately. The stdlib parser is
stricter than the monitors' feedparser; a parser rejection alone must not be
misreported as an HTTP failure. A syntactically valid feed is not an automatic
freshness certificate. No browser challenge execution or WAF bypass is used.

## Results — completed

**Neither Eddrit's tested routes nor Freedit's subreddit-root pages supplied
usable content in this GitHub-hosted runner test.** Native Reddit's control did.

- Run: [38723188256](https://github.com/uesu/News-Express/actions/runs/38723188256).
- Commit: `db586f5444205c4efa0901dd823c22cb4322c576` on
  `arena/c45edf9b-news-express`, triggered by a diagnostic-only branch push.
- Requests: **2026-10-15 10:51:19–10:52:26 UTC**, or **18:51–18:52 Manila time**.
- Job: `116382547103`, completed successfully in 72 seconds. Green means the
  diagnostic completed, **not that the mirrors passed**.
- Runner: GitHub-hosted Linux/X64, `ubuntu-latest`,
  `GitHub Actions 1000020318`. Exact cloud/region was not obtained; this is not
  evidence of a particular Azure region or a permanent universal block policy.
- Evidence: all 25 endpoint records and six suite-context records retrieved from
  the GitHub check-run annotations API. No signed log downloads were needed.
  The CLI still displayed the workflow's earlier name, but the job's six steps
  and tested commit confirm that the expanded diagnostic executed.

In the table, **200 challenge** means `Content-Type: text/html`, Anubis and
JavaScript-required markers, and zero matching entries/post IDs. It does not
mean usable RSS or a real post listing. **403** means HTML with a
JavaScript-required marker and zero post IDs.

| Game / subreddit | Eddrit `/new` HTML | Eddrit `/.rss` (engine) | Eddrit `/new/.rss` | Freedit `/r/<sub>` root |
|---|---|---|---|---|
| ZZZ / `Zenlesszonezeroleaks_` | 200 challenge | 200 challenge | 200 challenge | 403 |
| Genshin / `Genshin_Impact_Leaks` | 200 challenge | 200 challenge | 200 challenge | 403 |
| HSR / `HonkaiStarRail_leaks` | 200 challenge | 200 challenge | 200 challenge | 403 |
| Wuwa / `WutheringWavesLeaks` | 200 challenge | 200 challenge | 200 challenge | 403 |
| HNA / `HonkaiNexusAnimaLeaks` | 200 challenge | 200 challenge | 200 challenge | 403 |
| Ananta / `AnantaLeaks` | 200 challenge | 200 challenge | 200 challenge | 403 |

### The two exact user URLs

- `https://eddrit.com/r/Zenlesszonezeroleaks_/new` — HTTP **200**,
  `text/html; charset=utf-8`, 4,468 bytes, Anubis + JavaScript-required markers,
  **zero post IDs**, `candidate_response: false`.
- `https://redlib.freedit.eu/r/Genshin_Impact_Leaks` — HTTP **403**,
  `text/html; charset=UTF-8`, 5,676 bytes, JavaScript-required marker,
  **zero post IDs**, `candidate_response: false`. This exact root URL is now
  tested independently of the earlier `/new` and RSS requests.

### Working control

`https://www.reddit.com/r/Genshin_Impact_Leaks/new/.rss?limit=100` returned
HTTP **200**, `application/atom+xml`, **100 entries / 100 matching post links**,
with no detected challenge markers. The newest matching post was `1x6hqxy`,
published `2026-10-15T10:08:01+00:00`; it is also the Genshin post identified in
the earlier user-supplied production log. The control's cache header was
`private, max-age=3600`; this result is not a general freshness guarantee.

The successful control shows that the runner could retrieve and parse a real
Reddit feed during this test. It does not turn the mirror challenges into usable
responses, establish all-six-sub native health, or prove any browser behavior.

Full observations, including request times, exact URLs, headers, sizes and
control IDs/dates, are preserved in
[`diagnostics/eddrit-freedit-six-games-2026-10-15-run-38723188256.json`](diagnostics/eddrit-freedit-six-games-2026-10-15-run-38723188256.json).

## Recommendation and unchanged production behavior

- **Eddrit is already present as an RSS fallback.** Do not duplicate it or add it
  to the pristine HTML listing fleet on these results. Treat this as a failed
  current runner sample rather than relying on the older source comment saying
  it passed on 2026-09-20. The earlier historical success was not reproduced.
- **Do not add Freedit root pages as a workaround for `/new`.** All six root
  requests failed, including the exact Genshin URL supplied by the user.
- No automatic removal, fleet-order change, retry change or route substitution
  was made. A separate request would be needed to change production behavior.
- No browser/WAF challenge bypass, tokens, cookies, Discord calls, posting
  workflows, PRs, main changes or production-repository changes were used.
  Only the isolated diagnostic and reports were committed/pushed to the session
  branch. Kite files remain untouched. Report-only pushes do not trigger probes.

## Validation

- `python3 tests/test_freedit_probe.py` — **31 tests passed locally and on the
  hosted runner**. Covers per-community URL coverage, parser scoping,
  request-to-subject propagation, original-suite preservation and total-time/
  workflow coverage, plus the prior transport/security checks.
- `python3 tests/test_smoke.py` — **SMOKE TEST: ALL PASS** locally.
- `python3 tests/test_reddit_signals.py` — **REDDIT SIGNAL TEST: ALL PASS (96 pass)** locally.
- `python3 tests/test_twitter_media.py` — **TWITTER MEDIA TEST: ALL PASS** locally.
