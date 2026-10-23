# Round 79 — token-powered JSON-first + no-ghost text-only re-check (2026-10-23)

## Genshin ghost

* `Genshin_Impact_Leaks_1xcjoqu` — text-only, `selftext=[removed]` `removed_by_category=automod_filtered`, `created_utc=1792678313 (2026-10-22 14:11:53Z)`, Arctic `retrieved_on 1792678332 ups 1 num_comments 1`. RSS stayed stale text in combined feed `100 entries/5 subs` with `archived counts` stats (`proxy.get("stats")==None → arctic["ups"]` in `resolve_post_media` #4962/5185). Pending `removal_notice` for `455.1 min`, delivered `21:50Z` with `latency 458.8 min` and `payload flags 32768` while Reddit already deleted — `redditez/vxreddit/embeddit` all text-only + `redlib gallery 0/1`, native `0 url(s) → kind=none` → posted as text, needed strict live-gate.
* Contrast fresh text `WutheringWavesLeaks_1xcofgc` (`created 17:08Z → 21:10Z latency 2.1–6.2 min, ups 1, Arctic true`) posted via `vxreddit` image / normal path — never pending `removal_notice`, not a ghost.

## Changes

**1) JSON-first instant fallback** — `REDDIT_FEED_TOKEN` + `format_reddit_feed_query` host/path-agnostic (`old.reddit.com/.rss?feed=…`, `feed=…&user=…`, bare key). `feedtoken_probe_enabled()` on `auto` now `True` when `(CLIENT_ID&&SECRET) || (REDDIT_FEED_TOKEN && format_reddit_feed_query)` — empty/invalid still `OFF` (r31 guard preserved). `fetch_post_json` tries `www.reddit.com/comments/{id}.json?limit=25&raw_json=1&{feed_q}` first (`BROWSER_HEADERS`), `_stagger = min(FEEDTOKEN_JSON_STAGGER,2)` for token tier vs `65 s` anonymous, `403` → `_feedtoken_json_failed=True` memoized → next posts `0 s` RSS (`1 combined RSS req + ≤1 JSON req/run`). No workflow Variable/Secret change needed (`auto` powers existing token, `force`/`off` as before); `FEEDTOKEN_JSON_STAGGER` default stays `65` for tests (`r49b==65`), header §1b updated from stale Round-31-only to Round 79 wording.

**2) No-ghost text-only** — after `posted_ts = int(max(...))` (kept outside R25 `posted_ts =` extraction to keep `SMOKE TEST: ALL PASS`): `if (not TEST_POST_ID && not DRY_RUN && unique_key in pending && reason in _NO_RECHECK_REASONS && !ArcticEntry && !data.get("media")) → verify_archive_post_live(..., feed_ok=False, ghost-check) → if not live: mark_pending(removal_notice) + ghost-text-only:{why} + liveness_not_verified → continue`. `archived: True` with `media` (gallery / single pic / video) skips the gate entirely — only `removal_notice` re-appearing text-only ghosts are held. Fresh text posts (`Wuthering 1xcofgc`) unchanged (`2–6 min`), all future subs covered, deleted purge after `48 h` (`purge_expired_pending`), approved restores still post via RSS live-gate.

## Verification

* `python3 -m compileall -q "testing area" tests → compileall: OK`
* `timeout 120 python3 tests/test_smoke.py → SMOKE TEST: ALL PASS` (r30 `4→5` + `ghost-check`/`ghost-text-only`/`removal_notice`, `r31 auto without app OFF`, `r49b STAGGER==65`, R25 extraction intact, fleet 18).
* Live 403 on `.../1xcjoqu.json` and `.../1xcofgc.json` (datacenter), Arctic `1xcjoqu` truth.

## Deploy

No `.github/workflows` edit — attended path. Merge `arena/7420d783-news-express` → manual upload `testing area/reddit_main_v3.py` + `tests/test_smoke.py` (+ this doc/changelog) to `7jkxmy9nvbc`/`wvkhabh2s22` (engine first per `AGENTS.md`).

## References

PR #74 `2becfdb` (header fix) on `258c7e7`; base `b5bb262` (PR #73 fleet 18 merged).
