# Round 105 — first live relay-primary run: the summary speaks relay (2026-11-02)

**Trigger.** Production run `7jkxmy9nvbc` #12256 (11:20Z) — the first run with `DISCORD_BOT_TOKEN`
+ `INTAKE_CHANNEL_ID` set and relay **Reddit 0.0.5** writing to `#modlogs`:

```
INTAKE: relay ok — 0 record(s) for this engine (2 in window, 1 page(s), newest 263 s,
2 re-checked, 0 completed from record.json) — relay is the listing; combined feed /
fallback / archive sweep skipped.
Combined fetch status: relay · Monitor runtime: 3 s · 0 Reddit/redlib/Arctic requests
```

Engine behaviour was exactly as designed (switch-over complete, old chain idle). The only
blemish was the **run summary**, which still described the run in old-chain words:

| Summary line in #12256 | Problem |
| --- | --- |
| `Combined-feed entries: 0` | there was no combined feed — the relay was the listing |
| `Subreddits missing from the combined feed: AnantaLeaks, … (archive attempt below)` | nothing was missing (the six subreddits simply had no new post in the 6 h window) and no archive attempt follows in relay mode |
| `Feed fallback: not attempted (combined succeeded)` | nothing "succeeded"; the fallback is skipped because the relay is the listing |

## Change (summary step of `reddit_monitor.yml` only; engine untouched)

When `combined_fetch_status == "relay"`:

- `Relay records for this engine (6 h window): N` replaces `Combined-feed entries`;
- `Subreddits with no new post in the relay window: … (quiet, not missing; no archive attempt)`
  replaces the "missing … (archive attempt below)" line;
- `Feed fallback: not attempted (relay is the listing)`.

RSS runs keep every old word (guarded). The step grows 14,720 → 15,106 chars (cap 16,000 /
21,000). No new reporting call, no engine change, no cache change.

## Not changed on purpose

- **No relay heartbeat.** `status=stale` needs 30 min without *any* relay message (record or
  re-check) across all 12 subreddits + 3 accounts; `status=empty` needs 6 h without a single
  record. Both are practically unreachable while Reddit is up, and both fall back to the old
  chain for that one run and return to the relay on the next — the designed backup, not a gap.
- The relay keeps writing records of the Game-Express targets into the same channel; this
  engine counts them (`2 in window`) and acts only on its six subreddits.

## Tests

`tests/test_smoke.py`: `r105` renders the real summary step with a run-result shaped like
#12256 and asserts the relay wording (and that the r96 RSS-shaped run still prints the old
lines). All three suites ALL PASS here and in a `sync_tree()` production checkout.
