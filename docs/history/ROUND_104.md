# Round 104 (2026-11-02) — the relay is 1:1 with the old chain (relay 0.0.8)

## Provenance

Owner, after round 103's coverage table (three edges where the old chain was still
consulted for a relay-served post): the relay engine must cover **everything** the old
structure does, in News-Express *and* Game-Express. The vxreddit → embedez → embeddit
proxies are **part of the new structure** and stay; what must **not** be needed for a
relay-served post: redlib instances, reddit.com instances, Arctic. The old chain stays as
the fallback.

The three edges, plus two more found while reading the per-post pipeline:

| # | Old-chain touchpoint for a relay post (before) | Round 104 |
|---|---|---|
| 1 | Liveness in the first ~10 min: `candidate_liveness_verdict` did an Arctic lookup for a relay record without an update yet | A relay record that is not `removed` is **live from the listing itself** (`relay-listing`), no archive lookup; the relay's first re-check now comes at ~5 min |
| 2 | Approvals after 6 h relied on the round-98 Arctic reclaim | Relay stage **24 h** added (300 / 1800 / 7200 / 21600 / 86400 s); a post that flips removed/filtered → live is **re-sent complete** (`resent: "approved"`) |
| 3 | Game-Express publisher follow-up comments came from post pages / mirrors; News-Express's `💬 OP comment` line existed in FULL MODE only | Relay reads the author's own comments of **official** posts at every re-check; on change the record is re-sent with `opCommentCount` inline + `opComments` in `record.json`. Both readers consume them |
| 4 | `resolve_post_media`: `fetch_arctic_post` (post + parent), child Arctic probe in `discover_original_for_media`, two `enrich_gallery_redlib` harvests; `main()` asked `fetch_post_json` (reddit.com) first | `relay_complete` on the base gates every one of them off; native media come from the record's own URLs, counts from the record / newest re-check |
| 5 | Game-Express `items()` resolved empty-text entries and `program_post()` resolved candidates through `resolve_post()` (redlib / reddit.com) | `relay_complete` entries are never passed to `resolve_post()` — an empty `text` is a title-only post |
| 6 | `retract_dead_posts` always took a `/new` listing snapshot (redlib / reddit.com) | Skipped (with the mirror probe) for any post the relay has re-checked |

## Relay 0.0.8 (`devvit/gaming-express`, uploads as Reddit 0.0.7)

1. **Stages** `RECHECK_STAGES_SECONDS = [300, 1800, 7200, 21600, 86400]`; `RECHECK_WINDOW`
   24 h + 30 min. Stage 1 is the next poll after delivery (modqueue / AutoMod removals), the
   24 h look catches late approvals and late publisher comments.
2. **Approval re-send.** `becameLive(previousState, item)`: the stored `state:<id>` said
   `removed=<category>` or `deleted=true`, the re-check says live → the complete record is
   re-sent (`revision` + 1, `resent: "approved"`). A reader whose 6 h window has lost the
   first record (a post filtered at 00:05 and approved at 09:00) still gets the whole post.
3. **Publisher comments.** `isOfficialRecord(rec, officialUsers)` = author ∈ `officialUsers`
   ∪ distinguished ∪ flair `/\bofficial\b/i` (the same rule Game-Express applies). For those,
   each re-check reads `post.comments.get(50)`, keeps the author's own non-empty comments
   (oldest first; `{id, body, created, stickied}`), hashes them (`oc:<id>`), and on change
   re-sends the record with `opCommentCount` inline and `opComments` in `record.json`
   (`resent: "comments"`). Reasons join with `+` (`edited+comments`). One request per official
   post per stage, inside the existing ≤ 20 re-checks / 20 s soft deadline; a comments
   failure is logged and treated as "none" so it can never block the liveness update.
4. Record stays `v: 1`; pre-0.0.8 readers ignore the two new keys.

Unit tests (`relay.test.ts`, 27 pass): the five stages, `isOfficialRecord`, `opCommentsHash`,
`becameLive` (filtered → live, removed → live, deleted → live, live → live = no, still removed
= no), inline record carries only the count while `record.json` carries the comments.

## News-Express reader (`testing area/reddit_main_v3.py`)

- `_intake_needs_full_record` adds `opCommentCount > 0 and not opComments`;
  `apply_intake_full_record` merges `opComments` (`parse_intake_op_comments`: ids normalised,
  blank/malformed dropped). Same `INTAKE_ATTACHMENT_FETCHES = 10` bound.
- `intake_base_data` adds `relay_complete = not _intake_needs_full_record(rec)`,
  `relay_stats` (`relay_record_stats`: the newest `v: 2` item's score/comments, else the
  record's) and `relay_op_comment` (`relay_op_comment`: stickied first, else the earliest, in
  `extract_op_comment`'s shape — text via `strip_html`, permalink `…/comment/<id>/`).
- `resolve_post_media`: `relay_complete` → logs *relay record is complete — no archive, redlib
  or reddit.com request*, skips the parent archive lookup, sets `arctic = None` instead of
  `fetch_arctic_post`, drops both `enrich_gallery_redlib` calls; `discover_original_for_media`
  skips the child archive probe. The proxy wave (`fetch_proxy_post_memo`, embeddit stats,
  `resolve_video_url`) runs exactly as before. `stats` falls back to `relay_stats` (not for
  crossposts — those count the parent). `op_comment` is set from `relay_op_comment` when
  `REDDIT_OP_COMMENT` is on (default), rendering the existing `💬 OP comment (stickied)` line.
- `main()`: `post_json = None` for `relay_complete` bases (no reddit.com `.json` attempt).
- `candidate_liveness_verdict`: after the relay-update and record-`removed` checks, a relay
  record returns `("live", "listed on Reddit's /new by the relay (not removed); relay re-check
  pending", "relay-listing")`. The round-101 `relay_listing_is_fresher` branch (archive
  snapshot vs relay sighting) is removed with its helper — unreachable now.
- `retract_dead_posts`: `_fetch_new_listing` + `live_removal_reason` run only when
  `relay_update_for(post_id)` is None (new helper over `_INTAKE_UPDATES`).

A record the CDN could not complete (`bodyTruncated` still true, parent unnamed, comments
announced but missing) is **not** `relay_complete` and keeps the full round-101/103 fill-in:
archive, redlib harvest, post JSON. Nothing in the fallback chain changed.

## Game-Express (hand-off patch refreshed, base `main` @ `ccfe564` / PR #135)

- `reddit_intake.py`: `needs_full_record` (+ `opCommentCount`), `parse_op_comments`,
  `apply_full_record` merges `opComments`; `record_to_entry` merges the author's comments
  **exactly like `parse_reddit_rss`** merges same-author comments from a post page — appended
  to `text`, links/images harvested, `comments=[{id, author, text}]` — and sets
  `relay_complete`.
- `reddit.py`: `items()` — `resolvable = not e.get("relay_complete")` guards both
  `resolve_post()` calls; `program_post()` — `detail = dict(e)` for `relay_complete`
  candidates. Zero redlib / reddit.com requests for a relay-served game, title-only posts and
  the Special-Program backup lookup included.
- `tests/test_reddit_intake.py` gains `test_relay_008_op_comments_and_complete_records`
  (7 blocks now); docs (SOURCES, CHANGELOG, PRIVACY) updated. Verified on a fresh `--depth 1`
  clone of `ccfe564` with plain `git am` (intake 7/7, smoke 628/628, ruff) and inside its
  `sync_tree()` production checkout. The hand-off doc's apply step now says plain `git am`
  (`--3way` cannot work on a shallow clone).

## Tests

- `tests/test_smoke.py`: 8 `r104` guards — comment parsing + card line; attachment fetch for
  `opCommentCount`; `relay_complete` / `relay_stats` / `relay_op_comment` on the base; the
  pipeline end-to-end with every proxy down (two native photos, Reddit's counts, the stickied
  comment, **0** archive / redlib calls) versus a cut record (archive + redlib still asked);
  the retraction seatbelt (re-checked post: 0 listing/probe requests, unknown post: 1 each);
  source wiring of every gate; the Devvit 0.0.8 constants. The round-101 liveness guard now
  expects `relay-listing` for every clean relay record (it encoded the Arctic path).
- All three suites ALL PASS here and in a `sync_tree()` production checkout; Devvit
  `npm test` (tsc, biome, 27 unit tests, esbuild) green.

## Owner steps after merge

Zip → `npx devvit upload` (0.0.8 code → Reddit 0.0.7) — settings persist, nothing else
changes. Both repos' readers accept old and new records alike, so upload order does not
matter. Activation of the readers is unchanged: secret `DISCORD_BOT_TOKEN` + Variable
`INTAKE_CHANNEL_ID` (`docs/DEVVIT_SETUP.md` §9/§10).
