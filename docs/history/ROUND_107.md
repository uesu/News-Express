# Round 107 — a held post that Reddit lists again through the relay is a restore (2026-11-02)

## Live case

`r/Zenlesszonezeroleaks_` **1xlrj90** "Full M0r1 Sunbringer Jufufu(UP!) Robin | 65k 3.4.2 New
Boss (2:58)" — video post, flair Showcases, spoiler.

| time (UTC) | what happened |
|---|---|
| 08:11:03 | post created; it sat in the subreddit's mod queue (not in `/new`) |
| 08:20:24 | old chain (pre-relay): the archive sweep saw the row with a removal state → `pending_reddit.json` `Zenlesszonezeroleaks__1xlrj90 = {reason: removal_notice, source: arctic}` |
| ~12:35 | mods approved it; comments start ("11m ago" at 12:48) |
| 12:36 | relay (which lists a post only while Reddit's `/new` lists it) sent the complete record: `removed: null`, `full: true`, video `CMAF_720.mp4` + HLS |
| 12:40, 12:45, 12:50, 12:55 | every run: `INTAKE: relay ok — 1 record(s)` … `1 known-pending` (`Known-pending by reason: removal_notice: 1`) — **no card**, while the post sat live with 24 votes / 10 comments |

## Cause

`_pending_throttle_skip` (round 32): a hold with a never-re-check reason (`removal_notice`,
title/body marker, "removed by moderator", …) is only reopened when the post "re-enters via
RSS" — RSS re-listing a post is Reddit's own proof of a restore. Round 101 then classified
every relay record as a replay from the channel window ("not a restore → skip"), because the
same message is read again on every run. That was right for the replay and wrong for the
first sighting: in relay mode there is no RSS, so a post held by the old chain (or by the
proxy-body notice gate) and later approved by the mods could never come back until the hold
aged out of the 48 h window.

## Fix

`relay_listed_after_hold(pend, entry) -> float | None` (`testing area/reddit_main_v3.py`,
next to `_pending_throttle_skip`): the relay message is a restore when it is **newer than the
hold's last look** (`max(first_seen, last_checked)`) and the relay itself vouches for the
post — the record's `removed` is empty and its latest `v: 2` re-check (when there is one)
says not removed / not deleted. A clean re-check newer than the hold counts the same way
(Reddit's own current state); a record or re-check that says removed never does. A replay of
the message that produced the hold is older than `last_checked` by construction, so the
round-101 rule still holds for it. No request, bookkeeping on data already in hand.

- `_pending_throttle_skip`: relay entry → skip only when `relay_listed_after_hold` is `None`;
  Arctic resurfaces and the retryable-reason throttle are untouched.
- Main loop: one INFO line (`held as 'removal_notice' since N min, but Reddit's own listing
  (relay) vouches for it again — restore, full pipeline`), `run_stats["relay_restores"]`,
  `relay_restore_keys` (key, held reason, minutes held). The candidate then runs the normal
  pipeline: liveness `relay-listing` (live), `relay_complete` → proxies only, fresh hold,
  flood cap, dedup; on delivery the pending entry is popped as before.
- Summary step (`reddit_monitor.yml`, 15,106 → 15,557 chars; guard 16,000): new line
  `Held posts Reddit listed again (relay restore): N` + `restored: <key> — held as '<reason>'
  for N min`; in relay mode the suppression line reads `Known-rejected candidates (held
  earlier; no newer listing)` instead of "archive candidates". RSS-mode wording unchanged.
- `tests/test_smoke.py`: `r107` (five checks on the helper, the throttle and the main loop)
  and `r107b` (summary wording). Replayed against the live hold from `pending_reddit.json` and
  the live record: `listed_after_hold → 12:36:00Z (+4.3 h after the hold)`, throttle `False`,
  liveness `('live', …, 'relay-listing')`.

## What this does NOT change

- Removed posts stay removed: the relay must say `removed: null`, and a `v: 2` re-check that
  says removed/deleted wins. No proxy, mirror or archive text can unlock a hold.
- The 43 `removal_notice` holds the old chain left in `pending_reddit.json` are harmless:
  each either gets a newer relay record (→ restore) or ages out at 48 h; nothing is re-probed
  for them.
- Arctic is not consulted anywhere on this path. The round-98 reclaim (≤5 archive reads per
  run for *retryable* holds that no listing refreshes) is unchanged; in relay mode it only
  ever sees leftovers that slid out of the 6 h relay window.
- Game-Express: no equivalent defect. Its Reddit source keeps no hold memory (a removed post
  is simply not an item), reads `LOOKBACK_HOURS` (72 h) back, and a relay record newer than the
  last run is a plain new item. The hand-off patch
  (`docs/handoffs/game-express-intake-reader.patch`) was regenerated on GE `main` `71202ee4`
  (applies with `git am`, no conflicts) and now carries the cross-check test
  `test_round107_post_approved_from_the_mod_queue_hours_later_is_a_plain_new_item` (GE suites:
  intake 8/8, smoke 610/610, ruff clean).
- Devvit relay: nothing to change — it already detected the approval (the post entered `/new`
  at ~12:35Z and the record went out at 12:36Z with `score: 1, comments: 0`).

## Live result (production run #12276, 13:40Z — first run after the merge)

`Held posts Reddit listed again (relay restore): 1 — restored: Zenlesszonezeroleaks__1xlrj90 —
held as 'removal_notice' for 255.6 min` · `Known-rejected candidates (held earlier; no newer
listing): 0` · delivered `video/proxy: vxreddit, 1 item(s), LATENCY 329.4 min, held as
'removal_notice'` · liveness `relay-listing` · card = title, body (markdown kept), 720p video
with audio, `💬 36 👍 78`, created-time stamp, three buttons. `pending_reddit.json` no longer
holds the key; `posted_reddit.json` has it. The restore cost no archive, redlib or reddit.com
request.

## Verification

`python3 tests/test_smoke.py` ALL PASS · `tests/test_reddit_signals.py` 102 pass ·
`tests/test_twitter_media.py` ALL PASS · same suites in a `sync_tree()` production checkout.
