# Round 103 (2026-11-02) — the relay is the complete Reddit source (relay 0.0.7)

## Provenance

Owner, after round 102: *"let's have it a complete feature which is the Reddit official
Devvit — to prepare in advance just in case the old feature is down, except for the Reddit
proxies which are fine; keep the current structure; same on Game-Express; so we don't have
to create a new PR in the future when things go down."*

After round 101/102 the relay covered **discovery** completely, but three things still
leaned on the old sources per post: bodies above the relay's 1,900-character message
budget, crosspost parents (archive hop), and liveness (archive snapshot / mirrors). Round
103 moves those into the relay. The redlib / reddit.com / Arctic chain stays untouched as
the fallback; the vxreddit / embedez / embeddit video proxies stay for muxed audio.

## Relay 0.0.7 (`devvit/gaming-express`, uploads as Reddit 0.0.6)

1. **`record.json` attachment.** Every record message is a multipart webhook upload:
   `payload_json` = the trimmed fenced record exactly as before (still `v: 1`, new optional
   keys `full`, `mediaTruncated`, `edited`, `revision`, `xpostPermalink`, `video`), `files[0]`
   = the untrimmed record plus `parent` (the crosspost parent as a nested record, one
   `getPostById` only for crossposts). Built by hand as one string (`toMultipartBody`) so it
   needs nothing beyond `fetch(url, {body})`. If Discord/Devvit refuses the form (4xx), the
   same record is sent as plain content — the pre-0.0.7 path — and three refusals in a row
   pause the attachment for an hour. A post can never be lost to the attachment.
2. **Post-delivery re-check.** Delivered ids go into a sorted set (`sent:z`, score =
   created). Each poll re-checks posts that crossed a stage (10 min, 30 min, 2 h, 6 h;
   `dueStage`), ≤ 20 per poll, inside a 20-second soft deadline, and writes one batched
   `v: 2` message: `{v:2,kind:"update",at,posts:[{id,sub,age,stage,removed,deleted,edited,
   spoiler,…,locked,score,comments}]}`. The first look is always reported (that is the
   readers' positive "still listed" verdict); later looks only when `removed / deleted /
   edited / spoiler / … / locked` changed (`shouldReport`). A 404 on the re-check is reported
   as deleted.
3. **Edits.** When a re-check finds `edited` and the body hash changed (`bh:<id>`), the
   complete record is re-sent as a `v: 1` record with `revision` ≥ 2. Readers keep the newest
   message per id, so it supersedes without any reader change.
4. `v: 2` was chosen for updates on purpose: the round-101/102 readers accept `v: 1` only and
   ignore update messages entirely, so upload order does not matter.

Unit tests (`relay.test.ts`, 23 pass): round-trip of the new keys, `mediaTruncated`
flagging, multipart structure (boundary never inside the parts, attachment untrimmed while
the inline record is trimmed), stage schedule, report rule, batch splitting within the
budget with no item lost, body hash.

## News-Express reader (`testing area/reddit_main_v3.py`)

- `parse_intake_update()` (v2), `_intake_attachment_url()` (cdn.discordapp.com /
  media.discordapp.net only), `apply_intake_full_record()` (same-id check; body, media,
  parent, `xpostPermalink`, `video`), `_intake_needs_full_record()`.
- `fetch_intake_records()`: relay messages of both kinds keep the relay fresh (never other
  bots); the newest look per id is kept in `_INTAKE_UPDATES` and on each record as
  `_update`; cut records / crossposts are completed from `record.json`, ≤
  `INTAKE_ATTACHMENT_FETCHES` = 10 per run, failures leave the round-101 behaviour. A window
  with only re-check messages is `empty — relay alive (N re-check message(s)) but no new
  post`, not the Intent hint and not stale.
- `candidate_liveness_verdict()`: `relay_update_verdict()` is consulted **before** the
  record's own `removed` and before the archive lookup — *still listed* ⇒ live, removed /
  deleted ⇒ hold, queue category ⇒ pending approval; source `relay-update`, zero requests.
- `retract_dead_posts()` (seatbelt, `RETRACT_DEAD_POSTS` off by default): the relay verdict
  (`relay_removal_reason_for`) before the mirror/proxy probe.
- `intake_base_data()`: `crosspost_orig_path` from `xpostPermalink` when the relay names it;
  `intake_content_html()` anchors the parent's media when the crosspost has none of its own.
- Summary: `intake primary (relay ok; N record(s), newest S s, U re-checked, C completed)`;
  run result gains `update_msgs`, `updates`, `completed` (no ids).

Guards: ten `r103` checks in `tests/test_smoke.py` (parser, freshness from updates, latest
look wins, verdict table, wiring order, completion incl. wrong-post / missing attachment /
no-request-for-complete-records, the 10-per-run bound, edit supersession, crosspost path +
parent media, summary line, relay-alive detail).

## Game-Express (hand-off patch refreshed)

`gamexpress/sources/reddit_intake.py`: `parse_intake_update`, `attachment_url`,
`needs_full_record`, `apply_full_record`; the reader completes cut records / crossposts from
`record.json` (`source="intake-cdn"`, no token, ≤ 10), drops posts whose latest re-check says
removed or deleted, lists a post the re-check shows approved, keeps the newest record per id
(edits), reports `N re-checked, N completed from record.json` on the step-summary line; entries
gain `edited` and `crosspost_url`. `tests/test_reddit_intake.py` gains
`test_relay_007_updates_attachments_and_edits`. Patch:
`docs/handoffs/game-express-intake-reader.patch` against Game-Express `main` @ `3af83ff`
(smoke 626/626, suite 6/6, ruff clean, prod-shape checkout).

## What still touches the old sources, by design

- Video **audio**: `v.redd.it` renditions are video-only; the vxreddit → embedez → embeddit
  ladder stays (owner: "the proxies are fine").
- Game-Express publisher **follow-up comments** (merged from the post page / mirrors) — not a
  relay feature; listed as the only open roadmap item in `DEVVIT_SETUP.md` §10.
- Everything else runs on relay data alone for a relay-served post; the old chain remains the
  automatic fallback for any state other than `relay ok`.

## Owner steps

1. Re-zip → `npx devvit upload` (0.0.7 → Reddit 0.0.6). Existing settings persist. The poll
   line should read `… bootstrapped; recheck N looked, N update msg, N re-sent`.
2. Nothing else: the readers accept 0.0.6 and 0.0.7 messages alike, and activation is still
   the two settings (`DISCORD_BOT_TOKEN`, `INTAKE_CHANNEL_ID`) in both prod repos.
