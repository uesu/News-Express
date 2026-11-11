# Round 113 — three reading fixes on relay cards: mobile/music YouTube hosts, Reddit's `\>` escape, scheme-less x.com links (2026-11-11)

Scope: `testing area/reddit_main_v3.py` — the reading path only (`YOUTUBE_RE`, and the line stage
`_line_stage` that both `_clean_plain_body` and `clean_rss_body` end in). No card structure, no
component, no marker, no button, no cache, no dedup, no Devvit, no X engine, no Game-Express change.
Post 112's spoiler flag is untouched (and its guards still pass).

## Operator direction (the three live cards)

| live post | what the operator saw | cause | fix |
|---|---|---|---|
| `1xquvvi` — `[3.4.3] M0W1 Kafka … 65K Kill` (r/Zenlesszonezeroleaks_) | YouTube button missing, no second bare-link message, while the card itself showed the thumbnail | the record's `url` is `https://m.youtube.com/watch?v=hXE0oHPFWAM`; `extract_youtube_id` already read an `m.`/`music.` host, but `YOUTUBE_RE` only matched `www.` / bare, so the URL selector returned `None` | the regex accepts `www.` / `m.` / `music.` (the id reader already did) |
| `1xt22os` — `[4.7 Release] Project Yatta Updates …` (r/HonkaiStarRail_leaks) | body showed `\>> Check here`; Reddit shows `>> Check here` | Reddit markdown escapes a literal `>` as `\>`; the author wrote `\>>`, so the raw markdown carries `\>>` and Discord keeps the backslash | the line stage unescapes `\>` **only when a `>` follows it** |
| `1xsunnc` — `Wuwa 4.0 login soundtrack (by Brantleaks)` (r/WutheringWavesLeaks) | body ended with dead text `x.com/hotakatoki/status/2120176561634635897` | the author wrote the URL without a scheme; Reddit auto-links it, Discord leaves it as text | a scheme-less `x.com` / `twitter.com` **status** URL gets `https://` |

## Change

| where | what |
|---|---|
| `YOUTUBE_RE` | host group `(?:www\.|m\.|music\.)?` — `extract_youtube_url`, `select_youtube_url`, the YouTube button, the thumbnail lookup and the separate link message all follow from this one pattern |
| `_REDDIT_ESCAPED_GT_RE` (new) | `\\(?=>)` — a backslash immediately followed by `>` is removed. **Doubled only**: the lookahead never touches a lone `\>` (which would otherwise turn `\> text` into a Discord quote), and the round-99 author-escaped spoiler opener (`\>!text!<`) is already restored to `>!` before this stage, so it is unaffected |
| `_SCHEMELESS_X_STATUS_RE` (new) | `(?<![\w./@-])(?<!]\()(?:www\.)?(?:x|twitter)\.com/<user>/status/<id>` → prefixed with `https://`. Word-boundary and `](` guards keep `abx.com/…` prose and markdown link targets byte-identical; `x.com/a` (no `/status/<id>`) is untouched |
| `_line_stage` | the two regexes run on the finished line, after the v.redd.it scrubbing, so both the RSS/HTML route and the relay/plain route get them |

Why the line stage: `_clean_plain_body` (relay / JSON / Arctic selftext) and `clean_rss_body`
(RSS, redlib, proxy bodies) both end in `_line_stage`, and the live card came from the relay path.
Fenced code blocks never reach it (they are not lines of the body text the cleaner keeps verbatim),
and nothing else in the pipeline rewrites a body after this point.

## Evidence reviewed

- `1xt22os` record (relay): `spoiler: false`, body `Everything updated to the latest version.` — the
  card's `\>> Check here` therefore came from the body text, not from a renderer.
- `1xsunnc` card JSON (operator): body line `x.com/hotakatoki/status/2120176561634635897` rendered
  as plain text, the `embedez` video tile above it played fine — only the link was dead.
- `1xquvvi` record (relay, in `#new-structure`): `"url":"https://m.youtube.com/watch?v=hXE0oHPFWAM"`,
  `spoiler: false`; card JSON (operator) has no YouTube button and no second message, while the
  sibling `Mukuro` card — `https://www.youtube.com/watch?v=hXE0oHPFWAM` — has both.
- `m.youtube.com` / `music.youtube.com` are the same watch pages as `www.`; `extract_youtube_id`
  reads all three (confirmed by unit call before the change).

## Not done, on purpose

- No new host handling beyond mobile/music YouTube: `youtube-nocookie.com` and `youtu.be`-with-timestamp
  shapes were not in any live card, and guessing at them would widen the pattern without evidence.
- No general "linkify every scheme-less URL": only the X/Twitter status shape the operator reported.
  A scheme-less URL is otherwise indistinguishable from prose (e.g. `example.com/file.py`).
- No change to `\>` in code spans/fences and no change to the round-99 spoiler literal.

## Guards

`tests/test_smoke.py` `r113a–c`: mobile/music/www/youtu.be/shorts/live all select a URL and agree with
the id reader; the escaped `>` is dropped on both cleaning routes while a real quote line and the
escaped spoiler opener stay intact; the scheme-less X status URL is linked while a bare `x.com/a`, a
too-short id, `abx.com/…` prose and a markdown link target stay byte-identical.
