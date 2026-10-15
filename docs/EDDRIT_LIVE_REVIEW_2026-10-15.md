# Eddrit and Freedit subreddit-root live review — 2026-10-15

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

## Results

Pending the live branch-triggered run at this revision. Results will be saved
with the run ID, exact requested URLs, runner details available through the API,
and response metadata. No production monitor is being dispatched. No PR or
main/production branch edit is required.

## Offline validation

The diagnostic suite now includes per-community URL coverage, parser scoping,
request-to-subject propagation, original-suite preservation and total-time/
workflow coverage checks, in addition to the prior transport/security tests.
The existing monitor regression suites are run before publishing the diagnostic.
