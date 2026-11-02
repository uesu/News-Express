# Round 101 (2026-11-02) — the Devvit relay becomes the primary Reddit listing

## Provenance

1. **Reddit's timeline.** RSS feeds are retired on **2026-11-13**; anonymous `.json` has answered
   403 from datacenter IPs since 2026-10-20 (every production run logs
   `post JSON HTTP 403 → native mode`); unregistered access is removed on 2027-01-12 (which
   ends the redlib fleet — `REDLIB-REACH 0–1/26` is already the norm); the public Data API
   closes in 2027-03. The engine's discovery chain (combined RSS → per-subreddit RSS/redlib →
   Arctic Shift sweep) loses its first two legs within eleven days.
2. **Phase A (PRs #97–#107).** The Devvit app *Gaming Express* (`devvit/gaming-express/`,
   Reddit version 0.0.4) runs on Reddit's own servers, polls `/new` of twelve subreddits and
   three publisher accounts every minute, and writes one fenced-JSON record per post into the
   private Discord channel `#reddit-intake`. Live since 2026-11-01; steady poll line
   `poll: 12 subs, 3 users, 375 fetched, 0–1 sent, 374–375 seen, 0 failed`.
3. **Owner direction (2026-11-02).** "The relay becomes the main engine for News-Express
   Reddit; keep the RSS/redlib/Arctic engines as backup; implement it as soon as possible —
   we don't need to wait for three days." The card itself (Components v2, `build_v3_payload`)
   must not change.

## What changed (engine: `testing area/reddit_main_v3.py`)

### Discovery order

```
INTAKE_READER=primary (default)
   fetch_intake_records()  ── GET discord.com/api/v10/channels/<INTAKE_CHANNEL_ID>/messages
   │                            ?limit=100&after=<snowflake(now − INTAKE_LOOKBACK_SECONDS)>
   │                            Authorization: Bot <DISCORD_BOT_TOKEN>   (paged, ≤ 8 pages)
   ├─ ok (HTTP 200, newest message younger than INTAKE_STALE_SECONDS)
   │     → the relay IS the listing: combined feed, per-subreddit fallback and the archive
   │       sweep are skipped; combined_fetch_status = "relay"; log `INTAKE: relay ok — …`
   └─ anything else (off / unconfigured / http_<n> / error / empty / stale)
         → log ONE `INTAKE-FALLBACK: relay <status> (<why>)` line and run the pre-round-101
           chain exactly as before. Records the relay DID deliver are still added (dedup by key).
INTAKE_READER=shadow   old chain decides; relay read and compared (`INTAKE-SHADOW: …`).
INTAKE_READER=off      channel not read; log `INTAKE: reader off`.
```

Pipeline after discovery is **unchanged**: dedup cache, fresh hold, flood cap, pending
throttle, removed-post gate, `verify_archive_post_live` (feed_ok=True, like RSS),
`candidate_liveness_verdict`, `resolve_post_media` (proxies, redlib gallery, native extraction,
Arctic hop for crossposts), media-wait / partial-gallery gates, `build_v3_payload`,
continuations, retraction, MEDIA-HEAL.

### The relay entry (`_IntakeEntry`, `intake_base_data`)

- Feed-shaped duck type (`link`, `title`, `author`, `published_parsed`, `.get("content")`), so
  `collect()` and every `entry.get(...)` consumer work untouched. **Not** an `_ArcticEntry`:
  `feed_ok`, the Arctic pending throttle and the snapshot-source rules keep their meaning.
- Base data is built by `intake_base_data` (the `entry_to_base_data` twin): the body is Reddit's
  raw markdown and takes the **`_clean_selftext`** path (one unescape, the same path the
  post-JSON selftext takes); the title is unescaped once (API-escaped `&amp;`);
  `content_html` is a synthetic RSS-shaped anchor list (media URLs + the `[link]` destination +
  `[comments]`) so `extract_native_media`, `extract_outbound_url` and the gallery hint see what
  they saw in RSS; `vred_id` from `url` / `media[]` / body; `crosspost_parent_id` from `xpost`
  (`resolve_crosspost_source` gains an id-only `relay-parent-id` source that the media resolver
  turns into a path through its existing archive hop).
- `bodyTruncated: true` (relay message budget) → the base body is left **empty** so the existing
  archive/proxy fill-in recovers the full text; if nothing served it, `main()` uses the relayed
  part (`relay body was truncated and no source served the full text`).
- Replay semantics: a record stays in the channel, so a held post (media_wait, liveness,
  pending approval…) re-enters each run while it is inside the lookback window — the same
  "listed again, re-probed again" behaviour the 100-entry RSS window gave. A replayed record is
  **not** a restore: `_pending_throttle_skip` treats it like an archive resurface for the
  never-re-check reasons. Older holds are reclaimed by the round-98 archive path as before.

### Liveness (the part that needed thought)

The round-98 stale-snapshot override needs a post to be **listed by Reddit's own feed for three
consecutive runs**. A replayed relay record would satisfy that for a post Reddit removed two
minutes after the relay saw it — so relay entries carry provenance **`relay`**, never
`reddit-native`, and cannot build the streak. In its place, two stateless rules in
`candidate_liveness_verdict`:

| Evidence | Verdict | Source |
| --- | --- | --- |
| relay record `removed` is set (`removedByCategory` at relay time) | `removed` — queue category → `pending approval`, otherwise `removed by moderators/filters` | `relay-record` |
| archive row says removed, but its `retrieved_on` is **older** than the relay sighting (message snowflake, 20 s margin) | `live` — Reddit's `/new` listed the post *after* the archive looked, i.e. the queue state was lifted | `relay-listing` |
| archive row says removed and is **newer** than the sighting | `removed` (unchanged) | `arctic-lookup` |
| archive clean / no row | `live` / `unverified` (unchanged) | `arctic-lookup` |

Arctic captures ~10 s after creation (`retrieved_on` is in every `/api/posts/ids` row, verified
2026-11-02 on `1xlgjkw`: created 1793572467, retrieved 1793572477), and a filtered post is not
in `/new` for a non-moderator, so a relay sighting after an archive "queued" row is exactly the
approval the round-98 override was guessing at from the feed streak. Neither new source is in
`_SNAPSHOT_SOURCES`, so the override logic itself is untouched for RSS candidates.

### Everything else

- Run result: `intake` object (`status, mode, records_in_window, records_for_this_engine,
  newest_age_seconds, pages, detail`, plus `candidates` / `relay_only` / `old_chain_only` when
  applicable). No ids, no token. `_effective_settings()` gains `intake_reader`,
  `intake_configured`, `intake_stale_seconds`, `intake_lookback_seconds`.
- Summary: the existing **settings line** (printed verbatim by the summary step) gains a
  trailing `intake primary (relay ok; 12 record(s), newest 40 s)` /
  `intake primary (relay STALE → old chain; …)` fragment — the summary step's `run:` block is
  **not** grown (14,719 dedented chars; cap 16,000; limit 21,000).
- Media gates: the media-wait hint fires when the relay record lists media and no source served
  any; the partial-gallery gate compares against `len(media)` for `/gallery/` records.
- Workflow `env:` (`reddit_monitor.yml`): `DISCORD_BOT_TOKEN` (secret), `INTAKE_CHANNEL_ID`,
  `INTAKE_READER`, `INTAKE_STALE_SECONDS`, `INTAKE_LOOKBACK_SECONDS` (Variables).
  `.env.example` documents them. The bot token travels only in the `Authorization` header and
  is never logged or written.

### Corrections from the first live records (owner screenshots, 06:27–07:15 PHT)

- **Inline rich-text images** (`1xlgs9j`, `1xlh3fw`: `media: []`, preview.redd.it URLs in the
  markdown body) — Reddit's RSS carried those as anchors, so `extract_native_media` found them;
  the synthetic `content_html` now also anchors every redd.it image URL in the body (after
  `media[]`, deduplicated), so text posts with pasted images keep their gallery.
- **Markdown escapes inside bare URLs** (`1xlhem9`: `https://x.com/minmyouk\_xx/status/…`) —
  Reddit's renderer resolves `\_` before RSS/HTML consumers see it; raw markdown (relay and
  archive bodies) still carries it and Discord's autolink breaks at the backslash.
  `_unescape_markdown_in_urls` (in `_clean_plain_body`) strips backslash escapes inside **bare**
  URL tokens only; prose escapes and `[label](url)` targets stay as written (the round-99
  operator-approved card is byte-identical).
- Relay latency observed: `1xlhem9` created 1793574792 → channel message 07:15 (≈2 min, one
  2-minute poll); galleries arrive with the full `media[]` (3/3 for `1xlhem9`, 3/3 for
  `1xlh8pv`); `poll:` lines steady at `0 failed, 0 bootstrapped`.

## Operator steps (owner; the engine does nothing new until both exist)

1. Discord developer portal → New Application → Bot → **Reset Token** (copy once) → *Privileged
   Gateway Intents* → enable **Message Content Intent** (webhook-authored messages are not
   readable without it) → OAuth2 URL Generator: scope `bot`, permissions **View Channels** +
   **Read Message History** → open the URL, add the bot to the Citlali News server.
2. `#reddit-intake` → channel permissions → add the bot (or its role) with View Channel + Read
   Message History (the channel is private, so server-wide permissions are not enough).
3. Prod repo `uesu/7jkxmy9nvbc` → Settings → Secrets → `DISCORD_BOT_TOKEN`; → Variables →
   `INTAKE_CHANNEL_ID` = the channel id (Developer Mode → right-click channel → Copy ID).
4. Watch one run: the summary's settings line ends with `intake primary (relay ok; …)` and the
   log has `INTAKE: relay ok — N record(s) …`; `Combined fetch status: relay`. Before step 3 every
   run logs `INTAKE-FALLBACK: relay unconfigured …` and behaves exactly as before.
5. Rollback without a code change: Variable `INTAKE_READER=off` (or `shadow` to keep
   comparing).

## Known limits (deliberate, documented)

- Health = "newest message age". A quiet night across all twelve subreddits can exceed 30 min
  and flip one run to the old chain — harmless (additive), and the relay's next record flips it
  back. A relay heartbeat record (0.0.6) would make the signal exact; not needed to ship.
- A post removed *after* the relay saw it and *never* re-captured by the archive is caught by
  `verify_archive_post_live` (proxies) as before; the relay adds no new way to post a removed
  post and removes one (the feed streak) for its own entries.
- Long bodies: the relay's single-message budget truncates bodies above ~1.5 k characters;
  recovery is the existing archive/proxy fill-in. A relay-side attachment for long bodies is a
  possible 0.0.6 item.
- Game-Express is unchanged (no handoff yet, per the owner).

## Proofs

`tests/test_smoke.py` → `r101:` guards (parser, entry/base, truncated body, liveness table,
provenance/streak, throttle, reader against a fake Discord API — ok/stale/empty/403/
unconfigured/off, paging with `after`, token only in the header — discovery order in
`main()`, defaults and workflow wiring, settings-line reporting, media gates). Offline
`DRY_RUN` simulations of `main()` with a mocked channel: primary-ok (combined/fallback/archive
skipped, 4 dry-run deliveries incl. the truncated-body fallback), stale (old chain + union),
shadow (compare only), HTTP 403 and off (old chain, no Discord call in `off`).
Suites: `test_smoke.py`, `test_reddit_signals.py`, `test_twitter_media.py` ALL PASS, also inside
a `sync_tree()`-generated production checkout.
