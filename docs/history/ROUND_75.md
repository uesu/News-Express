# Round 75 — X RSS mirror rotation + Redlib RSS audit record

**Status:** Proposed for review
**Scope:** Twitter V3 RSS source order; Reddit V3 audit comments; offline smoke guards
**Date:** 2026-10-14

## Evidence and precheck

The source changes are based on response-body reads from 2026-10-14, not
status codes alone. Before applying the Twitter demotion, the maintainer
confirmed that the newest Twitter production run did not show real entries
delivered through `nitter.meowing.monster`.

### Twitter/X RSS mirrors

| Candidate | 2026-10-14 body / availability result | Decision |
|---|---|---|
| `nitter.meowing.monster` | Connection failure on every probe. The status.d420.de snapshot showed 17/22 checks unhealthy, 0 points, blank connectivity and no version. | Demote to the final probe; do not delete. It was body-audited in round 59 and moves back up when it answers. |
| `xcopy.uk` | `/Wuthering_Waves/rss` was hand-read: current entries dated 2026-10-12 through 2026-10-14, full text, media and links, with no wall, splash page or browser challenge. It is listed on the shitter fork's working-instances wiki, uses an independent backend and is not token-gated. | Trial in meowing.monster's former fifth slot. A clean off-runner body is a trial ticket; production-run logs provide the runner verdict. |
| `nitter.pp.ua` | 98% on d420 and healthy all day, but refused the `/rss` probe; there was no readable body to audit. | Not added. Re-probe first when another seat opens. |
| `nitter.poast.org` | Also refused the `/rss` probe, leaving no readable body to audit. | Not added; no trial. |
| `shi.meowing.de` | Fronted a browser challenge. | Not added. |
| `xnologin.com` | Redirected to a tiekoetter page saying RSS is disabled. | Not added. |
| `nitter.privacyredirect.com` | Served an error page. | Not added. |

Serving bodies were verified that day from `nitter.cf`, `xitter.cf`,
`nitter.kareem.one`, `shitter.thepixora.com` and `xcopy.uk`. `xitter.cf`'s
feed links point back to `nitter.cf`, so those two names share a backend as
previously documented. `tw.eir-nya.gay` returned HTTP 429 in this off-runner
probe, a fast failure; it retains its seat. The separate 2026-10-13 runner
verdict against it was HTTP 200 with zero entries on all handles, so it stays
under watch for a production-log confirmation rather than being demoted on
this one 429.

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

## Decision

Twitter V3 keeps the round-40 operator-approved `nitter.cf` + `xitter.cf`
pair in slots 1–2 and keeps `nitter.kareem.one` in slot 3. `tw.eir-nya.gay`
keeps slot 4 with a 429 watch note. The body-audited `xcopy.uk` trial takes
meowing.monster's former slot 5; `shitter.thepixora.com`, the token-gated
`nitter.miningtcup.me` fallback and the retained challenge-walled hosts keep
their existing relative order. `nitter.meowing.monster` moves to the final
probe, not out of the list. Its serial connect-timeout is incurred only if
every earlier instance has already failed.

Reddit has no source-list change. Membership and order are unchanged; the
round-75 smoke guard pins membership and the native-first invariant. The
record is an audit of the `.rss` failure mode, not a rotation or a removal.

## Deliberate non-goals

- Nothing is deleted: meowing.monster is demoted, every Reddit source stays,
  and `tw.eir-nya.gay` keeps its seat.
- No Redlib source is added, removed or reordered. The public candidates share
  an upstream Reddit-400 failure, while the HTML listing path remains usable.
- `nitter.pp.ua` is not added despite its tracker score because no `/rss`
  body was available to audit; it is first to re-probe when a seat opens.
- No workflow, proxy service, gate, cache, media path, token mapping or
  environment constant changes.

## Validation

```text
python3 tests/test_smoke.py           # SMOKE TEST: ALL PASS
python3 tests/test_reddit_signals.py  # ALL PASS
python3 tests/test_twitter_media.py   # TWITTER MEDIA TEST: ALL PASS
git diff --check
```

The smoke suite pins the complete Twitter V3 source order, the `xcopy.uk`
trial in slot 5, meowing.monster's retained final-probe position, the
untouched operator pair, and unchanged Reddit RSS membership with the native
feed first. Existing V1/V2 source-order guards remain on their separately
reviewed lists.
