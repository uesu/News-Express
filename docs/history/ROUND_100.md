# Round 100 (2026-11-01) — the X media heal outlives the run

## Provenance

1. **Production run `Twitter Feed Monitor #12739`** (`uesu/wvkhabh2s22`, 2026-11-01 11:00Z),
   tweet `Wuthering_Waves_2116847734669873623` — the Wuthering Waves LA concert video (5:04,
   source fxtwitter; renditions 3840x2160 `4jaj9Ng2KIzvEPtb.mp4` ≈ 813 MB and 1920x1080
   `KQTNFf7vricoapOP.mp4` ≈ 235 MB). Relevant log lines:

   ```
   Video downgraded: 813MB -> 235MB variant
   V3 Posted: Wuthering_Waves_2116847734669873623 (lang=en | source=fxtwitter)
   MEDIA-HEAL queued for …: Discord returned 1 heal-eligible media item(s) with no dimensions/content-type
   MEDIA-HEAL …: still unresolved after edit #1 (1 item(s)).   … #2 … #3 … #4
   MEDIA-HEAL …: media still unresolved after 4 edit(s); playback remains unverified.
   ```

   The posted payload carried the 1920x1080 mp4 as the only gallery item plus the note
   `🔽 Original video is ~813 MB — showing a smaller version (~235 MB) so it plays in Discord.
   [▶️ Watch full quality on X](…)`. Discord's created-message echo had
   `width: 0, height: 0, content_type: ""` for the tile.

2. **Operator screenshots.** `#wuwa-news` at 19:42 PHT (40 min after the post): the card is
   complete but the gallery shows **"Image failed to load"**. At 19:43 the operator restored the
   message in Discohook Utils and pressed *Edit* **without changing anything**; at 19:56 the
   same card shows the video player at 0:10 / 5:04. Pasting the 1920x1080 URL as a plain
   message also played.

3. **Operator direction.** Other 4K videos have played in the gallery before ("it only works
   sometimes"), so the size-based downgrade to 1080p is the right behaviour and must stay. The
   defect is the heal budget: four edits in one run (~3 minutes) is too little for a cold
   proxy that needed ~45 minutes. The official accounts do not post every minute, so the
   cron-job.org cadence (every 10 minutes) can carry the edit into later runs.

## Root cause

The round-47 heal was designed for a proxy that is cold for *seconds*: it re-sends the identical
payload up to four times, 45 s apart, and then only logs a warning. Its state lived in memory, so
the warning was the end of the story — nothing in a later run knew the message existed. The
cure itself was right (an identical edit is exactly what the operator did by hand); it was
simply given up on too early, and the engine had no way to try again.

## What changed

### Engine (`testing area/twitter_v3.py`)

- `heal_unresolved_media()` keeps its bounds (revalidation GET, ≤ 4 identical PATCHes,
  `MEDIA_HEAL_DELAY_SECONDS` apart, concurrent, after the posting loop) and now **returns** the
  `(webhook_url, message_id, payload, key)` tuples that were still unresolved when the edits
  ran out. Resolved, skipped-after-revalidation and terminal (401/403/404) cases return
  nothing.
- New `carry_over_media_heal(session, records, leftovers, now)` — one pass per run:

  | carried record (from earlier runs) | action |
  |---|---|
  | older than `MEDIA_HEAL_CARRY_HOURS` | dropped, `MEDIA-HEAL CARRY <key>: … giving up` |
  | no webhook for its account any more | dropped |
  | GET 200 and no unresolved eligible media | dropped, `resolved on its own (N min after posting)` |
  | GET 401 / 403 / 404 | dropped (message deleted or webhook changed) |
  | otherwise | **one identical PATCH**; resolved → dropped (`media resolved after carried edit #n (N min after posting)`); still cold or HTTP error → kept with `runs + 1`, `last_checked = now` |

  Oldest records first, at most `MEDIA_HEAL_CARRY_MAX_PER_RUN = 20` per run (the rest wait
  untouched). This run's leftovers are then added as new records. With
  `MEDIA_HEAL_CARRY_HOURS = 0` nothing is added or touched. Malformed records are discarded.
- Record shape (`media_heal_record()`):
  `{"account", "message_id", "payload", "first_seen", "last_checked", "runs"}` — the
  **account**, from which `get_webhook_for_account()` re-derives the webhook on the next run.
  **No webhook URL is ever written** (the file is committed to the repository).
- `load_media_heal_pending()` / `save_media_heal_pending()`: `media_heal_carry.json`, sorted
  keys, 2-space indent, trailing newline — byte-identical to what `merge_monitor_caches.py`
  writes, so neither a quiet run nor a recovery merge creates churn. Written every run, even
  `{}`, so the workflow's `git add` always finds it.
- `main()`: `heal_leftovers = await heal_unresolved_media(…)` → `carried =
  load_media_heal_pending()` → `carry_over_media_heal(…)` → `save_media_heal_pending(carried)`.
  All after the posting loop; posting latency is unchanged.
- New setting `MEDIA_HEAL_CARRY_HOURS = max(0, _env_int("MEDIA_HEAL_CARRY_HOURS", 6))`
  (empty-string safe, round-49b pattern).

### Workflow (`.github/workflows/twitter_monitor.yml`)

- `MEDIA_HEAL_CARRY_HOURS: ${{ vars.MEDIA_HEAL_CARRY_HOURS }}` in the monitor step's `env:`
  (round-42 invariant: every Variable is wired explicitly).
- Persist step: `if [ -f media_heal_carry.json ]; then git add -f media_heal_carry.json; fi`
  after `git add -f posted_tweets.json` (normal and recovery path), the file is copied aside
  with the dedup cache before `git reset --hard`, and `merge_monitor_caches.py` receives both
  files. The step script grows from 2,748 to ~3,000 characters (cap 16,000, GitHub 21,000).
- `.gitignore` lists the file like the other caches. Both files reach production through
  `sync_prod.py` (workflows and `.gitignore` are in its allowlist).

### Why the file is not called `pending_*`

`merge_monitor_caches.py`'s hygiene rule removes, from any **dict file whose name contains
"pending"**, every key that the merged posted **list** already contains. The carry records are
keyed by the dedup key (`Wuthering_Waves_2116847734669873623`), which *is* in
`posted_tweets.json` — a `pending_media_heal.json` would have been emptied on every recovery
merge. `media_heal_carry.json` is merged as a plain dict (newest `last_checked` wins), which
the suite proves by running the real script.

### What did NOT change

- Video handling: `VIDEO_SIZE_LIMIT` (256 MiB / opt-in 350 MiB), `GALLERY_VIDEO_LIMIT`, the
  variant downgrade, the GIF chain, the card layout and notes.
- In-run heal bounds and defaults (`MEDIA_HEAL`, scope `video`, 45 s, 4 attempts) and the
  round-70 revalidation.
- Nothing is posted twice: the carry-over only edits the message it already posted.
- The Reddit engine, the Reddit workflow, `sync_prod.py` and every cache file's contents.

## Expected log shape (next runs after a carried message)

```
MEDIA-HEAL Wuthering_Waves_…: media still unresolved after 4 edit(s); playback remains unverified — carried over to the next runs.
MEDIA-HEAL CARRY Wuthering_Waves_…: recorded for the next runs (up to 6 h).
…(next run, ~10 min later)…
MEDIA-HEAL CARRY Wuthering_Waves_…: still unresolved after carried edit #1 (12 min); next run tries again.
MEDIA-HEAL CARRY: 1 carried message(s) checked — 0 resolved on their own, 0 healed by this run's edit, 1 still pending, 0 given up, 0 dropped.
…(a later run)…
MEDIA-HEAL CARRY Wuthering_Waves_…: media resolved after carried edit #4 (47 min after posting) — the media now renders.
```

## Guards

- `tests/test_twitter_media.py` section 4b — 39 `r100` checks (see the CHANGELOG entry for the
  list; they include a real `merge_monitor_caches.py` invocation on a temp repo).
- `tests/test_smoke.py` — eight `r100` guards: defaults and unchanged caps, Variable wiring,
  persist-step wiring (both paths), `.gitignore` + sync allowlist, no-webhook record, the
  `pending` naming rule, main() ordering, and the round-49b empty-Variable default.
- All three suites ALL PASS in the dev checkout and inside a `sync_tree()` production checkout.

## Operator notes

- Nothing to configure: the carry-over is on with a 6-hour window. Set the repository Variable
  `MEDIA_HEAL_CARRY_HOURS` to lengthen/shorten it or `0` to switch it off.
- The first production run after this merge commits an empty `media_heal_carry.json` once
  (the usual `auto: update posted_tweets.json cache` commit); after that only real carry
  records change it.
- A message fixed by hand in Discohook is recognised on the next run (`resolved on its own`)
  and dropped without an edit.

## Rollback

Revert the commit (or set `MEDIA_HEAL_CARRY_HOURS=0`). A leftover `media_heal_carry.json` is
inert — nothing reads it once the carry-over is off.
