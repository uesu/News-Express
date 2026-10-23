# Round 83 — Arctic text-only pending-approval ghost (ZZZ 1xd8ppc, 2026-10-23 08:55)

## Symptom

* `Zenlesszonezeroleaks__1xd8ppc` `[ZZZ 3.4] Sunbringer Outfit 3D Model Renders` by `Fender-Ali` posted at `16:55` via `News Test ZZZ` as `text | native | 0 items` `LATENCY 5.1min` `archived counts` while still **Post is awaiting moderator approval** on `r/Zenlesszonezeroleaks` (1 upvote, 0 comments, screenshot `17:00`).
* Like Genshin `1xcjoqu` ghost (archived counts, delivered 8h late while deleted) but via **Arctic** text-only path: `Combined feed OK 100 entries covering 5/6 subs` → `RSS had no new posts — trying 27 post(s) from the archive` for Zenless, `24 candidates`, `11/23 REDLIB-REACH`, `redlib gallery enrichment failed (all instances)` → native fallback posted with archived counts.
* Monitor #9561 `2026-10-23T08:55:26Z westus` `aea7586→a5515bd`: `proxy warmup OK (3/3)`, `post JSON HTTP 403 — native mode`, `vxreddit placeholder`, `embeddit text only`, `redditez no data`, `native media 0`.

## Root cause

* R79 no-ghost gate `ghost-check` only guarded **re-appearing** `removal_notice` text-only via **RSS** (`unique_key in pending && !ArcticEntry && !media`): fresh Arctic text-only (first-seen, `not in pending`) bypassed it; Arctic first-time pending posts never verified live before posting.
* `verify_archive_post_live` with `feed_ok=False` for Arctic still returned `live via redlib` (redlib page exists while queued, no banner), so liveness gate didn't stop it.

## Fix — `testing area/reddit_main_v3.py` only

* Added `arctic-ghost-check` immediately after R79 `ghost-check`:
  ```py
  if (not TEST_POST_ID and not DRY_RUN and isinstance(entry, _ArcticEntry)
          and not data.get("media") and post_json is None):
      _live3, _why3 = await verify_archive_post_live(session, path, label=f"{unique_key} arctic-ghost-check", feed_ok=False)
      if not _live3:
          mark_pending(pending, unique_key, "pending approval", now, ...)
          liveness_not_verified ++ ; liveness_by_reason "arctic-text-only:{why}"
          keep pending (no archived ghost)
  ```
  - Text-only Arctic (native 0 items, no proxy media) must be live-verified (`proxy+redlib feed_ok=False`) else kept as `pending approval` (throttled like other pendings, posts once approved + verified). Legit approved Arctic text posts still pass (`live=True`) → post in 5 min. 0 extra req for media posts.

* `tests/test_smoke.py`: `mark_pending` count `5→6`, adds `"pending approval"` + `"arctic-ghost-check"` asserts.

## Verification

* `python -m py_compile` / `compileall -q` OK
* `tests/test_smoke.py` SMOKE TEST: ALL PASS (6 pendings)
* `tests/test_reddit_signals.py` 96 pass ; `test_twitter_media.py` ALL PASS
* Manual: `len(REDDIT_RSS_INSTANCES)==23` unchanged, `len(set)==23`, head `mint.lgbt`, traps absent.

## References

Monitor #9561 `aea7586→a5515bd`, pending approval screenshot `Fender-Ali 1 upvote`, R79 `1xcjoqu` ghost fix, PR #74, PR #76 `d138e3d`.
