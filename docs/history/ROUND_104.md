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
| 3 | Publisher follow-up comments | Dropped at the owner's request (see *Removed* below): neither engine ever showed them on a card, so the relay does not read comments |
| 4 | `resolve_post_media`: `fetch_arctic_post` (post + parent), child Arctic probe in `discover_original_for_media`, two `enrich_gallery_redlib` harvests; `main()` asked `fetch_post_json` (reddit.com) first | `relay_complete` on the base gates every one of them off; native media come from the record's own URLs, counts from the record / newest re-check |
| 5 | Game-Express `items()` resolved empty-text entries and `program_post()` resolved candidates through `resolve_post()` (redlib / reddit.com) | `relay_complete` entries are never passed to `resolve_post()` — an empty `text` is a title-only post |
| 6 | `retract_dead_posts` always took a `/new` listing snapshot (redlib / reddit.com) | Skipped (with the mirror probe) for any post the relay has re-checked |

## Relay 0.0.8 (`devvit/gaming-express`, uploads as Reddit 0.0.7)

1. **Stages** `RECHECK_STAGES_SECONDS = [300, 1800, 7200, 21600, 86400]`; `RECHECK_WINDOW`
   24 h + 30 min. Stage 1 is the next poll after delivery (modqueue / AutoMod removals), the
   24 h look catches late approvals.
2. **Approval re-send.** `becameLive(previousState, item)`: the stored `state:<id>` said
   `removed=<category>` or `deleted=true`, the re-check says live → the complete record is
   re-sent (`revision` + 1, `resent: "approved"`). A reader whose 6 h window has lost the
   first record (a post filtered at 00:05 and approved at 09:00) still gets the whole post.
3. Re-send reasons join with `+` (`edited+approved`). Record stays `v: 1`; pre-0.0.8 readers
   ignore the `resent` key. A publisher-comment follow-up (author's own comments of official
   posts, `opComments` in `record.json`) was prototyped the same day and removed before any
   upload — see *Removed* below.

Unit tests (`relay.test.ts`, 25 pass): the five stages, `becameLive` (filtered → live,
removed → live, deleted → live, live → live = no, still removed = no), a re-sent record
carries `resent` and `revision` inline.

## News-Express reader (`testing area/reddit_main_v3.py`)

- `intake_base_data` adds `relay_complete = not _intake_needs_full_record(rec)` (nothing
  cut, parent named) and `relay_stats` (`relay_record_stats`: the newest `v: 2` item's
  score/comments, else the record's).
- `resolve_post_media`: `relay_complete` → logs *relay record is complete — no archive, redlib
  or reddit.com request*, skips the parent archive lookup, sets `arctic = None` instead of
  `fetch_arctic_post`, drops both `enrich_gallery_redlib` calls; `discover_original_for_media`
  skips the child archive probe. The proxy wave (`fetch_proxy_post_memo`, embeddit stats,
  `resolve_video_url`) runs exactly as before. `stats` falls back to `relay_stats` (not for
  crossposts — those count the parent).
- `main()`: `post_json = None` for `relay_complete` bases (no reddit.com `.json` attempt).
- `candidate_liveness_verdict`: after the relay-update and record-`removed` checks, a relay
  record returns `("live", "listed on Reddit's /new by the relay (not removed); relay re-check
  pending", "relay-listing")`. The round-101 `relay_listing_is_fresher` branch (archive
  snapshot vs relay sighting) is removed with its helper — unreachable now.
- `retract_dead_posts`: `_fetch_new_listing` + `live_removal_reason` run only when
  `relay_update_for(post_id)` is None (new helper over `_INTAKE_UPDATES`).

A record the CDN could not complete (`bodyTruncated` still true, parent unnamed) is **not**
`relay_complete` and keeps the full round-101/103 fill-in:
archive, redlib harvest, post JSON. Nothing in the fallback chain changed.

### Removed at the owner's request: the `💬 OP comment` card line

The owner's live-card screenshots never showed it (it existed in FULL MODE only, i.e. with a
Reddit app, which this deployment does not have), so it is gone from both structures:
`REDDIT_OP_COMMENT` / `INCLUDE_OP_COMMENT`, `OP_COMMENT_MAX_CHARS`, `extract_op_comment`,
`op_comment_text`, the `_top_comments` collection in `fetch_post_json`, the `op_comment` key
of `resolve_post_media`'s result, the `op_line` plumbing in `build_v3_payload`, the workflow
`env:` line, the `.env.example` block and the README row. The owner then asked for the same on
the relay and Game-Express ("it doesn't need it"): the 0.0.8 publisher-comment follow-up
(`isOfficialRecord`, `authorComments`, `oc:<id>`, `opCommentCount` / `opComments`, `resent:
"comments"`) and the Game-Express `parse_op_comments` merge are gone too; the relay never
calls `post.comments.get`, `record.json` is the record + `parent` only. Game-Express's
pre-existing post-page parser (`parse_reddit_rss`, old chain) is untouched.

## Game-Express (hand-off patch refreshed, base `main` @ `4973dc6` / PR #137)

- `reddit_intake.py`: `record_to_entry` sets `relay_complete = not needs_full_record(rec)`;
  relay entries carry `comments=[]` (the relay ships none).
- `reddit.py`: `items()` — `resolvable = not e.get("relay_complete")` guards both
  `resolve_post()` calls; `program_post()` — `detail = dict(e)` for `relay_complete`
  candidates. Zero redlib / reddit.com requests for a relay-served game, title-only posts and
  the Special-Program backup lookup included.
- `tests/test_reddit_intake.py` gains `test_relay_008_complete_records_need_no_resolve`
  (7 blocks now); docs (SOURCES, CHANGELOG, PRIVACY) updated. Verified on a fresh `--depth 1`
  clone of `4973dc6` with plain `git am` (intake 7/7, smoke 628/628, ruff) and inside its
  `sync_tree()` production checkout. The hand-off doc's apply step now says plain `git am`
  (`--3way` cannot work on a shallow clone).

## Tests

- `tests/test_smoke.py`: 9 `r104` guards — no CDN read for `opCommentCount`-only records;
  `relay_complete` / `relay_stats` on the base; the pipeline end-to-end with every proxy down
  (two native photos, Reddit's counts, **0** archive / redlib calls) versus a cut record (archive + redlib still asked);
  the retraction seatbelt (re-checked post: 0 listing/probe requests, unknown post: 1 each);
  source wiring of every gate; the Devvit 0.0.8 constants; the OP-comment removal (no symbol,
  no Variable, no card line). The round-101 liveness guard now expects `relay-listing` for
  every clean relay record (it encoded the Arctic path); the old section-5 OP-comment checks
  are gone.
- All three suites ALL PASS here and in a `sync_tree()` production checkout; Devvit
  `npm test` (tsc, biome, 27 unit tests, esbuild) green.

## Owner steps after merge

Zip → `npx devvit upload` (0.0.8 code → Reddit **0.0.5**, done 2026-11-02 after switching to
`npx devvit login --copy-paste`; see `DEVVIT_SETUP.md` §3 step 4 / §5) — settings persist,
nothing else changes. Both repos' readers accept old and new records alike, so upload order does not
matter. Activation of the readers is unchanged: secret `DISCORD_BOT_TOKEN` + Variable
`INTAKE_CHANNEL_ID` (`docs/DEVVIT_SETUP.md` §9/§10).
