# Round 114 — the unused YouTube mp4 playback path is removed for good (2026-11-11)

Scope: `testing area/reddit_main_v3.py` plus its three documentation surfaces (`README.md`,
`TERMS_OF_SERVICE.md`, `PRIVACY_POLICY.md`), `.env.example`, `.github/workflows/reddit_monitor.yml`
and the round-52 Variable guard in `tests/test_reddit_signals.py`. No card structure, component,
button, marker, cache, dedup, Devvit, X-engine or Game-Express change.

## Why

The owner's evidence (`example of a youtube post on reddit.txt`, cards for `1xquvvi` / `1xt22os`)
shows what the engine actually delivers for a YouTube post: the `i.ytimg.com` **thumbnail** as an
IMAGE tile, the animated YouTube **button**, and one **bare link message** so Discord renders its own
official player. There is **no** direct-link / mp4 embed on any live card, and the historical attempt
at one — the optional `seaof.glass/yt/<id>.mp4` probe behind `YOUTUBE_MEDIA_EMBED=1` — was never
enabled in production, because no candidate transcoder proved reliable. A dead switch that implies a
playback capability the engine does not have is stale information, so it is removed rather than left
documented.

## What was removed (no stale switch, variable, template, host or note)

| surface | removed |
|---|---|
| engine | `YOUTUBE_MEDIA_EMBED`, `YOUTUBE_MP4_TEMPLATE`, the mp4 range probe + retry + its log lines, and the `media.append({"kind": "video", …})` branch that a resolved mp4 used to feed |
| engine | the `is_live` parameter of `resolve_youtube_media` — it existed only to gate that mp4 probe; the function now returns the thumbnail string alone |
| engine | the two header note blocks that described the switch (they now state the real behaviour: never a video tile, no third-party transcoder) |
| `.env.example` | the commented `YOUTUBE_MEDIA_EMBED=0` block |
| `.github/workflows/reddit_monitor.yml` | `YOUTUBE_MEDIA_EMBED: ${{ vars.YOUTUBE_MEDIA_EMBED }}` |
| `tests/test_reddit_signals.py` | the name in the round-52 mapped-Variable list (101 checks, was 102) |
| `README.md` | the feature-row claim of "optional real playback" and the Variable-table row |
| `TERMS_OF_SERVICE.md` | `seaof.glass` in the third-party service list |
| `PRIVACY_POLICY.md` | the `seaof.glass` service row |

`docs/history/*` (CHANGELOG_ARCHIVE, ENGINE_HISTORY, REPOSITORY_TRACKING) is left untouched: those are
dated records of what the engine did at the time, not current documentation.

## Behaviour now (unchanged on every live card)

A YouTube post (watch / shorts / live / youtu.be / `m.` / `music.`) — link post or body link:

1. `i.ytimg.com` thumbnail (maxresdefault → hqdefault → mqdefault) as the card's IMAGE tile,
2. the `starwardspark3` YouTube button,
3. one follow-up message with the bare URL (`YOUTUBE_LINK_MESSAGE`, default on).

Never a video tile — which is also why round 112's spoiler rule needs no exception for YouTube: there
is no video item to exempt. If a YouTube mp4 path is ever wanted again, it must come with a
reliability decision and a new guard; the `r114a–d` guards fail if the switch, the template, a
transcoder host or the video-tile branch reappears without one.

## Guards

`tests/test_smoke.py` `r114a–d`: no switch/template/transcoder host in the engine; the resolver's
signature is `(session, vid)` and its body ends in `return thumb` with no media URL; a YouTube
thumbnail built on a card is an IMAGE-gallery item; the workflow and `.env.example` no longer mention
the switch.
