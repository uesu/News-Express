# Round 102 (2026-11-02) — shared intake channel, 5-minute relay, Game-Express hand-off

## Provenance

1. **Owner direction (2026-11-02, after round 101 went live in fallback mode):** relay poll
   2 → 5 minutes ("to be on the safer side", matching the 5-minute engine crons); verify the
   intake structure for every media kind so that activation has "no bugs, no stale, no edge
   cases, no errors"; the relay webhook moves from `#reddit-intake` into the shared `#modlogs`
   channel (other bots write there); deliver the Game-Express reader now as a PR hand-off;
   audit README / privacy / ToS / `.gitignore` / `.env.example` / every md file and in-file
   comment for stale information; activation must need exactly two settings.
2. **What a shared channel breaks in the round-101 reader.** It paged *oldest-first* with
   `after=<snowflake(now − 6 h)>` and measured freshness on the newest *message*. In `#modlogs`
   a busy afternoon (Wick/SassGuard lines) could fill the 8 × 100 budget before reaching the
   newest relay records, and a fresh moderation line would have kept a paused relay "ok" with
   zero posts — the fallback would never fire. Both were real, not theoretical: the owner's
   channel carries hundreds of messages on event days.

## What changed

### Devvit relay `gaming-express` 0.0.6 (uploads as Reddit 0.0.5)

- `devvit.json` scheduler cron `*/2 * * * *` → `*/5 * * * *`.
- `MAX_SENDS_PER_POLL` 10 → 15 so the per-minute Discord ceiling is unchanged (3 sends/min).
- No record-format change (`v: 1`). Relay listing/readme unchanged (generic, no repo links).

### Engine `testing area/reddit_main_v3.py` — `fetch_intake_records()`

- **Newest-first paging.** `GET …/messages?limit=100[&before=<oldest id of previous page>]`;
  a page is cut at the lookback cutoff snowflake, which also ends the paging. The 800-message
  budget can therefore only shorten the look-back, never hide fresh records.
- **Freshness from relay records only.** `newest_age` is the age of the newest message whose
  `content` parses as a relay record. Other bots' messages, and webhook messages whose
  `content` arrives empty (Message Content Intent missing), never vouch for the relay.
- **New `empty` detail.** Messages present but no record: `"N message(s) in the last 360 min but
  none is a relay record (Message Content Intent off, wrong channel id, or the relay webhook
  points elsewhere)"` — the exact case after a channel move with a stale `intakeWebhook`.
- Everything downstream of `fetch_intake_records()` (entry adapter, holds, liveness, card) is
  byte-identical to round 101.

### Game-Express hand-off

`docs/handoffs/GAME_EXPRESS_INTAKE_READER.md` + `docs/handoffs/game-express-intake-reader.patch`
(`git am`-able against Game-Express `main` @ `1d133c3`): `gamexpress/sources/reddit_intake.py`
(reader with the same rules as above), six-line wiring in `RedditClient._gather_listing()`,
settings, `validate` line, step-summary line, `tests/test_reddit_intake.py` (5 blocks built from
the first live records), CI/bump gates, docs/policies. Verified in this sandbox: that suite,
Game-Express smoke 626/626, the four other test files, `ruff`, and the same inside a
`sync_tree()` production-shape checkout. Not pushed anywhere — the Game-Express session applies
it and opens the PR; the owner merges.

### Documentation audit

`README.md`, `AGENTS.md`, `PRIVACY_POLICY.md`, `TERMS_OF_SERVICE.md` (effective date
2026-11-02, relay/reader paragraphs, bot REST row), `.env.example`, `docs/DEVVIT_SETUP.md`
(5-minute cadence, `#modlogs` guidance, 0.0.6 row, §9 troubleshooting rows for the new hint,
§10 step 3 closed), `devvit/README.md`, `docs/REPOSITORY_TRACKING.md`, workflow and engine
comments: every `#reddit-intake` / "every 2 minutes" / "Game-Express does not read it yet"
statement replaced. `.gitignore` reviewed — nothing to add (no new generated files; the patch
file is a deliverable and is tracked on purpose).

## Verification

- `tests/test_smoke.py`: round-101 reader mock now serves Discord's real newest-first order
  with `before`; four `r102 reader:` guards (shared-channel age, other bots chatting while the
  relay is silent → `stale`, empty `content` → `empty` + hint, old messages dropped and paging
  ends). Three suites ALL PASS, also inside the `sync_tree()` production checkout.
- Devvit: `npm run lint` + `npm test` pass.

## Owner steps (unchanged two-setting activation)

1. Re-upload the relay from the zip: `npx devvit upload` (0.0.6 → Reddit 0.0.5), then
   `npx devvit settings set intakeWebhook` with the `#modlogs` webhook URL (settings persist).
2. Secret `DISCORD_BOT_TOKEN` + Variable `INTAKE_CHANNEL_ID` (= `#modlogs` id) in
   `uesu/7jkxmy9nvbc` **and** `uesu/8mqzv4k2n7c` (after the Game-Express PR is merged).
3. cron-job.org Reddit trigger 10 → 5 minutes.
