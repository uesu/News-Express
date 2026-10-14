# Round 75 — X RSS mirror rotation + Redlib RSS audit record

**Status:** Open — [PR #64](https://github.com/uesu/News-Express/pull/64)
**Scope:** Twitter V3 RSS source order; Reddit V3 audit comments; offline smoke guards
**Date:** 2026-10-14

## Evidence and precheck

The source changes are based on response-body reads from 2026-10-14, not
status codes alone. The initial precheck confirmed that the newest Twitter
production run had no real entries delivered through `nitter.meowing.monster`.
That absence was not evidence the host was still down: the serial chain stops
when an earlier instance serves, so a run handled by `nitter.cf` or `xitter.cf`
does not reach or test meowing.monster. The host's later same-day revival and
the corrected final ranking are recorded in the addendum below.

### Twitter/X RSS mirrors

| Candidate | Original morning probe/result (final status in addendum) | Initial decision |
|---|---|---|
| `nitter.meowing.monster` | Connection failure on every probe during the original outage. The status.d420.de snapshot then showed 17/22 checks unhealthy, 0 points, blank connectivity and no version; the host later revived the same day. | Initially demoted to the final probe, not deleted. The demotion was reversed after recovery and later body/runner evidence; see the addendum. |
| `xcopy.uk` | `/Wuthering_Waves/rss` was hand-read: current entries dated 2026-10-12 through 2026-10-14, full text, media and links, with no wall, splash page or browser challenge. It is listed on the shitter fork's working-instances wiki, uses an independent backend and is not token-gated. | Initially trialed in meowing.monster's former fifth slot; the operator later directed seat 3 after the full-coverage parity test. A clean off-runner body remains a trial ticket, not runner proof. |
| `nitter.pp.ua` | 98% on d420 and healthy all day, but refused the initial `/rss` probe; a later fill-in sweep found the feed bodies alias `shitter.thepixora.com`. | Not added; the later body comparison found no independent capacity. |
| `nitter.poast.org` | Also refused the `/rss` probe, leaving no readable body to audit. | Not added; no trial. |
| `shi.meowing.de` | Fronted a browser challenge. | Not added. |
| `xnologin.com` | Redirected to a tiekoetter page saying RSS is disabled. | Not added. |
| `nitter.privacyredirect.com` | Served an error page. | Not added. |

Serving bodies were verified that day from `nitter.cf`, `xitter.cf`,
`nitter.kareem.one`, `shitter.thepixora.com` and `xcopy.uk`. `xitter.cf`'s
feed links point back to `nitter.cf`, so those two names share a backend as
previously documented. `tw.eir-nya.gay` initially returned HTTP 429 in the
off-runner probe; on re-probe minutes later it served full bodies, including
TYPEII_EN, and the 429 cleared. Its runner ledger has no hard refusal (only
`LOSES_THE_RACE`), so it retains a seat with a retryable-rate-limit watch note.
The final probe-round findings supersede the earlier preliminary watch note.

### Reddit / Redlib RSS audit

All six Redlib RSS candidates in `REDDIT_RSS_INSTANCES` were fetched and
body-read at `/r/<sub>/new.rss?limit=100`. Every `.rss` request returned the
same upstream response: `Reddit error 400 "null": "Bad Request"`, on
Redlib's internal `new.rss.json?raw_json=1` call. This matches the
redlib-org issue #446/#518 breakage class: Reddit changed what its JSON API
accepts, and unpatched Redlib builds send a request shape it now rejects.

Additional observations: `nadeko.net` also fronts a `__goaway` challenge;
`privadency` load-balances to `redlib-2`; `artemislena` self-reports being
20+ commits behind; and `catsarch` runs a fork. The HTML `/new` listing path
is unaffected: `redlib.catsarch.com` rendered current posts in its listing
on the same day. Thus the round-64 listing confirmation and retraction
seatbelt keep their existing Redlib sources. The native Reddit feed still
answers, the `.rss` tier fails closed via permalink validation, and patched
Redlib builds can revive it without a code change.

## Final decision

The first proposal moved `nitter.meowing.monster` to the final probe based on
its morning outage. Later same-day evidence showed it had revived, and the
operator explicitly directed `xcopy.uk` to seat 3 after a full-coverage test.
The v4 fill-in sweep then added `nitter.freedit.eu` and
`nitter.gravitywell.xyz`, ranking the remaining members by runner history,
body coverage and track record. The complete twelve-member order and the
reason for each seat are recorded in the final addendum below. The round-40
operator-approved `nitter.cf` + `xitter.cf` pair remains byte-identical in
slots 1–2.

Reddit has no source-list change. Membership and order are unchanged; the
round-75 smoke guard pins membership and the native-first invariant. This is
an audit record, not a Reddit rotation or removal.

## Deliberate non-goals

- Nothing is deleted: the initial meowing.monster demotion was reversed after
  recovery; every Reddit source stays, and `tw.eir-nya.gay` keeps a seat.
- No Redlib source is added, removed or reordered. The public candidates share
  an upstream Reddit-400 failure, while the HTML listing path remains usable.
- `nitter.pp.ua` is not added: the fill-in sweep found its feeds serve
  `shitter.thepixora.com`-generated bodies, so it adds no independent capacity.
- No workflow, proxy service, gate, cache, media path, token mapping or
  environment constant changes.

## Validation

```text
python3 tests/test_smoke.py           # SMOKE TEST: ALL PASS
python3 tests/test_reddit_signals.py  # ALL PASS
python3 tests/test_twitter_media.py   # TWITTER MEDIA TEST: ALL PASS
git diff --check
```

The smoke suite pins the final twelve-member Twitter V3 order (`xcopy.uk`
at 3, meowing at 4, `freedit.eu` at 6, and `gravitywell.xyz` at 9), the
untouched operator pair, the retained walled tail, and unchanged Reddit RSS
membership with the native feed first. Existing V1/V2 source-order guards
remain on their separately reviewed lists.

## Addendum (2026-10-14, final order)

This final addendum supersedes the initial Round 75 Twitter demotion decision.
It incorporates the operator's seat-3 direction, the probe round ranking and
the subsequent fill-in sweep. No source is deleted; the Twitter fleet grows
from ten to twelve.

### Revival, precheck limitation and operator direction

`nitter.meowing.monster` was genuinely dark during the original morning
probes: connection failures on every attempt, about eight hours of downtime
(05:15–13:35 UTC), and a d420 snapshot of 17/22 checks unhealthy, 0 points,
blank connectivity and no version. It revived around 13:35 UTC; d420 showed
it healthy from 13:45 (94%), reporting version `2026.10.12-f97b733`. The
initial production-log precheck found no entries delivered through meowing,
but that did not test whether the host had recovered: the serial fallback
returns as soon as an earlier host delivers, so a run served by `nitter.cf`
or `xitter.cf` never reaches meowing and has no meowing verdict to log.
After revival, Game-Express run #2621 delivered from it on 5/6 handles via
IPv4 runners. Earlier run #2323 had delivered 6/6. d420 lists its
connectivity as IPv6 while the runners are IPv4-only, explaining the
slow-but-working behavior. The original last-place demotion is therefore
reversed: after the operator pair and xcopy, meowing takes seat 4.

The operator separately ran a full-coverage test for `xcopy.uk`: bodies
across every monitored account on both monitors were read and top tweet IDs
matched the `nitter.cf` controls (8/8). The three active News-Express
accounts were re-probed that afternoon with identical top IDs and current
entries. The operator then directed `xcopy.uk` to seat 3, ahead of every
other mirror. The off-runner test remains a trial ticket; if the chain ever
reaches it, the production runner supplies the runtime verdict.

### Probe round: ranking the existing fleet below the operator pair

Top tweet IDs were compared across serving mirrors and against the
`nitter.cf` controls from the morning full-coverage test. Matching IDs
establish current bodies rather than stale feeds.

| Final seat | Host | Body and runner evidence |
|---:|---|---|
| 4 | `nitter.meowing.monster` | TYPEII_EN, PomPom_HonkaiSR and Wuthering_Waves returned full bodies with identical current top IDs through Oct 14 07:00; HonkaiNA and Ananta_EN from the full-coverage pass bring it to 5/5 accounts. d420 showed it healthy since 13:45 (94%). It is the only non-token-gated mirror besides the operator pair with positive runner deliveries: Game-Express run #2323 was 6/6; run #2621 after revival was 5/6. It remains on watch for the IPv4/IPv6 latency difference. |
| 5 | `tw.eir-nya.gay` | PomPom_HonkaiSR, Wuthering_Waves and (on re-probe) TYPEII_EN served full current bodies with identical IDs. One TYPEII_EN 429 cleared on retry minutes later: an aggressive per-request limit, not a hard refusal. The Game-Express ledger records `LOSES_THE_RACE` only. |
| 7 | `shitter.thepixora.com` | TYPEII_EN, PomPom_HonkaiSR and Wuthering_Waves served full bodies with identical IDs; d420 was healthy on all 21 checks (91%). Game-Express runners received HTTP 403 on all six handles on 2026-10-13, the freshest hard runner refusal in this fleet, so it sits below the two no-runner-evidence trials. |
| 8 | `nitter.miningtcup.me` | Token wall off-runner; d420 93%, IPv4 and RSS OK. Game-Express runners proved 6/6 with the token; without it the monitor skips instantly. It remains the strongest token-backed spare. |
| 10 | `nitter.kareem.one` | 3/5: Wuthering_Waves, HonkaiNA and Ananta_EN served current bodies with matching IDs. `User "TYPEII_EN" not found` and `User "PomPom_HonkaiSR" not found` were each reproduced twice while its game feeds served — deterministic account-resolution gaps, not downtime. Its gaps complement gravitywell.xyz at seat 9. |
| 11 | `nitter.netbub.com` | Go-away anti-scrape challenge wall. |
| 12 | `nitter.jaydenha.uk` | Click-to-enter interstitial; d420 flapped with six blips and the build is outdated. It remains last. |

### Fill-in sweep: candidates not yet in the fleet

The sweep covered the shitter fork's working-instances wiki (working,
rate-limited, redirector and Tor lists), the d420 board and Game-Express's
lower tier. Probes were made on monitored accounts and bodies were read.

| Candidate | Verdict |
|---|---|
| `nitter.freedit.eu` (seat 6) | **Admitted as a trial, 5/5 accounts.** TYPEII_EN (`2109654625897054655`), PomPom_HonkaiSR (`2109856657367007548`) and Wuthering_Waves (`2110264340259700754`) were current; HonkaiNA (`2095844335539605808`, quiet since Sep 4) and Ananta_EN (`2104254743027593701`, quiet since Sep 27) matched their controls, with pinned handling correct. Own backend and full fidelity for retweets, quotes, articles and media. The wiki labels it “active but rate limited,” but every probe answered cleanly. Not on d420 and no runner evidence. It sits above thepixora because unknown runner performance is preferable to a one-day-old known 403. |
| `nitter.gravitywell.xyz` (seat 9) | **Admitted as a trial, 3/5 accounts.** TYPEII_EN, PomPom_HonkaiSR and Ananta_EN were current with identical IDs; `User "Wuthering_Waves" not found` and `User "HonkaiNA" not found` were reproduced 2/2 while its other feeds served. Discovered as the backend behind Game-Express's `x.n0g.xyz`; the backend itself was not in either fleet. Its two account gaps complement kareem.one's two gaps, so together the mirrors cover all five accounts. Not on d420 and no runner evidence. |
| `nitter.pp.ua` | Not independent: `/rss` serves thepixora-generated bodies for both News-Express-exclusive accounts. The homepage is its own, but its feeds add a hop rather than capacity. |
| `nitter.anoxinon.de` | Rejected: “Instance has been rate limited,” matching the wiki's currently hard-limited tier. |
| `nitter.tiekoetter.com` | Rejected: “RSS feed is disabled,” consistent with d420. |
| `nitter.click` | Rejected: browser-check challenge on `/rss`. |
| `nitter.xitter.cc` | Rejected: back up, but RSS is disabled. |
| `xcancel.com` | Rejected: service suspended during legal proceedings. |
| `nitter.yuuki.sh` | Rejected: Cloudflare 526, origin SSL broken. |
| `nitter.perennialte.ch` | Rejected: stale by about a month; its top TYPEII_EN item was Sep 12 versus Oct 12 on the fleet. |
| `nitter.privacydev.net` | Rejected: HTTP 500. |
| `nitter.net` | Rejected: empty parked shell. |
| Wiki redirectors (`nitt.tr`, `twit.0r.cx`, `xxcancel.com`, `twiiit.com`), Tor onions and `bitter.st` | Not applicable: no independent RSS origin, or login-walled. |

### Final Twitter V3 order

1. `nitter.cf` — operator-approved primary.
2. `xitter.cf` — operator-approved secondary; its feed links point back to nitter.cf.
3. `xcopy.uk` — operator-directed seat after the 8/8 parity test.
4. `nitter.meowing.monster` — revived; 5/5 bodies and positive runner history, with IPv4/IPv6 latency watch.
5. `tw.eir-nya.gay` — serving; the 429 cleared on retry.
6. `nitter.freedit.eu` — 5/5 body trial, no runner history.
7. `shitter.thepixora.com` — clean bodies, but recent runner 403 watch.
8. `nitter.miningtcup.me` — token-gated, runner-proven 6/6 when configured.
9. `nitter.gravitywell.xyz` — 3/5 body trial, complementary coverage with kareem.one.
10. `nitter.kareem.one` — 3/5 body; deterministic gaps covered by gravitywell.xyz.
11. `nitter.netbub.com` — anti-scrape wall, retained as last-resort probe.
12. `nitter.jaydenha.uk` — interstitial / outdated build, retained last.

The Round 40 operator block is unchanged. Nothing is deleted; membership
increases from ten to twelve. Since the serial chain stops at the first
successful feed, while `nitter.cf` serves none of seats 3–12 is probed; the
lower ranking matters precisely when the operator pair fails. Reddit's
Round 75 audit comments and its membership guard are unchanged.
