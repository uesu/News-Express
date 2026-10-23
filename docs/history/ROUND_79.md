# Round 79 — token-powered JSON-first instant fallback (2026-10-23)

## Changes

**JSON-first instant fallback** — `REDDIT_FEED_TOKEN` + `format_reddit_feed_query` host/path-agnostic (`old.reddit.com/.rss?feed=…`, `feed=…&user=…`, bare key). `feedtoken_probe_enabled()` on `auto` now `True` when `(CLIENT_ID&&SECRET) || (REDDIT_FEED_TOKEN && format_reddit_feed_query)` — empty/invalid still `OFF` (r31 guard preserved). `fetch_post_json` tries `www.reddit.com/comments/{id}.json?limit=25&raw_json=1&{feed_q}` first (`BROWSER_HEADERS`), `_stagger = min(FEEDTOKEN_JSON_STAGGER,2)` for token tier vs `65 s` anonymous, `403` → `_feedtoken_json_failed=True` memoized → next posts `0 s` RSS (`1 combined RSS req + ≤1 JSON req/run`). No workflow Variable/Secret change needed (`auto` powers existing token, `force`/`off` as before); `FEEDTOKEN_JSON_STAGGER` default stays `65` for tests (`r49b==65`), header §1b updated from stale Round-31-only to Round 79 wording.


## Verification

* `python3 -m compileall -q "testing area" tests → compileall: OK`
* `timeout 120 python3 tests/test_smoke.py → SMOKE TEST: ALL PASS` (`r31 auto without app OFF`, `r49b STAGGER==65`, R25 extraction intact, fleet 18; ghost gate removed 2026-10-23 — Arctic not posting if gone is handled by main liveness gate `verify_archive_post_live` for all entries).
* Live 403 on `.../1xcjoqu.json` and `.../1xcofgc.json` (datacenter), Arctic `1xcjoqu` truth.

## Deploy

No `.github/workflows` edit — attended path. Merge `arena/7420d783-news-express` → manual upload `testing area/reddit_main_v3.py` + `tests/test_smoke.py` (+ this doc/changelog) to `7jkxmy9nvbc`/`wvkhabh2s22` (engine first per `AGENTS.md`).

## References

PR #74 `2becfdb` (header fix) on `258c7e7`; base `b5bb262` (PR #73 fleet 18 merged).
